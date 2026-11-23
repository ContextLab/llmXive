# Quickstart Guide: Predicting the Effect of Alloying on Poisson's Ratio

This guide provides the steps to install dependencies, configure the environment, and run the full research pipeline for predicting the Poisson's ratio of aluminum alloys.

## 1. Install Requirements

Ensure you are in the project root directory. Create a virtual environment and install the required dependencies:

```bash
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
pip install -r code/requirements.txt
```

## 2. Set MP_API_KEY

The data extraction step requires an API key for the Materials Project. Set this environment variable before running the extraction script:

```bash
export MP_API_KEY="your_materials_project_api_key_here"
```

## 3. Run Data Extraction

Extract raw alloy data from the configured sources (Materials Project and NIST):

```bash
python code/cli/download_cli.py
```

*Output*: `data/raw/alloys_raw.parquet`

## 4. Run Data Cleaning

Clean, filter, and transform the raw data into a processed dataset:

```bash
python code/cli/clean_cli.py
```

*Output*: `data/processed/alloys_clean.parquet`

## 5. Run Modeling Pipeline

Train the Random Forest model, evaluate performance, and save results:

```bash
python code/cli/model_cli.py
```

*Outputs*:
- `models/rf_model.pkl` (Trained model)
- `data/processed/model_metrics.json` (Performance metrics)
- `results/feature_importance.json` (Feature importance scores)
- `results/final_report.md` (Final research report)

## Verification

After completing all steps, verify that the following files exist:
- `data/processed/alloys_clean.parquet`
- `models/rf_model.pkl`
- `results/final_report.md`

If any step fails, check `data/logs/exclusion_log.txt` for filtering details and `data/logs/pipeline.log` for execution errors.