from typing import Optional

from pydantic import BaseModel, Field


class PortfolioCompanyInput(BaseModel):
    company_name: str
    company_id: str = Field(description="Unique identifier (e.g. ISIN, LEI, or internal ID).")
    company_isin: Optional[str] = None
    company_lei: Optional[str] = None
    investment_value: float = Field(description="Investment value, used for weighting.")
    engagement_target: Optional[bool] = Field(default=False, description="Used in scenario 4 what-if analysis.")
    user_fields: Optional[dict] = Field(default=None, description="Custom fields for grouping or display.")


class ErrorDetail(BaseModel):
    detail: str
    type: Optional[str] = None
