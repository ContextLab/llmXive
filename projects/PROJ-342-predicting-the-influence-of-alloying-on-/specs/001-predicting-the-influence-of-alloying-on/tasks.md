---
description: "Task list for feature implementation – Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses"
---

# Tasks: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Input**: `spec.md`, `plan.md`, `data-model.md`, contracts in `specs/001-predicting-the-influence-of-alloying-on/contracts/`  
**Prerequisites**: None (all tasks start from a fresh repository)

> **Notation**  
> `- [ ] T### [P] [USx] description …`  
> `P` = can run in parallel with other tasks that touch different files.  
> `USx` = user‑story label (US1 = Data Ingestion, US2 = Modeling & Feature Engineering, US3 = Interpretation & Reporting).  
> Indented lines list concrete outputs and verification checks.

## Phase 1 – Core Infrastructure (shared across all stories)

- [X] T001 Create project skeleton, logging, and resource‑monitoring utilities  
  - Create directories: `code/`, `data/raw/`, `data/processed/`, `artifacts/models/`, `artifacts/metrics/`, `artifacts/reports/`, `tests/`, `specs/001-predicting-the-influence-of-alloying-on/contracts/`.  
  - Add `code/__init__.py` that configures a project‑wide logger writing to `logs/` (e.g., `logs/ingest.log`, `logs/train.log`).  
  - Implement `code/resource_monitor.py` with a `@limit_resources` decorator that reads limits from `config.yaml` (runtime ≤ 6 h, RAM ≤ 7 GB) or overrides from environment variables, writes a JSON usage report to `data/resource_usage.json`.  
  - **Verification**: All listed directories exist, `logs/` folder is present, importing `code` produces a logger, and after a dummy decorated function runs, `data/resource_usage.json` contains keys `runtime_seconds` and `peak_ram_gb`.

## Phase 2 – User Story 1: Data Ingestion & Validation (US1)

- [ ] T002 [US1] Implement robust Zenodo ingestion pipeline (`code/ingest.py`)   <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 -->
  - Fetch dataset from primary DOI `10.5281/zenodo.10043838`; on failure, automatically retry fallback DOI `10.5281/zenodo.11023456`.  
  - Stream CSV with `chunksize=1000` to stay within the 7 GB RAM budget.  
  - Validate each chunk against `specs/001-predicting-the-influence-of-alloying-on/contracts/dataset.schema.yaml` using `jsonschema`.  
  - Drop any record missing `tg_value` or a complete `elements` mapping (FR‑001).  
  - Write the cleaned table to `data/processed/cleaned_mg.csv` (non‑empty).  
  - Emit ingestion statistics to `data/ingestion_stats.json` containing keys: `source_doi`, `raw_count`, `cleaned_count`, `retention_rate`.  
  - Log actions and any fallback usage to `logs/ingest.log`.  
  - **Verification**: `cleaned_mg.csv` exists with > 0 rows, `ingestion_stats.json` includes all required keys with sensible numeric values, and the log records the DOI actually used.

- [ ] T003 [P] Add unit & integration tests for the ingestion pipeline (optional but recommended)  
  - `tests/unit/test_ingest_schema.py` checks that a valid CSV passes schema validation and an invalid CSV raises `jsonschema.ValidationError`.  
  - `tests/integration/test_data_ingestion.py` mocks Zenodo responses to verify fallback logic and proper error raising (`DataUnavailableError`) when both DOIs are unreachable.  
  - **Verification**: Tests exist and initially fail (red‑green workflow) before the implementation above is completed.

## Phase 3 – User Story 2: Descriptor Computation (US2)

- [ ] T004 [US2] Compute atomic descriptors and diagnostic log (`code/descriptors.py`)  
  - Using `mendeleev==0.31.0`, calculate for each composition:  
    * `radius_mismatch` (standard deviation of atomic radii)  
    * `electronegativity_diff` (range of Pauling electronegativities)  
    * `VEC` (valence‑electron concentration)  
    * `weighted_mean_radius` **diagnostic only**.  
  - Save the diagnostic scalar to `data/processed/diagnostic_log.json` (`{ "weighted_mean_radius": <float> }`) and copy it verbatim to `artifacts/reports/diagnostic_log.json`.  
  - Write the three model‑ready descriptors (excluding `weighted_mean_radius`) to `data/processed/descriptors.csv`.  
  - **Verification**: `diagnostic_log.json` exists in both locations with the same float value; `descriptors.csv` exists, is non‑empty, contains exactly the columns `radius_mismatch`, `electronegativity_diff`, `VEC`, and does **not** contain `weighted_mean_radius`.

