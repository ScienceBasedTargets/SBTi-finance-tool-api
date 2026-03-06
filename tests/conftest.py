import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_portfolio():
    return [
        {
            "company_name": "Company A",
            "company_id": "1123",
            "investment_value": 1000000,
            "engagement_target": False,
        },
        {
            "company_name": "Company B",
            "company_id": "1124",
            "investment_value": 500000,
            "engagement_target": False,
        },
    ]
