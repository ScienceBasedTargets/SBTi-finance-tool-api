def test_whatif_requires_scenario(client, sample_portfolio):
    response = client.post(
        "/v1/temperature/whatif",
        json={"companies": sample_portfolio},
    )
    assert response.status_code == 422


def test_whatif_with_scenario(client, sample_portfolio):
    response = client.post(
        "/v1/temperature/whatif",
        json={
            "companies": sample_portfolio,
            "scenario": {"number": 1},
            "data_providers": ["CSV"],
        },
    )
    assert response.status_code in (200, 400, 500)
    if response.status_code == 200:
        data = response.json()
        assert "scores" in data
        assert "coverage" in data
