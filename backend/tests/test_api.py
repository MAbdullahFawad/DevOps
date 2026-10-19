from backend.app import app


def test_health_reports_missing_artifact_honestly():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["model_ready"] is False


def test_schema_explains_artifact_setup():
    response = app.test_client().get("/schema")
    assert response.status_code == 503
    assert "not installed" in response.json["error"]


def test_prediction_requires_json_object():
    response = app.test_client().post("/predict", json=[1, 2])
    assert response.status_code == 400


def test_prediction_reports_missing_model():
    response = app.test_client().post("/predict", json={"duration": 1})
    assert response.status_code == 503