## Phase 4 – User Story 2: Stratification & Model Training (US2)

- [ ] T005 [US2] Generate family‑size stratification status (`code/train.py`)  
  - Inspect `data/processed/cleaned_mg.csv` to count records per `family`.  
  - If any family has < 50 samples, log a `STRATIFICATION_WARNING` to `logs/train.log`.  
  - Write a JSON status file `data/processed/stratification_status.json` with an entry for each family: `{ "family": "<name>", "sample_count": <int>, "warning": true/false }`.  
  - **Verification**: `stratification_status.json` exists, contains a record for every family, and `warning` is `true` exactly for families with < 50 samples.

- [ ] T006 [US2] Train Gradient Boosting Regressor with LOFO CV and persist artifacts  
  - Perform Leave‑One‑Family‑Out cross‑validation (no family appears in both train and test folds).  
  - Grid‑search ≤ 10 hyperparameter combos (e.g., `n_estimators`, `max_depth`, `learning_rate`).  
  - Select the best model (highest mean R²) and serialize to `artifacts/models/best_model.pkl`.  
  - Compute performance metrics: mean R², R² std, mean MAE, and baseline null‑model R² (mean‑prediction).  
  - Record feature importances.  
  - Save all metrics to `artifacts/metrics/metrics.json` with the schema required by `artifact.schema.yaml` plus an additional `null_model_r2` field.  
  - Wrap the training function with `@limit_resources` to enforce FR‑005; resource usage is written to `data/resource_usage.json`.  
  - **Verification**: `best_model.pkl` loads with `pickle`; `metrics.json` contains keys `r2_mean`, `r2_std`, `mae_mean`, `null_model_r2`, `feature_importances`; `data/resource_usage.json` reports peak RAM ≤ 7 GB and runtime ≤ 6 h.

- [ ] T007 [US2] Conduct sensitivity analysis on `max_depth` (FR‑006)  
  - Re‑train the model for each `max_depth` in `{3, 5, 7}` using the same LOFO splits.  
  - Record the R² for each depth, compute variance σ², and store results in `artifacts/metrics/sensitivity_analysis.json` with fields `max_depth_sweep` (list of `{max_depth, r2_score}`) and `r2_variance`.  
  - **Verification**: JSON file exists, contains three entries for the three depths, and `r2_variance` is a non‑negative float.

## Phase 5 – User Story 3: Statistical Validation (US3)

- [ ] T008 [US3] Compute pairwise Pearson & Spearman correlations (`code/analyze.py`)  
  - Load `data/processed/descriptors.csv`.  
  - For every unordered pair of the three predictors, calculate Pearson r, Pearson p, Spearman ρ, Spearman p.  
  - Save a CSV `data/processed/correlation_matrix.csv` with columns `feature_pair`, `pearson_coeff`, `pearson_pvalue`, `spearman_coeff`, `spearman_pvalue`.  
  - **Verification**: CSV exists, has three rows (one per pair), and all numeric columns are populated.

- [ ] T009 [US3] Apply Benjamini‑Hochberg FDR correction (FR‑008)  
  - Read the p‑values from `correlation_matrix.csv`.  
  - Perform BH correction at α ≤ 0.05 and write corrected values to `data/processed/fdr_corrected_pvalues.json` (`{ "<pair>": <float> }`).  
  - **Verification**: JSON file exists, contains three corrected p‑values between 0 and 1.

- [ ] T010 [US3] Calculate VIF and condition number, flag collinearity (FR‑007, edge‑case)  
  - Using the same descriptor matrix (without `weighted_mean_radius`), compute VIF for each predictor.  
  - Create `data/processed/vif_diagnostic_log.json` with keys: `vif_values` (mapping feature → float) and `flagged_features` (list of features with VIF > 5).  
  - Compute the condition number of the predictor matrix, write `data/processed/collinearity_log.json` containing `condition_number` (float) and `status` (`"warning"` if > 30 else `"ok"`).  
  - **Verification**: Both JSON files exist, VIF values are numeric, `flagged_features` lists any > 5, condition number file respects the threshold logic.

