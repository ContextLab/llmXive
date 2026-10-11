# Quickstart: Predicting Tribological Properties from Surface Roughness

This guide walks you through running the full analysis on a fresh GitHub Actions runner (or locally on Linux/macOS). **Prerequisite:** a publicly reachable OpenML dataset ID 42123 and optional Materials Project API key (set as `MATERIALS_PROJECT_API_KEY` env var). If the dataset cannot be fetched, the pipeline will stop with a clear “data‑gap” error.

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
1. **download** – streams OpenML dataset (Phase 0 & 1).  
2. **preprocess** – feature extraction, robust IQR outlier removal, imputation, scaling (Phase 2‑3).  
3. **modeling** – nested cross‑validation, hyper‑parameter tuning, final model training (Phase 5).  
4. **evaluation** – metrics, power analysis, significance testing (Phase 6‑7).  
5. **interpret** – SHAP visualizations and directionality checks (Phase 8).

## 4. Inspect results
- Metrics: `results/metrics.json`
- SHAP plot: `figures/shap_importance.png`
- Summary JSON (ready for paper stage): `results/summary.json` **(the project's SSoT for results)**
- Checksums for raw files: `data/raw/checksums.txt`

## 5. Running unit / contract tests
```bash
pytest -q
```
All tests must pass; the contract test validates that `data/processed/tribology_dataset.parquet` satisfies `contracts/tribology-dataset.schema.yaml`.

## 6. Expected runtime
On the CI runner the full pipeline should complete well within the allocated time limit (SC‑005). If the dataset exceeds available memory, the pipeline automatically streams rows and never loads the entire file into RAM.

**Important:** If the OpenML dataset cannot be downloaded (no verified URL), the script will raise `DataAvailabilityError` and exit with a non‑zero error status. In that case, contact the project owner to provide a verified open dataset URL or adjust the specification accordingly.

---

