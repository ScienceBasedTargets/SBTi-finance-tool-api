from typing import List, Optional

from pydantic import BaseModel, Field
from SBTi.interfaces import EScope, ETimeFrames, ScoreAggregations
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

from app.schemas.common import PortfolioCompanyInput


class TemperatureScoreRequest(BaseModel):
    companies: List[PortfolioCompanyInput]
    data_providers: List[str] = Field(default=[], description="Provider names from /v1/data-providers. Defaults to first configured.")
    fallback_score: float = Field(default=3.2, ge=0, description="Score for companies without valid targets.")
    aggregation_method: PortfolioAggregationMethod = PortfolioAggregationMethod.WATS
    scopes: List[EScope] = Field(default=[], description="Empty = all scopes.")
    time_frames: List[ETimeFrames] = Field(default=[], description="Empty = all time frames.")
    grouping_columns: Optional[List[str]] = Field(default=None, description="Columns to group results by.")
    anonymize: bool = False
    aggregate: bool = True
    reporting_date: Optional[str] = Field(default=None, description="ISO 8601 date. Defaults to today.")


class TemperatureScoreResponse(BaseModel):
    aggregated_scores: Optional[ScoreAggregations] = None
    scores: List[dict] = Field(description="Full per-company scoring data.")
    companies: List[dict] = Field(description="Simplified view: name, scope, time frame, score.")
