from typing import List, Optional

from pydantic import BaseModel, Field
from SBTi.interfaces import EScope, ETimeFrames, ScenarioInterface, ScoreAggregations
from SBTi.portfolio_aggregation import PortfolioAggregationMethod

from app.schemas.common import PortfolioCompanyInput


class WhatIfRequest(BaseModel):
    """Scenarios 1-4 model engagement effects on portfolio temperature scores.

    Set engagement_type to "SET_TARGETS" (2.0C) or "SET_SBTI_TARGETS" (1.75C).
    """

    companies: List[PortfolioCompanyInput]
    scenario: ScenarioInterface = Field(description="e.g. {\"number\": 1, \"engagement_type\": \"SET_TARGETS\"}")
    data_providers: List[str] = Field(default=[], description="Provider names. Defaults to first configured.")
    fallback_score: float = Field(default=3.2, ge=0, description="Score for companies without valid targets.")
    aggregation_method: PortfolioAggregationMethod = PortfolioAggregationMethod.WATS
    scopes: List[EScope] = Field(default=[], description="Empty = all scopes.")
    time_frames: List[ETimeFrames] = Field(default=[], description="Empty = all time frames.")
    grouping_columns: Optional[List[str]] = None
    anonymize: bool = False
    reporting_date: Optional[str] = Field(default=None, description="ISO 8601 date. Defaults to today.")


class WhatIfResponse(BaseModel):
    aggregated_scores: Optional[ScoreAggregations] = None
    scores: List[dict]
    coverage: float
