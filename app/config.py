import json
import os
from functools import lru_cache


class AppConfig:
    def __init__(self):
        config_path = os.environ.get(
            "SBTI_CONFIG_PATH",
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json"),
        )
        with open(config_path) as f:
            raw = json.load(f)
        self.default_score: float = raw.get("default_score", 3.2)
        self.aggregation_method: str = raw.get("aggregation_method", "WATS")
        self.data_providers: list = raw.get("data_providers", [])


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
