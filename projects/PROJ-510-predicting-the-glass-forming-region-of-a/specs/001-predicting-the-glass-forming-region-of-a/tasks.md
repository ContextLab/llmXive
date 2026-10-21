# Tasks: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the provided JSON-Schema contracts.

This research study implements a machine learning pipeline to determine the correlation between thermodynamic descriptors and the critical cooling rate (CCR) of ternary alloy systems. The study is designed for a CPU-only environment, utilizing streaming for large datasets and strict schema validation for all artifacts.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the environment and run a thin, end-to-end pipeline on real data to verify the ingestion-to-prediction flow.

- [ ] T001 Establish the project layout, install dependencies (`pandas`, `scikit-learn`, `datasets`, `pyyaml`), and document the execution flow in `specs/001-predict-glass-forming-region/quickstart.md`.
- [ ] T002 [US-1] Implement the data ingestion pipeline in `code/ingestion.py`. 
    - Stream elemental properties from OQMD and fetch the experimental CCR dataset.
    - Implement a robust composition parser for ternary alloys (exactly 3 elements).
    - Filter for valid `glass_forming_label` and `critical_cooling_rate` (log exclusions to `data/logs/exclusion_log.txt` and `data/logs/label_filtering_status.json`).
    - Implement "fail loudly" logic: if $N < 500$ after filtering, raise `ValueError` and write to `data/logs/empty_dataset_error.log`.
    - Implement `try/except` blocks for network fetches that write failures to `data/logs/fetch_error.log`.
    - Output: `data/processed/processed_alloys_raw.csv`.
- [ ] T003 [US-1] Implement thermodynamic feature engineering in `code/features.py` and verify correctness via `tests/unit/test_thermo.py`.
    - Compute mixing enthalpy, atomic size difference, and electronegativity variance using OQMD properties.
    - Ensure no synthetic fallbacks; missing elemental data must raise a `ValueError`.
    - Execute the pipeline to produce `data/processed/processed_alloys.csv` and record its SHA-256 hash in `data/logs/ingestion_hash.txt`.
    - **Checkpoint**: Run a basic `RandomForestRegressor` on this dataset to produce a preliminary `data/models/cv_metrics.json` and verify the full path from raw data to a numeric prediction.

## Phase 2: Complete the study and validate its evidence

**Goal**: Execute the full scientific protocol, including rigorous cross-validation, significance testing, and sensitivity analysis.

- [ ] T004 [US-2] Implement the training and validation framework in `code/trainer.py`.
    - Perform a stratified 80/20 train-test split (`random_state=42`).
    - Execute 5-fold cross-validation for a `RandomForestRegressor` and a `DummyRegressor` (mean predictor).
    - Compute a paired permutation test (10,000 permutations) to determine if RF RMSE is significantly lower than Dummy RMSE ($p < 0.05$).
    - Output: `data/models/random_forest_model.pkl` and `data/models/cv_metrics.json` (conforming to `metrics.schema.yaml`).
- [ ] T005 [US-2] Implement permutation importance analysis in `code/evaluator.py`.
    - Calculate importance for the three thermodynamic descriptors using $n=1000$ iterations (`random_state=42`).
    - Compute empirical p-values for each feature against a shuffled baseline.
    - Output: `data/reports/feature_importance.csv` (conforming to `feature_importance.schema.yaml`).
- [ ] T006 [US-2] Implement the sensitivity analysis sweep in `code/evaluator.py`.
    - Evaluate model performance across binarized thresholds of $[50, 100, 150]$ K/s.
    - Calculate the F1-score for each threshold and determine stability (PASS/FAIL).
    - Output: `data/reports/sensitivity_report.json` (conforming to `sensitivity.schema.yaml`).
- [ ] T007 Perform final artifact integrity and schema validation.
    - Implement `code/validate_schemas.py` to validate all CSVs and JSONs against the provided YAML contracts.
    - Check for collinearity ($|\rho| > 0.8$) among descriptors and log results to `data/logs/collinearity_report.json`.
    - Generate the final `data/models/model_output.json` registry containing all artifact paths and hashes.

## Phase 3: Reproducible results and paper handoff

**Goal**: Synthesize findings into a reproducible report and verify the entire workflow from scratch.

- [ ] T008 Implement `code/generate_report.py` to produce `REPORT.md` from the validated artifacts.
    - Ensure all conclusions are framed as **associational** (FR-006).
    - Explicitly document the limitation of using only three descriptors and the potential bias from omitted predictors like electronic structure (FR-007).
    - Map numerical results from `cv_metrics.json` and `sensitivity_report.json` directly into the text.
- [ ] T009 Perform a final "clean-room" reproducibility run.
    - Execute the entire pipeline from `code/ingestion.py` through `code/generate_report.py` in a fresh environment.
    - Confirm that the resulting `data/logs/ingestion_hash.txt` matches the original and that `validate_schemas.py` reports zero errors.
    - Document the final handoff state in `specs/001-predict-glass-forming-region/research.md`.

## Dependencies and requirement coverage

| Requirement | Task | Verification Command |
|-------------|------|----------------------|
| FR-001, 002, 005, 009, 013, 016, 018 | T002, T003 | `python code/ingestion.py && python code/features.py` |
| FR-003, 008, 010, 019 | T004 | `python code/trainer.py` |
| FR-004 | T005 | `python code/evaluator.py --importance` |
| FR-015 | T006 | `python code/evaluator.py --sensitivity` |
| FR-006, 007 | T008 | `grep -E "associational|limitation" REPORT.md` |
| FR-017 | T007 | `python code/validate_schemas.py` |
| SC-001, 003, 005 | T002 | `cat data/logs/label_filtering_status.json` |
| SC-002 | T004 | `cat data/models/cv_metrics.json` |
| SC-004 | T005 | `cat data/reports/feature_importance.csv` |
| SC-006 | T006 | `cat data/reports/sensitivity_report.json` |
| SC-007 | T007 | `python code/validate_schemas.py` |
