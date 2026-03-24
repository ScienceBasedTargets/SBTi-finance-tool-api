from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import AppConfig, get_config

router = APIRouter()


class DataProviderInfo(BaseModel):
    name: str
    type: str


@router.get("/data-providers", response_model=List[DataProviderInfo], summary="List data providers")
def list_data_providers(config: AppConfig = Depends(get_config)):
    """Returns the data providers configured on this instance."""
    return [
        DataProviderInfo(name=dp["name"], type=dp["type"])
        for dp in config.data_providers
    ]
