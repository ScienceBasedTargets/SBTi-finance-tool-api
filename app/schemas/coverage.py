from typing import List, Optional

from pydantic import BaseModel, Field
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

from app.schemas.common import PortfolioCompanyInput


class CoverageRequest(BaseModel):
    companies: List[PortfolioCompanyInput]
    data_providers: List[str] = Field(default=[], description="Provider names. Defaults to first configured.")
    aggregation_method: PortfolioAggregationMethod = PortfolioAggregationMethod.WATS
    reporting_date: Optional[str] = Field(default=None, description="ISO 8601 date. Defaults to today.")


class CoverageResponse(BaseModel):
    coverage: float = Field(description="Percentage of portfolio covered by approved SBTi targets.")