- [ ] T014 [US3] Generate bootstrapped feature‑importance statistics for SC‑002  
  - Using the best model from T006, perform 200 bootstrap resamples of the training data (sampling with replacement).  
  - For each resample, compute feature importances and store them.  
  - Aggregate results to produce mean importance, standard deviation, and 95 % confidence intervals for each predictor.  
  - Write the full distribution and CI summary to `data/processed/feature_importance_bootstrap.json`.  
  - **Verification**: JSON file exists, contains per‑feature arrays of importance values, and includes fields `mean`, `std`, `ci_lower`, `ci_upper`.

- [ ] T015 [US3] Generate feature‑importance stability summary CSV for reporting  
  - Load `data/processed/feature_importance_bootstrap.json`.  
  - Compute mean, standard deviation, and 95 % confidence interval for each predictor.  
  - Write `data/processed/feature_importance_summary.csv` with columns `feature`, `mean_importance`, `std_importance`, `ci_lower`, `ci_upper`.  
  - **Verification**: CSV exists, contains rows for each of the three predictors, and all numeric columns are populated.

## Phase 6 – Reporting (US3)

- [ ] T011 [US3] Produce scientific figures and final report (`code/report.py`)  
  - Partial dependence plots for each predictor → `artifacts/reports/pdp_radius_mismatch.png`, `pdp_vec.png`, `pdp_electronegativity.png`.  
  - Correlation heat‑map → `artifacts/reports/correlation_heatmap.png`.  
  - Stability plot from bootstrapped feature‑importance CIs (generated using the output of T014) → `artifacts/reports/stability_plot.png`.  
  - Assemble `artifacts/reports/final_report.md` that:  
    * Summarizes data ingestion statistics, stratification warnings, model performance, sensitivity variance, VIF flags, condition number, and FDR‑corrected correlations.  
    * Presents the bootstrapped importance confidence intervals **by reading the `data/processed/feature_importance_summary.csv`** and rendering them as a table.  
    * Includes the exact phrase **“These findings are associational only”** (FR‑004).  
    * Contains no causal verbs such as “causes” or “determines”.  
    * Embeds the generated figures.  
  - **Verification**: `final_report.md` exists, contains the required phrase, omits prohibited language, references all figure files, includes a table of bootstrapped CI values (sourced from the CSV), and the table matches the data in `feature_importance_summary.csv`.

## Phase 7 – End‑to‑End Validation & CI Integration

- [ ] T012 Run full pipeline and verify artifact integrity  
  - Execute `bash scripts/run_ci.sh` (or equivalent entry point) on a clean runner.  
  - On success, script exits 0; on expected data‑unavailable situation it exits 1 with the exact string `DATA_UNAVAILABLE`.  
  - After a successful run, invoke `python code/verify_artifacts.py` which: validates `metrics.json` against `artifact.schema.yaml`, checks that `final_report.md` complies with the no‑causal‑language rule, and confirms all required files exist (including the new bootstrapped statistics artifact).  
  - **Verification**: CI script returns the expected exit code, `verify_artifacts.py` exits 0, and a log `logs/verification.log` records the pass.

- [ ] T013 Add GitHub Actions workflow (`.github/workflows/ci.yml`)  
  - Workflow stages: `ingest`, `train`, `analyze`, `report`, `validate`.  
  - Each stage runs the corresponding script and fails on non‑zero exit unless the failure message is exactly `DATA_UNAVAILABLE` (treated as a graceful early exit).  
  - Workflow is triggered on pushes to the feature branch and on pull‑request events.  
  - **Verification**: The YAML file exists at the specified path, validates with `actionlint`, and a manual workflow dispatch shows the expected job sequence.

### Dependency & Execution Order Summary

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T002 (optional) |
| T004 | T002 |
| T005 | T004 |
| T006 | T004, T005 |
| T007 | T006 |
| T008 | T004 |
| T009 | T008 |
| T010 | T008 |
| T014 | T006 |
| T015 | T014 |
| T011 | T008, T009, T010, T014, T015 |
| T012 | T001–T011 (full pipeline) |
| T013 | T012 (workflow definition) |

All tasks are expressed as independent, checkable units that together satisfy **every functional and scientific requirement** of the specification while remaining executable on the default CPU‑only CI environment.