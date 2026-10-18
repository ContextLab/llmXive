# Quickstart: Predicting Corrosion Rates with Interaction Effects

This guide documents the single end-to-end command to reproduce the full analysis
(data ingestion, validation, feature engineering, model training, significance
testing, SHAP interpretability, and reporting) on a CPU-only environment
(2 vCPUs, ~7 GB RAM, ≤ 6 h wall-time).

## Prerequisites

- Python 3.11
- Git
- Internet access (to download the public corrosion dataset via the `openml` package)

## Steps

1. **Create a virtual environment and install dependencies**

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r src/requirements.txt
    ```

    (The identical pins are mirrored in `code/requirements.txt` for reproducibility.)

2. **Run the full pipeline (single command)**

    ```bash
    python -m src.pipeline.run_all
    ```

    The pipeline will, in order:

    1. Fetch a real tabular corrosion dataset via the `openml` Python package
       (fail-loud search; no synthetic fallback) and record provenance
       (dataset ID, version, URL, SHA-256 checksum) in `metadata/dataset.yaml`.
    2. Validate required columns (pH, salinity, temperature, composition,
       corrosion_rate, source_id), harmonize corrosion rate to mm/year, impute
       missing non-target values, standardize numeric predictors, and one-hot
       encode composition, writing `data/processed/cleaned_dataset.csv`.
    3. Compute VIF diagnostics for base predictors
       (`data/results/vif_diagnostics.json`).
    4. Engineer residualized interaction and degree-2 polynomial features,
       writing `data/processed/features.parquet`.
    5. Train Full, Null, and mean-only baseline models under 5-fold
       StratifiedGroupKFold on `source_id` with a constrained grid search
       (`max_depth ∈ {3,4,5}`, `n_estimators ∈ {50,100,150}`), persisting the
       best model and metadata.
    6. Evaluate on a group-aware 80/20 held-out split and run the paired
       sign-flip Full-vs-Null permutation test, per-column permutation
       importance with Benjamini-Hochberg correction, and the
       target-permutation Full-vs-Null test.
    7. Compute SHAP interaction values and generate figures under
       `outputs/figures/`.
    8. Run the hyperparameter sensitivity sweep (Jaccard stability) and write
       summary tables to `data/results/`.

3. **Run the test suite**

    ```bash
    pytest src/tests/
    ```

    This runs the ingestion unit tests, contract tests, and pipeline tests.

## Key outputs

- Cleaned data: `data/processed/cleaned_dataset.csv`
- Feature matrix: `data/processed/features.parquet`
- Best model: `data/results/best_model.joblib` with metadata in
  `data/results/model_artifact.yaml`
- Metrics and significance tests: `data/results/*.json`
  (e.g. `first_run_metrics.json`, `heldout_metrics.json`,
  `interaction_test.json`, `bh_interaction_importance.json`,
  `target_perm_fullnull.json`, `sensitivity_maxdepth.json`)
- Figures: `outputs/figures/*.png`
- Dataset provenance: `metadata/dataset.yaml`

## Expected runtime and resources

- Total wall-time ≤ 6 h on a 2-vCPU, 7 GB RAM CPU-only runner.
- Peak RSS ≤ 7 GB (monitored via psutil; a documented stratified-sampling
  strategy with a logged seed triggers if exceeded).

## Notes

- All findings are **associational**, not causal: the data are observational.
- If a required column is missing from a candidate dataset, ingestion halts
  with `Error: MISSING_VARIABLE [name] in [source]` (FR-001). A missing
  optional `crystal_structure` column logs a warning and proceeds.