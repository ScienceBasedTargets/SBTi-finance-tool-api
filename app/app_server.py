import json
import logging
import os

from typing import List, Dict

import pandas as pd
import numpy as np
from flask import Flask, request, send_from_directory
from flask_restful import Resource, Api
from flask_swagger_ui import get_swaggerui_blueprint

import mimetypes

mimetypes.init()

import SBTi
from SBTi.data.csv import CSVProvider
from SBTi.data.excel import ExcelProvider
from SBTi.portfolio_aggregation import PortfolioAggregationMethod
from SBTi.temperature_score import Scenario

UPLOAD_FOLDER = 'data'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api = Api(app)

DATA_PROVIDER_MAP = {
    "excel": ExcelProvider,
    "csv": CSVProvider,
}


def get_config():
    # TODO: Make this path relative to the current directory, instead of the working directory
    with open('config.json') as f_config:
        return json.load(f_config)


class BaseEndpoint(Resource):
    """
    This class instantiates the data provider classes and loads in the config file. Further classes with inherit the
     methods from this class.

    :rtype:
    :return:
    """

    def __init__(self):
        self.config = get_config()

        # Set the logging level based on the config
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config["verbosity"])

        self.data_providers = []
        for data_provider in self.config["data_providers"]:
            data_provider["class"] = DATA_PROVIDER_MAP[data_provider["type"]](**data_provider["parameters"])
            self.data_providers.append(data_provider)

    def _get_data_providers(self, json_data: Dict):
        """
        Determines which data provider and in which order should be used.
        :param json_data:

        :rtype: List
        :return: a list of data providers in order.
        """
        # TODO: Move this to the data provider
        # TODO: Why is there a hard-coded Excel connector here?
        data_providers = []
        if "data_providers" in json_data:
            for path in json_data["data_providers"]:
                data_provider = DATA_PROVIDER_MAP['excel'](path)
                data_providers.append(data_provider)

        # TODO: When the user did give us data providers, but we can't match them this fails silently, maybe we should
        # fail louder
        if len(data_providers) == 0:
            data_providers = [data_provider["class"] for data_provider in self.data_providers]
        return data_providers


class TemperatureScoreEndpoint(BaseEndpoint):
    """
    Generates the temperature aggregation scoring for the companies provided.

    :rtype: Dictionary
    :return: aggregation scoring per companies.
    """

    def __init__(self):
        super().__init__()

    def post(self):
        json_data = request.get_json(force=True)

        try:
            scores, aggregations, coverage, column_distribution = SBTi.pipeline(
                data_providers=self._get_data_providers(json_data),
                portfolio=pd.DataFrame(json_data["companies"]),
                fallback_score=json_data.get("default_score", self.config["default_score"]),
                aggregation_method=PortfolioAggregationMethod.from_string(json_data["aggregation_method"]),
                grouping=json_data.get("grouping_columns", None),
                scenario=Scenario.from_dict(json_data.get('scenario', None)),
                anonymize=json_data.get("anonymize_data_dump", False)
            )
        except ValueError as e:
            return {"success": False, "message": str(e)}, 400

        # Filter scope (s1s2, s3 or s1s2s3)
        if len(json_data.get("filter_scope_category", [])) > 0:
            scores = scores[scores["scope_category"].isin(json_data["filter_scope_category"])]

        # Filter time frame (short, mid, long)
        if len(json_data.get("filter_time_frame", [])) > 0:
            scores = scores[scores["time_frame"].isin(json_data["filter_time_frame"])]

        # Include columns
        include_columns = ["company_name", "scope_category", "time_frame", "temperature_score"] + \
                          [column for column in json_data.get("include_columns", []) if column in scores.columns]

        return {
            "aggregated_scores": aggregations,
            # TODO: The scores are included twice now, once with all columns, and once with only a subset of the columns
            "scores": scores.where(pd.notnull(scores), None).to_dict(orient="records"),
            "coverage": coverage,
            "companies": scores[include_columns].replace({np.nan: None}).to_dict(orient="records"),
            "feature_distribution": column_distribution
        }


class DataProvidersEndpoint(BaseEndpoint):
    """
    This class provides the user with a list of the available data providers.
    """

    def __init__(self):
        super().__init__()

    def get(self):
        """
        Get a list of available data providers on this server.

        :rtype: List
        :return: a list of data providers.
        """
        return [{"name": data_provider["name"], "type": data_provider["type"]}
                for data_provider in self.config["data_providers"]]


class DocumentationEndpoint(Resource):
    """
    Supports flask_swagger documentation endpoint
    """

    def get(self, path):
        return send_from_directory('static', path)


class ParsePortfolioEndpoint(Resource):
    """
    This class allows the client to user to parse his Excel portfolio and transform it into a JSON object.
    Note: This endpoint is only meant to be used by the UI!
    """

    def post(self):
        skiprows = request.form.get("skiprows", 0)
        df = pd.read_excel(request.files.get('file'), skiprows=int(skiprows))

        return {'portfolio': df.replace(r'^\s*$', np.nan, regex=True).dropna(how='all').replace({np.nan: None}).to_dict(
            orient="records")}


class ImportDataProviderEndpoint(Resource):
    """
    Allows the user to replace the "inputFormat" with a new "data provider".
    """

    def post(self):
        file = request.files['file']
        file_name = file.filename
        file_type = file_name.split('.')[-1]
        if (int(file.tell()) < 10000000) & (file_type == 'xlsx'):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'InputFormat.xlsx'))
            return {'POST Request': {'Response': {'Status Code': 200, 'Message': 'Data Provider Imported'}}}
        else:
            return {'POST Request': {'Response': {'Status Code': 400, 'Message': 'Error. File did not save.'}}}


SWAGGER_URL = '/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'SBTi-API'
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

api.add_resource(TemperatureScoreEndpoint, '/temperature_score/')
api.add_resource(DataProvidersEndpoint, '/data_providers/')
api.add_resource(DocumentationEndpoint, '/static/<path:path>')
api.add_resource(ParsePortfolioEndpoint, '/parse_portfolio/')
api.add_resource(ImportDataProviderEndpoint, '/import_data_provider/')

if __name__ == '__main__':
    app.run(debug=True)  # important to mention debug=True
