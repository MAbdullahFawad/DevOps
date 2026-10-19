"""Local inference API for the TON-IoT research benchmark.

The trained bundle is deliberately not included in source control. Generate it
by running the research notebook, then place ton_iot_best_model.pkl in
backend/models/. The static GitHub Pages build never runs Python inference.
"""
from pathlib import Path
import logging

from flask import Flask, jsonify, request

BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / "models" / "ton_iot_best_model.pkl"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
app.logger.setLevel(logging.INFO)


def load_bundle():
    if not MODEL_PATH.exists():
        return None
    # Only load artifacts you created and trust. Pickle/joblib can execute code.
    import joblib
    return joblib.load(MODEL_PATH)


try:
    BUNDLE = load_bundle()
except Exception:
    app.logger.exception("Could not load the local model bundle")
    BUNDLE = None


@app.get("/health")
def health():
    ready = BUNDLE is not None
    return jsonify(status="ok", model_ready=ready,
                   model_name=BUNDLE.get("model_name") if ready else None,
                   features=len(BUNDLE.get("feature_columns", [])) if ready else None)


@app.get("/schema")
def schema():
    if BUNDLE is None:
        return jsonify(error="Model bundle is not installed",
                       setup="Run TON_IoT_Research_Benchmark.ipynb and place its trusted output at backend/models/ton_iot_best_model.pkl"), 503
    return jsonify(features=BUNDLE["feature_columns"],
                   numeric_features=BUNDLE.get("numeric_columns", []),
                   categorical_features=BUNDLE.get("categorical_columns", []),
                   required_inputs=BUNDLE.get("raw_input_columns", []),
                   numeric_inputs=BUNDLE.get("raw_numeric_columns", []),
                   categorical_inputs=BUNDLE.get("raw_categorical_columns", []),
                   model_name=BUNDLE.get("model_name"),
                   classes=BUNDLE.get("class_names", []))


def engineer(frame):
    import numpy as np
    import pandas as pd
    frame = frame.copy()
    columns = set(frame.columns)
    for left, right, name in (("src_bytes", "dst_bytes", "byte"),
                              ("src_pkts", "dst_pkts", "packet")):
        if left in frame and right in frame:
            a = pd.to_numeric(frame[left], errors="coerce")
            b = pd.to_numeric(frame[right], errors="coerce").replace(0, np.nan)
            frame[f"{name}_ratio"] = a / b
            frame[f"{name}_imbalance"] = a - pd.to_numeric(frame[right], errors="coerce")
    duration = next((c for c in ("duration", "flow_duration", "dur") if c in columns), None)
    byte_count = next((c for c in ("bytes", "total_bytes", "sbytes") if c in columns), None)
    packet_count = next((c for c in ("packets", "total_packets", "spkts") if c in columns), None)
    if byte_count is None and {"src_bytes", "dst_bytes"}.issubset(columns):
        byte_count = "__total_bytes"
        frame[byte_count] = pd.to_numeric(frame.src_bytes, errors="coerce") + pd.to_numeric(frame.dst_bytes, errors="coerce")
    if packet_count is None and {"src_pkts", "dst_pkts"}.issubset(columns):
        packet_count = "__total_packets"
        frame[packet_count] = pd.to_numeric(frame.src_pkts, errors="coerce") + pd.to_numeric(frame.dst_pkts, errors="coerce")
    if duration and byte_count:
        frame["bytes_per_second"] = pd.to_numeric(frame[byte_count], errors="coerce") / pd.to_numeric(frame[duration], errors="coerce").replace(0, np.nan)
    if duration and packet_count:
        frame["packets_per_second"] = pd.to_numeric(frame[packet_count], errors="coerce") / pd.to_numeric(frame[duration], errors="coerce").replace(0, np.nan)
    if byte_count and packet_count:
        frame["bytes_per_packet"] = pd.to_numeric(frame[byte_count], errors="coerce") / pd.to_numeric(frame[packet_count], errors="coerce").replace(0, np.nan)
    return frame.replace([np.inf, -np.inf], np.nan)


@app.post("/predict")
def predict():
    record = request.get_json(silent=True)
    if not isinstance(record, dict):
        return jsonify(error="Expected one JSON object representing a network flow"), 400
    if BUNDLE is None:
        return jsonify(error="Local model is not available",
                       detail="Generate the trusted artifact from the research notebook and save it under backend/models/ton_iot_best_model.pkl."), 503
    import numpy as np
    import pandas as pd
    target = BUNDLE.get("target_name", "type")
    forbidden = {target, "label"}.intersection(record)
    if forbidden:
        return jsonify(error="Target fields must not be supplied as predictors", fields=sorted(forbidden)), 400
    try:
        frame = engineer(pd.DataFrame([record]))
        missing = [column for column in BUNDLE.get("raw_input_columns", []) if column not in frame]
        if missing:
            return jsonify(error="Incomplete flow record", detail="Supply every model input field.", missing_fields=missing), 400
        for column in BUNDLE["feature_columns"]:
            if column not in frame:
                frame[column] = np.nan
        frame = frame[BUNDLE["feature_columns"]]
        if BUNDLE.get("model_name") == "CatBoost":
            for column in BUNDLE.get("catboost_numeric", []):
                frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(BUNDLE["catboost_medians"].get(column, 0))
            for column in BUNDLE.get("catboost_categorical", []):
                frame[column] = frame[column].fillna(BUNDLE["catboost_modes"].get(column, "__MISSING__")).astype(str)
        model = BUNDLE["model"]
        probabilities = model.predict_proba(frame)[0]
        index = int(np.argmax(probabilities))
        classes = BUNDLE["class_names"]
        return jsonify(predicted_attack_type=str(classes[index]),
                       confidence=float(probabilities[index]),
                       class_probabilities={str(c): float(p) for c, p in zip(classes, probabilities)},
                       model_name=BUNDLE.get("model_name"),
                       disclaimer="Research benchmark output; not a production security decision. Validate on your own environment.")
    except (ValueError, TypeError) as exc:
        return jsonify(error="Invalid flow record", detail=str(exc)), 400
    except Exception:
        app.logger.exception("Inference failed")
        return jsonify(error="Prediction processing failed"), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
