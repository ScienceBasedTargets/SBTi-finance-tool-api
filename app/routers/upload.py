import io
from typing import List

import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

import SBTi.utils
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

from app.config import AppConfig, get_config
from app.dependencies import resolve_providers, df_to_records
from app.schemas.upload import UploadScoreResponse

router = APIRouter()


@router.post("/csv", response_model=UploadScoreResponse, response_model_exclude_none=True,
             summary="Upload CSV and score")
async def upload_csv(
    file: UploadFile = File(...),
    fallback_score: float = Form(3.2),
    aggregation_method: str = Form("WATS"),
    data_providers: str = Form(""),
    config: AppConfig = Depends(get_config),
):
    """Upload a portfolio CSV and return temperature scores."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        portfolio = SBTi.utils.dataframe_to_portfolio(df)

        provider_names = [n.strip() for n in data_providers.split(",") if n.strip()]
        providers = resolve_providers(provider_names, config)
        agg_method = PortfolioAggregationMethod(aggregation_method)

        portfolio_data = SBTi.utils.get_data(providers, portfolio)
        scores_df, aggregations = SBTi.utils.calculate(
            portfolio_data=portfolio_data,
            fallback_score=fallback_score,
            time_frames=[],
            scopes=[],
            aggregation_method=agg_method,
            grouping=None,
            scenario=None,
            anonymize=False,
            aggregate=True,
        )

        return UploadScoreResponse(
            portfolio_count=len(portfolio),
            aggregated_scores=aggregations,
            scores=df_to_records(scores_df),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/excel", response_model=UploadScoreResponse, response_model_exclude_none=True,
             summary="Upload Excel and score")
async def upload_excel(
    file: UploadFile = File(...),
    skiprows: int = Form(0),
    fallback_score: float = Form(3.2),
    aggregation_method: str = Form("WATS"),
    data_providers: str = Form(""),
    config: AppConfig = Depends(get_config),
):
    """Upload a portfolio Excel file and return temperature scores."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), skiprows=skiprows)
        df = df.replace(r"^\s*$", np.nan, regex=True).dropna(how="all")
        portfolio = SBTi.utils.dataframe_to_portfolio(df)

        provider_names = [n.strip() for n in data_providers.split(",") if n.strip()]
        providers = resolve_providers(provider_names, config)
        agg_method = PortfolioAggregationMethod(aggregation_method)

        portfolio_data = SBTi.utils.get_data(providers, portfolio)
        scores_df, aggregations = SBTi.utils.calculate(
            portfolio_data=portfolio_data,
            fallback_score=fallback_score,
            time_frames=[],
            scopes=[],
            aggregation_method=agg_method,
            grouping=None,
            scenario=None,
            anonymize=False,
            aggregate=True,
        )

        return UploadScoreResponse(
            portfolio_count=len(portfolio),
            aggregated_scores=aggregations,
            scores=df_to_records(scores_df),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse", summary="Parse Excel to JSON")
async def parse_portfolio(file: UploadFile = File(...), skiprows: int = Form(0)) -> List[dict]:
    """Parse an Excel file and return rows as a list of dicts without scoring."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents), skiprows=skiprows)
    df = df.replace(r"^\s*$", np.nan, regex=True).dropna(how="all")
    return df_to_records(df)
