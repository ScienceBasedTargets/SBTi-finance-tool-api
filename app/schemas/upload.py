from typing import List, Optional

from pydantic import BaseModel, Field
from SBTi.interfaces import ScoreAggregations


class UploadScoreResponse(BaseModel):
    portfolio_count: int = Field(description="Number of companies parsed from the file.")
    aggregated_scores: Optional[ScoreAggregations] = None
    scores: List[dict]
