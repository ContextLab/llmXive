---
description: "Task list for feature implementation – Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses"
---

# Tasks: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts in `specs/001-predict-the-influence-of-alloying-on/contracts/`  
**Prerequisites**: None (all tasks start from a fresh repository)

> **Notation**  
> `- [ ] T### [P] [USx] description …`  
> `P` = can run in parallel with other tasks that touch different files.  
> `USx` = user‑story label (US1 = Data Ingestion, US2 = Modeling & Feature Engineering, US3 = Interpretation & Reporting).  
> Indented lines list concrete outputs and verification checks.

## Phase 1 – Core Infrastructure & First End‑to‑End Run

- [X] T001 [P] [US1] Create project skeleton and basic utilities  
  - Directories created: `code/`, `data/raw/`, `data/processed/`, `artifacts/models/`, `artifacts/metrics/`, `figures/`, `paper/`, `tests/`, `specs/001-predicting-the-influence-of-alloying-on/contracts/`, `logs/`.  
  - Add `code/__init__.py` that configures a project‑wide logger writing to `logs/`.  
  - Implement `code/resource_monitor.py` with a `@limit_resources` decorator that reads limits from `config.yaml` (runtime ≤ 6 h, RAM ≤ 7 GB) and writes usage to `data/resource_usage.json`.  
  - **Verification**: All listed directories exist, importing `code` produces a logger, and after a dummy decorated function runs, `data/resource_usage.json` contains keys `runtime_seconds` and `peak_ram_gb`.

- [ ] T002 [P] [US1] Implement robust Zenodo ingestion pipeline (`code/ingest.py`)   <!-- FAILED-IN-EXECUTION: code/download_dataset.py exit=1; code/ingest.py exit=1 -->
  - Attempt download of the primary dataset DOI `10.5281/zenodo.10043838`; on failure automatically retry the fallback DOI `10.5281/zenodo.11023456`. If both fail, raise a clear `RuntimeError` (no synthetic fallback).  
  - Stream the CSV using `pandas.read_csv(..., chunksize=1000)` to stay within the 7 GB RAM budget.  
  - Validate each chunk against `specs/001-predicting-the-influence-of-alloying-on/contracts/dataset.schema.yaml` via `jsonschema`.  
  - Drop any record missing `tg_value` or a complete `elements` mapping (fulfilling FR‑001).  
  - Write the cleaned table to `data/processed/cleaned_data.csv` (must contain > 0 rows).  
  - Emit ingestion statistics to `data/ingestion_stats.json` with keys: `source_doi`, `raw_count`, `cleaned_count`, `retention_rate`.  
  - Log all actions and the DOI actually used to `logs/ingest.log`.  
  - **Verification**: `cleaned_data.csv` exists with > 0 rows, `ingestion_stats.json` includes all required keys with sensible numeric values, and `logs/ingest.log` records the selected DOI.

- [ ] T003 [P] [US1] Add unit & integration tests for the ingestion pipeline (`tests/unit/test_ingest_schema.py`, `tests/integration/test_ingest_real.py`)  
  - Unit test checks that a valid CSV passes schema validation and an invalid CSV raises `jsonschema.ValidationError`.  
  - Integration test performs a real download attempt of the primary DOI (no mocks) and verifies that the fallback DOI is used when the primary is unreachable; also checks that a `RuntimeError` is raised when both DOIs fail.  
  - **Verification**: Tests exist and initially fail (red‑green workflow); after `code/ingest.py` is completed they pass.

## Phase 2 – Descriptor Computation, Modeling, & Statistical Validation

- [ ] T004 [P] [US2] Compute atomic descriptors and diagnostic log (`code/descriptors.py`)  
  - Using `mendeleev==0.31.0`, calculate for each composition: `radius_mismatch`, `electronegativity_diff`, `VEC`, and the diagnostic `weighted_mean_radius`.  
  - Save the diagnostic scalar to `data/processed/diagnostic_log.json` **and** copy it verbatim to `artifacts/metrics/diagnostic_log.json`.  
  - Write the three model‑ready descriptors (excluding `weighted_mean_radius`) to `data/processed/descriptors.csv`.  
  - **Verification**: `diagnostic_log.json` exists in both locations with identical float value; `descriptors.csv` exists, is non‑empty, contains exactly the columns `radius_mismatch`, `electronegativity_diff`, `VEC`, and does **not** contain `weighted_mean_radius`.

- [ ] T005 [P] [US2] Generate family‑size stratification status (`code/stratify.py`)  
  - Read `data/processed/cleaned_data.csv`, count records per `family`.  
  - For any family with < 50 samples, log a `STRATIFICATION_WARNING` to `logs/train.log`.  
  - Write `data/processed/stratification_status.json` with entries `{ "family": "<name>", "sample_count": <int>, "warning": true/false }`.  
  - **Verification**: JSON file exists, contains a record for every family, and `warning` is `true` exactly for families with < 50 samples.

