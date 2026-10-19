# Signal — TON-IoT Research Console

A full-stack research interface for the repository’s TON-IoT network intrusion benchmark. The project compares Random Forest, LightGBM, XGBoost, Logistic Regression and CatBoost for binary detection and ten-class attack attribution. Signal adds a local Flask inference API, a responsive Angular interface, automated CI, and a static GitHub Pages build.


**Student:** Muhammad Abdullah · **Registration ID:** 232052
**Repository:** [MAbdullahFawad/DevOps](https://github.com/MAbdullahFawad/DevOps)

## Research and model provenance

The source of truth is `TON_IoT_Research_Benchmark.ipynb`, which loads `codymlewis/TON_IoT_network` and constructs its fitted preprocessing/model pipeline. Its final artifact is saved as both `ton_iot_best_model.pkl` and `backend/models/ton_iot_best_model.pkl`. The notebook must be executed before local predictions are available. The cloned repository does not contain a trained model or sample record, and no fabricated result is shown when the artifact is missing.

The notebook removes explicit source/destination IP identity fields and the label columns from predictors, engineers flow ratios and rates, uses a stratified 80/20 split, and reports multiclass, binary, per-class, calibration, robustness, and efficiency analyses. See the notebook for the exact model and evaluation protocol. Benchmark output is a research signal, not a production security decision; results need independent device, site, and time validation.

## Requirements

- Python 3.12 recommended (the notebook also needs Jupyter and its research dependencies)
- Node.js 24 LTS for the frontend
- Git

## Run the research notebook

Create and activate a virtual environment, then install the notebook dependencies:

```powershell
python -m venv .venv-research
.\.venv-research\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install jupyter nbformat nbclient ipykernel pandas numpy scikit-learn matplotlib seaborn shap joblib datasets lightgbm xgboost catboost
python -m ipykernel install --user --name ton_iot_research --display-name "Python (TON-IoT Research)"
python run_notebook.py
```

Notebook execution downloads the dataset and runs multiple model comparisons. It may take substantial time and compute. On completion, the notebook saves the local API bundle to `backend/models/ton_iot_best_model.pkl`. Model artifacts and data are ignored by Git by default.

The final notebook stage also writes one target-free benchmark record to `backend/test_payload.json` and `data/sample_inputs.csv` for reproducible verification. Keep Flask running in its own terminal, restart it after training so it loads the new bundle, then run `python -m backend.verify_local` from the repository root. This checks the required feature schema and compares the HTTP prediction and probabilities to the same-process Flask reference.

## Start the local full-stack app

In Terminal 1, from the repository root:

```powershell
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-models.txt
python backend/app.py
```

In Terminal 2:

```powershell
cd frontend
npm.cmd ci
npm.cmd start
```

Open `http://localhost:4200`. Angular proxies `/api` to Flask at `127.0.0.1:5000`. The interface supports a network-flow record and keeps inputs local. The backend follows the bundle structure emitted by the notebook, including its label encoder, feature engineering, and CatBoost categorical handling. After the model is ready, the form loads its complete required input schema from `/schema`; fill every required field using values from one flow record. The ?Load example flow? button only fills a small illustrative starting point and does not supply a benchmark prediction.

API endpoints:

- `GET /health` reports whether a model bundle is present.
- `GET /schema` describes the loaded model’s feature names and classes.
- `POST /predict` accepts one JSON flow record and returns the predicted attack type and class probabilities.

Install `backend/requirements-models.txt` in the same environment if you intend to load a model family that depends on LightGBM, XGBoost, or CatBoost. Without the model bundle, `/health` remains available, while `/schema` and `/predict` return HTTP 503 with setup guidance. The UI disables inference in this state. Confirm the services are connected with `Invoke-RestMethod http://127.0.0.1:4200/api/health`; it should return `status: ok`. Before training completes, `model_ready: false` and a prediction request intentionally returns 503. After training, restart Flask and confirm `model_ready: true`; then run `python -m backend.verify_local` and use the form at `http://localhost:4200`, entering the values from `backend/test_payload.json` (including ?Complete model feature set?), then submit. Never add `label` or `type` to the record.

## Checks

```powershell
python -m pip install -r backend/requirements.txt
python -m pytest -q backend/tests
cd frontend
npm.cmd ci
npm.cmd run build
```

CI runs the backend API checks and production Angular build on pushes and pull requests to `main`. On a push to `main`, the GitHub Pages deployment runs only after both CI jobs pass. It intentionally does not train/download the research dataset or load a private model. Build output is uploaded as an Actions artifact.

## Publish a code change

The Angular dev server refreshes local UI edits while it is running. To publish a change, commit and push it to `main`:

```powershell
git add .
git commit -m "Describe the change"
git push origin main
```

GitHub Actions then checks the backend and builds the frontend. A successful run deploys the frontend to Pages; a failed check stops deployment. Pull requests run CI checks but are not published until merged to `main`. Backend and model changes still run locally; GitHub Pages hosts only the static Angular frontend.

## GitHub Pages

`.github/workflows/ci.yml` builds the Angular app with the `/DevOps/` project-site base path and deploys the static files to GitHub Pages after CI succeeds. In repository Settings → Pages, set the source to **GitHub Actions**. The Pages site does not host Flask, the model, or inference. Its model state will be unavailable by design; local predictions require the local Flask server and the trusted model artifact.

## Project layout

```text
backend/                  Flask API and API checks
frontend/                 Angular application
.github/workflows/        CI and GitHub Pages deployment
TON_IoT_Research_Benchmark.ipynb  Research workflow and model artifact generation
data_dictionary.csv       Source dataset field inventory
docs/environment.txt      Detected local tool versions and artifact state
```

## License

No license has been selected for this project yet. Dataset terms and model/data permissions should be reviewed before redistribution.
