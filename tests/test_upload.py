import io


def test_upload_csv_rejects_non_csv(client):
    file = io.BytesIO(b"test")
    response = client.post(
        "/v1/upload/csv",
        files={"file": ("test.txt", file, "text/plain")},
    )
    assert response.status_code == 400


def test_upload_excel_rejects_non_excel(client):
    file = io.BytesIO(b"test")
    response = client.post(
        "/v1/upload/excel",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert response.status_code == 400


def test_parse_rejects_non_excel(client):
    file = io.BytesIO(b"test")
    response = client.post(
        "/v1/upload/parse",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert response.status_code == 400
