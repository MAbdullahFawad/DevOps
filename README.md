# TON-IoT Research Benchmark

Comparative and explainable machine-learning experiments for multi-class intrusion detection in IoT/IIoT network traffic using the TON_IoT dataset.

## Contents

- `TON_IoT_Research_Benchmark.ipynb` - the research workflow and evaluation notebook.
- `run_notebook.py` - executes the notebook from start to finish and saves outputs.
- `data_dictionary.csv` - field descriptions for the project data.

The workflow compares Random Forest, LightGBM, XGBoost, Logistic Regression, and CatBoost for binary detection and ten-class attack attribution. It also evaluates leakage controls, compact feature sets, per-class performance, uncertainty, explanations, runtime, and saved model artifacts.

## Setup

Use Python 3.10 or newer. Create an isolated environment and install the notebook dependencies:

```powershell
python -m venv .venv-research
.\.venv-research\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install jupyter nbformat nbclient pandas numpy scikit-learn matplotlib seaborn shap joblib datasets lightgbm xgboost catboost
```

The notebook downloads the TON_IoT data through the Hugging Face `datasets` library, so an internet connection is required for the first run.

## Run

```powershell
python run_notebook.py
```

To work interactively, open `TON_IoT_Research_Benchmark.ipynb` in VS Code with the project environment selected as the kernel.

## Notes

Results depend on dataset versions, label definitions, available hardware, and the installed library versions. Published scores are included as context and are not treated as an exact reproduction target. Generated models, caches, notebook checkpoints, and local environments are intentionally excluded from version control.

## License

No license has been selected for this project yet.