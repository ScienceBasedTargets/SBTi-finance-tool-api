from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

import SBTi.utils
from SBTi.interfaces import PortfolioCompany
from SBTi.portfolio_coverage_tvp import PortfolioCoverageTVP

from app.config import AppConfig, get_config
from app.dependencies import resolve_providers
from app.schemas.coverage import CoverageRequest, CoverageResponse

router = APIRouter()


@router.post("/coverage", response_model=CoverageResponse, summary="Calculate portfolio coverage")
def calculate_coverage(
    request: CoverageRequest,
    config: AppConfig = Depends(get_config),
):
    """Returns the percentage of the portfolio covered by companies with approved SBTi targets."""
    try:
        portfolio = [PortfolioCompany(**c.model_dump()) for c in request.companies]
        providers = resolve_providers(request.data_providers, config)
        reporting_date = (
            datetime.fromisoformat(request.reporting_date)
            if request.reporting_date
            else None
        )

        portfolio_data = SBTi.utils.get_data(providers, portfolio, reporting_date=reporting_date)
        coverage = PortfolioCoverageTVP().get_portfolio_coverage(
            portfolio_data, request.aggregation_method
        )

        return CoverageResponse(coverage=coverage or 0.0)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
