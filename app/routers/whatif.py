from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

import SBTi.utils
import SBTi.temperature_score
from SBTi.interfaces import PortfolioCompany
from SBTi.portfolio_coverage_tvp import PortfolioCoverageTVP

from app.config import AppConfig, get_config
from app.dependencies import resolve_providers, df_to_records
from app.schemas.whatif import WhatIfRequest, WhatIfResponse

router = APIRouter()


@router.post("/whatif", response_model=WhatIfResponse, response_model_exclude_none=True,
             summary="Run what-if scenario")
def calculate_whatif(
    request: WhatIfRequest,
    config: AppConfig = Depends(get_config),
):
    """Recalculate temperature scores under an engagement scenario."""
    try:
        portfolio = [PortfolioCompany(**c.model_dump()) for c in request.companies]
        providers = resolve_providers(request.data_providers, config)
        reporting_date = (
            datetime.fromisoformat(request.reporting_date)
            if request.reporting_date
            else None
        )

        portfolio_data = SBTi.utils.get_data(providers, portfolio, reporting_date=reporting_date)
        scenario = SBTi.temperature_score.Scenario.from_interface(request.scenario)

        scores_df, aggregations = SBTi.utils.calculate(
            portfolio_data=portfolio_data,
            fallback_score=request.fallback_score,
            time_frames=request.time_frames,
            scopes=request.scopes,
            aggregation_method=request.aggregation_method,
            grouping=request.grouping_columns,
            scenario=scenario,
            anonymize=request.anonymize,
            aggregate=True,
        )

        coverage = PortfolioCoverageTVP().get_portfolio_coverage(
            portfolio_data, request.aggregation_method
        )

        return WhatIfResponse(
            aggregated_scores=aggregations,
            scores=df_to_records(scores_df),
            coverage=coverage or 0.0,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
