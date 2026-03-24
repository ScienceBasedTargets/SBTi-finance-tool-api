import pandas as pd
from typing import List

import SBTi.utils
from SBTi.data import DataProvider
from app.config import AppConfig


def resolve_providers(provider_names: List[str], config: AppConfig) -> List[DataProvider]:
    """Resolve provider name strings to DataProvider instances."""
    if not provider_names:
        provider_names = [config.data_providers[0]["name"]]
    return SBTi.utils.get_data_providers(config.data_providers, provider_names)


def df_to_records(df: pd.DataFrame) -> List[dict]:
    """Convert a DataFrame to a list of dicts, replacing NaN with None for JSON serialization."""
    return df.where(pd.notnull(df), None).to_dict(orient="records")