- [ ] T006 [P] [US2] Train Gradient Boosting Regressor with LOFO CV (`code/train.py`)  
  - Perform Leave‑One‑Family‑Out cross‑validation (no family appears in both train and test folds) and limit the grid‑search to **≤ 10** hyperparameter combinations.  
  - Select the best model (highest mean R²) and serialize to `artifacts/models/best_model.pkl`.  
  - Compute performance metrics: `r2_mean`, `r2_std`, `mae_mean`, and **baseline null‑model R² (`null_model_r2`)** on each test fold.  
  - Record feature importances (mean over CV folds).  
  - Save a JSON file `artifacts/metrics/model_performance.json` containing the performance metrics **including** `null_model_r2` and a boolean field `model_beats_null` indicating whether `r2_mean` > `null_model_r2`.  
  - Wrap the training function with `@limit_resources` to enforce FR‑005; resource usage is written to `data/resource_usage.json`.  
  - **Verification**: `best_model.pkl` loads with `pickle`; `data/resource_usage.json` reports peak RAM ≤ 7 GB and runtime ≤ 6 h; `artifacts/metrics/model_performance.json` exists with keys `r2_mean`, `null_model_r2`, and `model_beats_null` = true; LOFO CV splits are logged in `logs/train.log`; the grid‑search log shows no more than 10 hyperparameter combos evaluated.

- [ ] T007 [P] [US2] Post‑hoc sensitivity analysis on `max_depth` (`code/sensitivity.py`)  
  - Re‑train the model for each `max_depth` in `{3, 5, 7}` using the same LOFO splits and the best hyperparameters for the other parameters.  
  - Record the R² for each depth, compute variance σ², and store results in `artifacts/metrics/sensitivity_analysis.json` with fields `max_depth_sweep` (list of `{max_depth, r2_score}`) and `r2_variance`.  
  - **Verification**: JSON file exists, contains three entries for the three depths, and `r2_variance` is a non‑negative float.

- [ ] T008 [P] [US3] Compute pairwise correlations and apply Benjamini‑Hochberg FDR correction (`code/correlate_fdr.py`)  
  - Load `data/processed/descriptors.csv`.  
  - For every unordered pair of the three predictors, calculate Pearson r & p‑value, Spearman ρ & p‑value.  
  - Write raw results to `data/processed/correlation_matrix.csv` with columns `feature_pair`, `pearson_r`, `pearson_p`, `spearman_rho`, `spearman_p`.  
  - Perform BH correction at α ≤ 0.05 on the three raw p‑values and write corrected values to `data/processed/fdr_corrected_pvalues.json` (`{ "<pair>": <float> }`).  
  - **Verification**: `correlation_matrix.csv` exists with three rows, all numeric columns populated; `fdr_corrected_pvalues.json` exists with three corrected p‑values between 0 and 1.

- [ ] T009 [P] [US3] Compute VIF and flag collinearity (`code/vif.py`)  
  - Using the descriptor matrix (excluding `weighted_mean_radius`), compute VIF for each predictor.  
  - Create `data/processed/vif_diagnostic_log.json` with keys `vif_values` (feature → float), `flagged_features` (list of features with VIF > 5), and `collinearity_flag` (boolean, true if any VIF > 5).  
  - Compute the condition number of the predictor matrix and write `data/processed/collinearity_log.json` containing `condition_number` (float) and `status` (`"warning"` if > 30 else `"ok"`).  
  - **Verification**: Both JSON files exist, VIF values are numeric, `flagged_features` lists any > 5, `collinearity_flag` matches the presence of such features, and `collinearity_log.json` respects the threshold logic.

- [ ] T010 [P] [US3] Bootstrap feature‑importance statistics and produce summary (`code/bootstrap_fi.py`)  
  - Using the best model from T006, perform 200 bootstrap resamples of the training data (sampling with replacement).  
  - For each resample, compute feature importances; aggregate to produce mean importance, standard deviation, and 95 % confidence intervals for each predictor.  
  - Write `data/processed/feature_importance_bootstrap.json` containing per‑feature arrays of importance values plus fields `mean`, `std`, `ci_lower`, `ci_upper`.  
  - Generate a summary CSV `data/processed/feature_importance_summary.csv` with columns `feature`, `mean_importance`, `std_importance`, `ci_lower`, `ci_upper`.  
  - **Verification**: JSON file exists with required statistics for all three predictors; summary CSV exists, contains a row per predictor, and all numeric columns are populated.

