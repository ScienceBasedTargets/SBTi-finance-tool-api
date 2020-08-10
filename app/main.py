import json
import os

from typing import List, Optional

import pandas as pd
import numpy as np
import uvicorn
from SBTi.data.bloomberg import Bloomberg
from SBTi.data.cdp import CDP
from SBTi.data.iss import ISS
from SBTi.data.trucost import Trucost
from SBTi.data.urgentum import Urgentum
from SBTi.interfaces.interfaces import PortfolioCompany, ScenarioInterface

from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel

app = FastAPI()

import mimetypes

mimetypes.init()

import SBTi
from SBTi.data.csv import CSVProvider
from SBTi.data.excel import ExcelProvider
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

UPLOAD_FOLDER = 'data'

DATA_PROVIDER_MAP = {
    "excel": ExcelProvider,
    "csv": CSVProvider,
    "bloomberg": Bloomberg,
    "cdp": CDP,
    "iss": ISS,
    "trucost": Trucost,
    "urgentum": Urgentum,
}


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


with open('config.json') as f_config:
    config = json.load(f_config)


def _get_data_providers(data_providers_input: List[str]):
    """
    Determines which data provider and in which order should be used.
    :param json_data:

    :rtype: List
    :return: a list of data providers in order.
    """
    # TODO: Move this to the data provider
    data_providers = []
    for data_provider in config["data_providers"]:
        data_provider["class"] = DATA_PROVIDER_MAP[data_provider["type"]](**data_provider["parameters"])
        data_providers.append(data_provider)

    selected_data_providers = []
    for data_provider_name in data_providers_input:
        for data_provider in data_providers:
            if data_provider["name"] == data_provider_name:
                selected_data_providers.append(data_provider["class"])
                break

    # TODO: When the user did give us data providers, but we can't match them this fails silently, maybe we should
    # fail louder
    if len(selected_data_providers) == 0:
        data_providers = [data_provider["class"] for data_provider in data_providers]
    return data_providers


@app.post("/temperature_score/")
def calculate_temperature_score(data: RequestTemperatureScore):
    try:
        scores, aggregations, coverage, column_distribution = SBTi.pipeline(
            data_providers=_get_data_providers(data.data_providers),
            portfolio=data.companies,
            fallback_score=data.default_score,
            filter_time_frame=data.filter_time_frame,
            filter_scope_category=data.filter_scope_category,
            aggregation_method=PortfolioAggregationMethod.from_string(data.aggregation_method),
            grouping=data.grouping_columns,
            scenario=SBTi.temperature_score.Scenario.from_interface(data.scenario),
            anonymize=data.anonymize_data_dump
        )
    except ValueError as e:
        return {"success": False, "message": str(e)}, 400

    # Include columns
    include_columns = ["company_name", "scope_category", "time_frame", "temperature_score"] + \
                      [column for column in data.include_columns if column in scores.columns]

    return {
        "aggregated_scores": aggregations,
        # TODO: The scores are included twice now, once with all columns, and once with only a subset of the columns
        "scores": scores.where(pd.notnull(scores), None).to_dict(orient="records"),
        "coverage": coverage,
        "companies": scores[include_columns].replace({np.nan: None}).to_dict(orient="records"),
        "feature_distribution": column_distribution
    }


@app.get("/data_providers/")
def get_data_providers():
    return [{"name": data_provider["name"], "type": data_provider["type"]}
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
