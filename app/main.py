import json
import os

from typing import List, Optional

import pandas as pd
import numpy as np
import uvicorn
from SBTi.interfaces import PortfolioCompany, ScenarioInterface, EScope, ETimeFrames, ScoreAggregations
from SBTi.portfolio_coverage_tvp import PortfolioCoverageTVP

from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException
from pydantic import BaseModel
import mimetypes
import SBTi
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

app = FastAPI(
    title="SBTi Finance Temperature Alignment tool API",
    description="This tool helps companies and financial institutions to assess the temperature alignment of current "
                "targets, commitments, and investment and lending portfolios, and to use this information to develop "
                "targets for official validation by the SBTi.",
    version="0.1.0",
)

mimetypes.init()
UPLOAD_FOLDER = 'data'

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')) as f_config:
    config = json.load(f_config)


class ResponseTemperatureScore(BaseModel):
    aggregated_scores: Optional[ScoreAggregations]
    scores: List[dict]
    coverage: float
    companies: List[dict]


@app.post("/temperature_score/", response_model=ResponseTemperatureScore, response_model_exclude_none=True)
def calculate_temperature_score(
        companies: List[PortfolioCompany] = Body(
            ...,
            description="A portfolio containing the companies. If you want to use other fields later on or for grouping "
                        "you can include these in the 'user_fields' object."),
        default_score: float = Body(
            default=config["default_score"],
            gte=0,
            description="The default score to fall back on when there's no target available."),
        data_providers: Optional[List[str]] = Body(
            default=[],
            description="A list of data provider names to use. These names should be available in the list that can be "
                        "retrieved through the /data_providers/ endpoint."),
        aggregation_method: Optional[PortfolioAggregationMethod] = Body(
            default=config["aggregation_method"],
            description="The aggregation method to use."),
        grouping_columns: Optional[List[str]] = Body(
            default=None,
            description="A list of column names that should be grouped on."),
        include_columns: Optional[List[str]] = Body(
            default=[],
            description="A list of column names that should be included in the output."),
        scenario: Optional[ScenarioInterface] = Body(
            default=None,
            description="The scenario that should be used. This will change (some of the) targets, to simulate a "
                        "what-if scenario."),
        anonymize_data_dump: Optional[bool] = Body(
            default=False,
            description="Whether or not the resulting data set should be anonymized or not."),
        aggregate: Optional[bool] = Body(
            default=True,
            description="Whether to calculate aggregations or not."),
        scopes: Optional[List[EScope]] = Body(
            default=[],
            description="The scopes that should be included in the results."),
        time_frames: Optional[List[ETimeFrames]] = Body(
            default=[],
            description="The time frames that should be included in the results.")
) -> ResponseTemperatureScore:
    """
    Calculate the temperature score for a given set of parameters.
    """
    try:
        data_providers = SBTi.data.get_data_providers(config["data_providers"], data_providers)
        portfolio_data = SBTi.utils.get_data(data_providers, companies)
        scores, aggregations = SBTi.utils.calculate(
            portfolio_data=portfolio_data,
            fallback_score=default_score,
            time_frames=time_frames,
            scopes=scopes,
            aggregation_method=aggregation_method,
            grouping=grouping_columns,
            scenario=SBTi.temperature_score.Scenario.from_interface(scenario),
            anonymize=anonymize_data_dump,
            aggregate=aggregate
        )

        coverage = PortfolioCoverageTVP().get_portfolio_coverage(portfolio_data, aggregation_method)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=repr(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

    # Include columns
    include_columns = ["company_name", "scope", "time_frame", "temperature_score"] + \
                      [column for column in include_columns if column in scores.columns]

    return ResponseTemperatureScore(
        aggregated_scores=aggregations,
        scores=scores.where(pd.notnull(scores), None).to_dict(orient="records"),
        coverage=coverage,
        companies=scores[include_columns].replace({np.nan: None}).to_dict(orient="records")
    )


class ResponseDataProvider(BaseModel):
    name: str
    type: str


@app.get("/data_providers/", response_model=List[ResponseDataProvider])
def get_data_providers() -> List[ResponseDataProvider]:
    """
    Get a list of the available data providers.
    """
    return [ResponseDataProvider(name=data_provider["name"], type=data_provider["type"])
            for data_provider in config["data_providers"]]


@app.post("/parse_portfolio/", response_model=List[dict])
def parse_portfolio(file: bytes = File(...), skiprows: int = Form(...)):
    """
    Parse a portfolio Excel file and return it as a list of dictionaries.

    *Note: This endpoint is only for use in the frontend*
    """
    df = pd.read_excel(file, skiprows=int(skiprows))

    return df.replace(r'^\s*$', np.nan, regex=True).dropna(how='all').replace({np.nan: None}).to_dict(orient="records")


@app.post("/import_data_provider/")
def import_data_provider(file: UploadFile = File(...)):
    """
    Import a new Excel data provider file. This will overwrite the current "dummy" data provider input file.

    *Note: This endpoint is only for use in the frontend during the beta testing phase.*
    """
    # TODO: Remove this endpoint after the beta testing phase
    file_name = file.filename
    file_type = file_name.split('.')[-1]
    if file_type == 'xlsx':
        x = 10000000 / 10000
        xi = 0
        with open(os.path.join(UPLOAD_FOLDER, 'input_format_tmp.xlsx'), 'ab') as f:
            for chunk in iter(lambda: file.file.read(10000), b''):
                f.write(chunk)
                xi += 1
                if xi > x:
                    f.close()
                    os.remove(os.path.join(UPLOAD_FOLDER, 'input_format_tmp.xlsx'))
                    return {'POST Request': {'Response': {'Status Code': 400, 'Message': 'Error. File did not save.'}}}
        os.replace(os.path.join(UPLOAD_FOLDER, 'input_format_tmp.xlsx'),
                   os.path.join(UPLOAD_FOLDER, 'input_format.xlsx'))
        return {'detail': 'Data Provider Imported'}
    else:
        raise HTTPException(status_code=500, detail='Error. File did not save.')


if __name__ == "__main__":
    uvicorn.run("main:app", host=config["server"]["host"], port=config["server"]["port"],
                log_level=config["server"]["log_level"], reload=config["server"]["reload"])
