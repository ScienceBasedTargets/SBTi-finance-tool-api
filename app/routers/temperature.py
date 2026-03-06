from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

import SBTi.utils
import SBTi.temperature_score
from SBTi.interfaces import PortfolioCompany

from app.config import AppConfig, get_config
from app.dependencies import resolve_providers, df_to_records
from app.schemas.temperature import TemperatureScoreRequest, TemperatureScoreResponse

router = APIRouter()


@router.post("/score", response_model=TemperatureScoreResponse, response_model_exclude_none=True,
             summary="Calculate temperature scores")
def calculate_temperature_score(
    request: TemperatureScoreRequest,
    config: AppConfig = Depends(get_config),
):
    """Calculate temperature alignment scores for a portfolio of companies."""
    try:
        portfolio = [PortfolioCompany(**c.model_dump()) for c in request.companies]
        providers = resolve_providers(request.data_providers, config)
        reporting_date = (
            datetime.fromisoformat(request.reporting_date)
            if request.reporting_date
            else None
        )

        portfolio_data = SBTi.utils.get_data(providers, portfolio, reporting_date=reporting_date)
        scores_df, aggregations = SBTi.utils.calculate(
            portfolio_data=portfolio_data,
            fallback_score=request.fallback_score,
            time_frames=request.time_frames,
            scopes=request.scopes,
            aggregation_method=request.aggregation_method,
            grouping=request.grouping_columns,
            scenario=None,
            anonymize=request.anonymize,
            aggregate=request.aggregate,
        )

        company_cols = ["company_name", "scope", "time_frame", "temperature_score"]
        available_cols = [c for c in company_cols if c in scores_df.columns]

        return TemperatureScoreResponse(
            aggregated_scores=aggregations,
            scores=df_to_records(scores_df),
            companies=df_to_records(scores_df[available_cols]),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
