def test_list_data_providers(client):
    response = client.get("/v1/data-providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "type" in data[0]
