"""Compare the running Flask API to an in-process prediction on a real fixture."""
import json
from pathlib import Path

import requests

from backend.app import app, load_bundle

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "backend" / "test_payload.json"
API_URL = "http://127.0.0.1:5000"


def main():
    if not PAYLOAD_PATH.exists():
        raise SystemExit("Missing backend/test_payload.json. Run the research notebook first.")
    bundle = load_bundle()
    if bundle is None:
        raise SystemExit("Missing trusted model bundle. Run the research notebook first.")
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    missing = sorted(set(bundle["raw_input_columns"]) - set(payload))
    if missing:
        raise SystemExit(f"Sample payload is missing model inputs: {missing}")
    if bundle.get("target_name", "type") in payload or "label" in payload:
        raise SystemExit("Sample payload must not include target columns.")

    # The Flask test client provides a same-process reference result.
    expected = app.test_client().post("/predict", json=payload)
    if expected.status_code != 200:
        raise SystemExit(f"Local inference reference failed ({expected.status_code}): {expected.get_json()}")

    with requests.Session() as session:
        session.trust_env = False
        health = session.get(f"{API_URL}/health", timeout=5)
        health.raise_for_status()
        if not health.json().get("model_ready"):
            raise SystemExit("Flask is running but has not loaded the trained model. Restart it after training.")
        response = session.post(f"{API_URL}/predict", json=payload, timeout=30)
        response.raise_for_status()

    actual, reference = response.json(), expected.get_json()
    if actual["predicted_attack_type"] != reference["predicted_attack_type"]:
        raise SystemExit("HTTP result does not match direct local inference.")
    for label, probability in reference["class_probabilities"].items():
        if abs(actual["class_probabilities"][label] - probability) > 1e-9:
            raise SystemExit(f"HTTP probability mismatch for {label}.")
    print("PASS: running Flask prediction matches direct inference")
    print(f"Model: {actual['model_name']} | class: {actual['predicted_attack_type']} | confidence: {actual['confidence']:.6f}")


if __name__ == "__main__":
    main()
