import json
import os

from typing import List, Optional

import pandas as pd
import numpy as np
import uvicorn
from SBTi.interfaces import PortfolioCompany, ScenarioInterface

from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="SBTi Finance Temperature Alignment tool",
    description="This tool helps companies and financial institutions to assess the temperature alignment of current "
                "targets, commitments, and investment and lending portfolios, and to use this information to develop "
                "targets for official validation by the SBTi.",
    version="0.1.0",
)

import mimetypes

mimetypes.init()

import SBTi
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

UPLOAD_FOLDER = 'data'


with open('config.json') as f_config:
    config = json.load(f_config)


class RequestTemperatureScore(BaseModel):
    data_providers: Optional[List[str]] = []
    companies: List[PortfolioCompany]
    default_score: float
    aggregation_method: Optional[str] = "WATS"
    grouping_columns: Optional[List[str]] = None
    include_columns: Optional[List[str]] = []
    scenario: Optional[ScenarioInterface] = None
    anonymize_data_dump: Optional[bool] = False
    filter_scope_category: Optional[List[str]] = []
    filter_time_frame: Optional[List[str]] = []


class ResponseTemperatureScore(BaseModel):
    aggregated_scores: dict
    scores: List[dict]
    coverage: float
    companies: List[dict]
    feature_distribution: Optional[dict]


@app.post("/temperature_score/", response_model=ResponseTemperatureScore)
def calculate_temperature_score(
        companies: List[PortfolioCompany] = Body(..., description="A portfolio containing the companies"),
        default_score: float = Body(
            default=config["default_score"],
            gte=0,
            description="The default score to fall back on when there's no target available."),
        data_providers: Optional[List[str]] = Body(
            default=[],
            description="A list of data provider names to use. These names should be available in the list that can be "
                        "retrieved through the /data_providers/ endpoint."),
        aggregation_method: Optional[str] = Body(
            default=config["aggregation_method"],
            description="The aggregation method to use. This can be one of the following 'WATS', 'TETS', 'MOTS', "
                        "'EOTS', 'ECOTS', 'AOTS'"),
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
        filter_scope_category: Optional[List[str]] = Body(
            default=[],
            description="The scopes that should be included in the results."),
        filter_time_frame: Optional[List[str]] = Body(
            default=[],
            description="The time frames that should be included in the results.")
) -> ResponseTemperatureScore:
    """
    Calculate the temperature score for a given set of parameters.
    """
    try:
        scores, aggregations, coverage, column_distribution = SBTi.pipeline(
            data_providers=SBTi.data.get_data_providers(config["data_providers"], data_providers),
            portfolio=companies,
            fallback_score=default_score,
            filter_time_frame=filter_time_frame,
            filter_scope_category=filter_scope_category,
            aggregation_method=PortfolioAggregationMethod.from_string(aggregation_method),
            grouping=grouping_columns,
            scenario=SBTi.temperature_score.Scenario.from_interface(scenario),
            anonymize=anonymize_data_dump
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Include columns
    include_columns = ["company_name", "scope_category", "time_frame", "temperature_score"] + \
                      [column for column in include_columns if column in scores.columns]

    return ResponseTemperatureScore(
        aggregated_scores=aggregations,
        scores=scores.where(pd.notnull(scores), None).to_dict(orient="records"),
        coverage=coverage,
        companies=scores[include_columns].replace({np.nan: None}).to_dict(orient="records"),
        feature_distribution=column_distribution,
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


@app.post("/parse_portfolio/")
def parse_portfolio(file: bytes = File(...), skiprows: int = Form(...)):
    df = pd.read_excel(file, skiprows=int(skiprows))

    return {'portfolio': df.replace(r'^\s*$', np.nan, regex=True).dropna(how='all').replace({np.nan: None}).to_dict(
            orient="records")}


@app.post("/import_data_provider/")
def import_data_provider(file: UploadFile = File(...)):
    file_name = file.filename
    file_type = file_name.split('.')[-1]
    if file_type == 'xlsx':
        x = 10000000 / 10000
        xi = 0
        with open(os.path.join(UPLOAD_FOLDER, 'InputFormat_tmp.xlsx'), 'ab') as f:
            for chunk in iter(lambda: file.file.read(10000), b''):
                f.write(chunk)
                xi += 1
                if xi > x:
                    f.close()
                    os.remove(os.path.join(UPLOAD_FOLDER, 'InputFormat_tmp.xlsx'))
                    return {'POST Request': {'Response': {'Status Code': 400, 'Message': 'Error. File did not save.'}}}
        os.rename(os.path.join(UPLOAD_FOLDER, 'InputFormat_tmp.xlsx'),
                  os.path.join(UPLOAD_FOLDER, 'InputFormat.xlsx'))
        return {'POST Request': {'Response': {'Status Code': 200, 'Message': 'Data Provider Imported'}}}
    else:
        return {'POST Request': {'Response': {'Status Code': 400, 'Message': 'Error. File did not save.'}}}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info", reload=True)
