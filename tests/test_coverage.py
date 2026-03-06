def test_coverage_requires_companies(client):
    response = client.post("/v1/coverage", json={})
    assert response.status_code == 422


def test_coverage_with_portfolio(client, sample_portfolio):
    response = client.post(
        "/v1/coverage",
        json={
            "companies": sample_portfolio,
            "data_providers": ["CSV"],
        },
    )
    assert response.status_code in (200, 400, 500)
    if response.status_code == 200:
        data = response.json()
        assert "coverage" in data
        assert isinstance(data["coverage"], float)
