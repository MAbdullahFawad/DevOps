import pytest
import backend.app as api
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


def test_ton_iot_feature_engineering_matches_dataset_field_names():
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    row = api.engineer(pd.DataFrame([{
        "duration": 2, "src_bytes": 8, "dst_bytes": 2,
        "src_pkts": 4, "dst_pkts": 2,
    }])).iloc[0]
    assert row["byte_ratio"] == 4
    assert row["packet_ratio"] == 2
    assert row["bytes_per_second"] == 5
    assert row["packets_per_second"] == 3


def test_prediction_rejects_missing_trained_model_inputs(monkeypatch):
    np = pytest.importorskip("numpy")
    class Model:
        def predict_proba(self, frame):
            return np.array([[0.8, 0.2]])

    monkeypatch.setattr(api, "BUNDLE", {
        "model": Model(), "model_name": "test", "feature_columns": ["duration"],
        "raw_input_columns": ["duration", "src_bytes"], "class_names": ["normal", "dos"],
    })
    response = app.test_client().post("/predict", json={"duration": 1})
    assert response.status_code == 400
    assert response.json["missing_fields"] == ["src_bytes"]