- [ ] T011 [P] [US3] Assemble final ModelArtifact JSON (`code/assemble_artifact.py`)  
  - Consume:  
    * `artifacts/models/best_model.pkl` (model metadata),  
    * `artifacts/metrics/sensitivity_analysis.json` (sensitivity variance),  
    * `data/processed/fdr_corrected_pvalues.json` (FDR‑adjusted p‑values),  
    * `data/processed/vif_diagnostic_log.json` (`collinearity_flag`),  
    * `data/processed/correlation_matrix.csv` (raw correlations),  
    * `data/processed/feature_importance_summary.csv` (bootstrapped CI).  
  - Construct a JSON object conforming to `contracts/artifact.schema.yaml` with fields: `artifact_id`, `model_type`, `hyperparameters`, `performance_metrics`, `feature_importances`, `sensitivity_variance`, `fdr_corrected_pvalues`, `associational_statement` (exact phrase), `collinearity_flag`, `correlations` (populated from the CSV), and `feature_importance_ci` (populated from the summary CSV).  
  - Write the result to `artifacts/metrics/metrics.json`.  
  - **Verification**: `metrics.json` validates against `contracts/artifact.schema.yaml` (all required properties present, correct types, and `associational_statement` equals the mandated string).

- [ ] T012 [P] [US3] Produce scientific figures and final report (`code/report.py`)  
  - Partial‑dependence plots for each predictor → `figures/pdp_radius_mismatch.png`, `figures/pdp_vec.png`, `figures/pdp_electronegativity.png`.  
  - Correlation heat‑map → `figures/correlation_heatmap.png`.  
  - Feature‑importance stability plot (using `data/processed/feature_importance_summary.csv`) → `figures/feature_importance_stability.png`.  
  - Assemble `paper/report.md` that:  
    * Summarizes ingestion stats, stratification warnings, model performance, sensitivity variance, VIF flag, condition number, and FDR‑corrected correlations.  
    * Presents the bootstrapped importance confidence intervals (reading from `artifacts/metrics/metrics.json` field `feature_importance_ci`).  
    * Contains the exact phrase **“These findings are associational only.”** (FR‑004).  
    * Omits causal verbs such as “causes” or “determines”.  
    * Embeds all generated figures.  
  - **Verification**: `paper/report.md` exists, includes the required phrase, contains no prohibited language, references all figure files, and the tables match the data in `artifacts/metrics/metrics.json`.

- [ ] T015 [P] [US2] Perform quantitative power‑analysis (`code/power_analysis.py`)  
  - Run the Monte‑Carlo simulation described in the plan to estimate statistical power for detecting a ΔR² = 0.05 improvement over the null model.  
  - Append the resulting `power_estimate` (float between 0 and 1) to `artifacts/metrics/model_performance.json`.  
  - **Verification**: `model_performance.json` contains a numeric `power_estimate` field with value ≥ 0.0 and ≤ 1.0.

- [ ] T013 [P] Run full pipeline and verify artifact integrity (`code/run_all.sh`)  
  - Execute the ordered scripts: `code/download_dataset.py → code/ingest.py → code/descriptors.py → code/stratify.py → code/train.py → code/sensitivity.py → code/correlate_fdr.py → code/vif.py → code/bootstrap_fi.py → code/power_analysis.py → code/assemble_artifact.py → code/report.py`.  
  - On success, script exits 0; if both DOI downloads fail, exit 1 with the exact string `DATA_UNAVAILABLE`.  
  - After a successful run, invoke `code/verify_artifacts.py` which validates `artifacts/metrics/metrics.json` against `contracts/artifact.schema.yaml`, checks that `paper/report.md` complies with the no‑causal‑language rule, and confirms the presence of all required files (including bootstrapped statistics, figures, and `power_estimate`).  
  - **Verification**: `run_all.sh` returns the expected exit code, `verify_artifacts.py` exits 0, and `logs/verification.log` records a pass.

- [ ] T014 [P] Add GitHub Actions CI workflow (`.github/workflows/ci.yml`)  
  - Workflow stages: `download`, `ingest`, `descriptor`, `stratify`, `train`, `sensitivity`, `correlate_fdr`, `vif`, `bootstrap_fi`, `power_analysis`, `assemble_artifact`, `report`, `validate`.  
  - Each job runs the corresponding script and fails on non‑zero exit unless the failure message is exactly `DATA_UNAVAILABLE` (treated as graceful early exit).  
  - Triggered on pushes to the feature branch and on pull‑request events.  
  - **Verification**: YAML file exists at the specified path, validates with `actionlint`, and a manual workflow dispatch shows the expected job sequence.

### Dependency & Execution Order Summary

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T002 |
| T004 | T002 |
| T005 | T004 |
| T006 | T004, T005 |
| T007 | T006 |
| T008 | T004 |
| T009 | T008 |
| T010 | T006 |
| T011 | T006, T007, T008, T009, T010 |
| T012 | T011 |
| T015 | T012 |
| T013 | T001–T012, T015 (full pipeline) |
| T014 | T013 (workflow definition) |

All tasks together satisfy **every functional and scientific requirement** of the specification while remaining executable on the default CPU‑only CI environment.