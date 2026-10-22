# Quickstart: Predicting Tribological Properties from Surface Roughness

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or locally on Linux/macOS). **Prerequisite:** the OpenML dataset with ID 42123 must be publicly reachable; an optional Materials Project API key can be supplied via environment variable `MATERIALS_PROJECT_API_KEY`. If the dataset cannot be fetched, the pipeline will stop with a clear “data‑gap” error.

## 1. Clone the repository and install dependencies
```bash
git clone https://github.com/your-org/tribology-prediction.git
cd tribology-prediction
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Set optional environment variables
```bash
export MATERIALS_PROJECT_API_KEY="your_api_key_here"   # optional
export RANDOM_SEED=42
```

## 3. Run the pipeline
```bash
python -m src.pipeline.run_all
```
`run_all` orchestrates the phases defined in `plan.md`:

1. **download** – Phase 0 & 1 (data availability check, streaming OpenML dataset).  
2. **extract** – Phase 2 (pySurf roughness extraction or KS‑validated fallback).  
3. **preprocess** – Phase 3 (MAD outlier removal, median imputation with logging, scaling, row‑count assertion).  
4. **split** – Phase 4 (group‑aware train/test split by `pairing_id`).  
5. **modeling** – Phase 5 (nested CV, hyper‑parameter tuning, final model training).  
6. **evaluation** – Phase 6 & 7 (metrics, power analysis, significance testing).  
7. **interpret** – Phase 8 (SHAP plots, directionality reporting).  

## 4. Inspect results
- **Metrics**: `results/metrics.json`  
- **SHAP importance plot**: `figures/shap_importance.png`  
- **Summary JSON (SSoT for downstream paper)**: `results.json`  
- **Raw data checksums**: `data/raw/checksums.txt`

## 5. Run unit & contract tests
```bash
pytest -q
```
All tests must pass; the contract test validates that `data/processed/tribology_dataset.parquet` satisfies `contracts/tribology-dataset.schema.yaml`.

## 6. Expected runtime
On the CI runner the full pipeline should finish well within the allocated time limit (SC‑005). If the dataset size exceeds available memory, the pipeline streams rows and never loads the entire file into RAM.

**Important:** If the OpenML dataset (the specified dataset) cannot be downloaded (no verified URL), the script will raise `DataAvailabilityError` and exit with a non‑zero status. In that case, contact the project owner to provide a verified open dataset URL or adjust the specification accordingly.

---
