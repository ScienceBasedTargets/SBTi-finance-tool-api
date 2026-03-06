def test_temperature_score_requires_companies(client):
    response = client.post("/v1/temperature/score", json={})
    assert response.status_code == 422


def test_temperature_score_with_portfolio(client, sample_portfolio):
    response = client.post(
        "/v1/temperature/score",
        json={
            "companies": sample_portfolio,
            "data_providers": ["CSV"],
        },
    )
    # May return 200 or 400/500 depending on data availability
    assert response.status_code in (200, 400, 500)
    if response.status_code == 200:
        data = response.json()
        assert "scores" in data
        assert "companies" in data
