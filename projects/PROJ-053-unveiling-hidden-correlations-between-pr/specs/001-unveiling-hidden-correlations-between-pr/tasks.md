# Tasks: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Input**: Design documents from `/specs/001-unveiling-hidden-correlations/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `android/src/` or `ios/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001A [P] Create data directory structure: `projects/PROJ-053-unveiling-hidden-correlations-between-pr/data/`, `data/raw/`, `data/processed/`, `results/`, `docs/`, `state/`
- [ ] T001B [P] Create test directory structure: `tests/`, `tests/unit/`, `tests/integration/`
- [ ] T001C-1 [P] Create `code/` directory.
- [ ] T001C-2 [P] Create `code/__init__.py`.
- [ ] T001C-3 [P] Create `code/config.py`.
- [ ] T001D [P] Create configuration and dependency files: `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/requirements.txt` (initially empty), `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` (initially empty), `contracts/` directory

**Phase 1 Complete - Foundation Ready**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/schema_validator.py` to validate CSV against `contracts/dataset.schema.yaml`. **Logic**: Load the YAML schema, read the CSV, and verify all required columns exist and contain numeric data (parsing strings as floats if necessary). Raise a `ValueError` if validation fails. **Deliverable**: `code/data/schema_validator.py`. **Verify**: Script runs without error on a valid CSV and raises `ValueError` on an invalid CSV.
- [X] T007 Setup `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` to manage paths (`data/raw/`, `data/processed/`, `results/`) and random seeds (fixed)
- [X] T009 Configure error handling and logging infrastructure in `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` and `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/utils/logger.py`
- [X] T010 Create `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` keys for manual data placement paths (e.g., `MANUAL_DATA_PATHS`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: A researcher uploads or downloads a raw public AM alloy dataset and receives a clean, normalized CSV ready for modeling, with missing values handled and categorical variables encoded.

**Independent Test**: Can be fully tested by running the preprocessing script on a known raw dataset file and verifying the output CSV contains normalized numeric columns, one-hot encoded alloy types, and no missing values, with a log file confirming the imputation and normalization steps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011 [P] [US1] Unit test for median imputation logic in `tests/unit/test_preprocess.py`
- [X] T012 [P] [US1] Unit test for one-hot encoding of `alloy_type` in `tests/unit/test_preprocess.py`
- [X] T013 [P] [US1] Integration test for full pipeline from raw CSV to processed CSV in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T014A-1 [US1] [DEPENDS ON T006, T010] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/download.py` (Part 1: Verified Source Download). **Action**: Implement logic to attempt download from verified sources (Zenodo, HuggingFace, UCI) for AM alloy datasets. Include retry logic with backoff. If successful, save to `data/raw/am_raw_data.csv` and log checksum. **Constraint**: If all verified sources fail, proceed to T014B-1. **Deliverable**: `code/data/download.py` with download logic. **Verify**: Script successfully downloads from a verified source or fails with a clear error after retries.
- [ ] T014B-1 [US1] [DEPENDS ON T014A-1] **Manual Data Placement Enforcement (Check)**. **Action**: Check for the existence of `data/raw/am_raw_data.csv`. If missing, raise a `FileNotFoundError` with the exact message: "No verified source found for AM-Machine-Learning dataset. Automated download failed after retries. Please manually place a valid CSV file at `data/raw/am_raw_data.csv`." **Deliverable**: `code/data/download.py` updated with check. **Verify**: Script raises error when file is missing after download failure.
- [ ] T015B-1 [US1] [DEPENDS ON T014A-1] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/validate_source_independence.py` (Part 1: Log Validation). **Action**: Check for the existence of `data/raw/source_independence_log.txt`. **Constraint**: If missing, HALT execution with error: "Constitution Principle VII Violation: Source independence log missing. Predictor and target data streams must be verified as independent. Please provide `data/raw/source_independence_log.txt`." **Deliverable**: `code/data/validate_source_independence.py`. **Verify**: Script halts if log is missing.
- [ ] T015B-2 [US1] [DEPENDS ON T015B-1] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/validate_source_independence.py` (Part 2: Content Validation). **Action**: Parse `source_independence_log.txt` (JSON format: `{"predictors": ["col1",...], "targets": ["col2",...]}`). Verify that these columns exist in the raw CSV. If any listed column is missing in the CSV, **HALT execution** with an error detailing the missing column. **Deliverable**: `code/data/validate_source_independence.py`. **Verify**: Script halts if columns in log are missing in CSV.
- [ ] T016A-1 [US1] [DEPENDS ON T015B-2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 1: Scope Detection). **Action**: Check for column named `fatigue_life` (case-insensitive). If missing, write a log entry to `data/processed/preprocessing.log`: `[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility. (See Plan Assumption: Dataset-variable fit)`. **Deliverable**: Log entry in `data/processed/preprocessing.log`. **Verify**: Log contains scope reduction entry.
- [ ] T016A-2 [US1] [DEPENDS ON T016A-1] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 2: Target Reconfiguration). **Action**: If `fatigue_life` is missing, write `data/processed/target_config.json` with `{"active_targets": ["yield_strength", "ductility"]}`. **This artifact is mandatory**. **Deliverable**: `data/processed/target_config.json`. **Verify**: File exists and contains correct JSON.
- [ ] T016A-3 [US1] [DEPENDS ON T016A-2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3: Sample Count Check). **Action**: Verify if N < 50. If so, **HALT execution** with the **exact** error message: "Insufficient data for GPR training; minimum 50 samples required." **Deliverable**: Error handling in `code/data/preprocess.py`. **Verify**: Script halts with correct error if N < 50.
- [ ] T016B-1 [US1] [DEPENDS ON T016A-3] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 2: Imputation). **Action**: Median‑impute missing numeric values; log counts. **Deliverable**: Imputed dataset. **Verify**: No missing values remain.
- [ ] T016B-2 [US1] [DEPENDS ON T016B-1] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 2.1: Encoding). **Action**: One‑Hot Encoding: Encode `alloy_type` into binary columns (`is_<type>`), then drop original column. **Deliverable**: Encoded dataset. **Verify**: `alloy_type` column removed, binary columns added.
- [ ] T016C-1 [US1] [DEPENDS ON T016B-2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3: Split). **Action**: Perform train-test split (stratified by `alloy_type` if present) **before** scaling. **Deliverable**: Split datasets. **Verify**: Train and test sets created.
- [ ] T016C-2 [US1] [DEPENDS ON T016C-1] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3.1: Target Preservation). **Action**: Preserve Original Target: Save the original (unnormalized) target vector to `data/processed/original_target.npy` for later metric calculation (T029A). **Deliverable**: `data/processed/original_target.npy`. **Verify**: File exists.
- [ ] T016C-3 [US1] [DEPENDS ON T016C-2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3.2: Normalization). **Action**: Fit `MinMaxScaler` on training set only; transform train and test. **Deliverable**: Normalized datasets. **Verify**: Values in [0,1].
- [ ] T016C-4 [US1] [DEPENDS ON T016C-3] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3.3: Artifact Generation). **Action**: Save min/max values to `data/processed/normalization_bounds.json`. Output: Write `data/processed/train.csv` and `data/processed/test.csv`. **Deliverable**: `data/processed/normalization_bounds.json`, `train.csv`, `test.csv`. **Verify**: Files exist.
- [ ] T016D [US1] [DEPENDS ON T014A-1, T014B-1, T015B-2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 4: Filter and Save Intermediate Dataset). **Action**: Load raw CSV, calculate Variance Inflation Factor (VIF) for predictors. If VIF > 5 for any feature, log a WARNING and construct `energy_density` feature. Drop zero-variance columns. Save intermediate dataset to `data/processed/filtered.csv`. **Deliverable**: `data/processed/filtered.csv`. **Verify**: File exists with correct columns.
- [ ] T015B-3 [US1] [DEPENDS ON T016D] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/validate_source_independence.py` (Part 3: Exclusion List Generation). **Action**: Check for derived feature columns (e., `energy_density`). If found, log a WARNING and add to `data/processed/excluded_columns.yaml`. **Output**: Write `data/processed/excluded_columns.yaml` listing excluded columns (initially just derived columns). **Deliverable**: `data/processed/excluded_columns.yaml`. **Verify**: File exists and contains expected columns.
- [X] T022 [US1] [DEPENDS ON T016C-4] Write log entries for imputation counts, dropped columns, and normalization stats to `data/processed/preprocessing.log`. **Action**: Ensure the log file contains entries for `imputation_count`, `dropped_columns`, and `normalization_bounds` with specific values. **Deliverable**: Updated `data/processed/preprocessing.log`. **Verify**: Log contains entries with specific values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gaussian Process Regression Model Training and Validation (Priority: P2)

**Goal**: A researcher trains a Gaussian Process Regression model to predict mechanical properties from processing parameters and receives performance metrics (R², RMSE) documenting the model's predictive capability.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed data, verifying the model object is saved, and checking a results JSON file for R² and RMSE values that are reported (without arbitrary pass/fail thresholds).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for GPR hyperparameter optimization in `tests/unit/test_gpr.py`
- [X] T024 [P] [US2] Integration test for model training and metric calculation in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/baseline_trainer.py` to train Linear Regression on the same training set for SC‑001 comparison
- [X] T026 [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py` to train GPR with RBF kernel using k‑fold cross‑validation to maximize log marginal likelihood **and output permutation_importance.json**. **Deliverable**: GPR model object and `results/permutation_importance.json`. **Verify**: Model saved and importance file generated.
- [X] T027 [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/metrics.py` to calculate R², RMSE, and MAE on a held‑out test set
- [X] T030 [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/stratified_analysis.py`:
 - Group the processed data by `alloy_type` (if present) and compute per‑group R², RMSE, MAE using the trained GPR model.
 - Write a structured JSON artifact `results/confounder_analysis.json` containing a dictionary keyed by alloy type with the metrics.
- [ ] T029A [US2] [DEPENDS ON T026, T027, T016C-4] Calculate and Save Metrics. **Action**: Calculate raw metrics (GPR R², RMSE, MAE; Baseline R², RMSE, MAE). Handle edge case for `rmse_percentage_of_range` (if range < 1e-6, set to null). Calculate `delta_r2` and `percentage_improvement`. Save all metrics to `results/metrics.json` with fixed precision. **Deliverable**: `results/metrics.json`. **Verify**: File exists with correct schema.
- [ ] T031A [US3] [DEPENDS ON T026, T016C-4] Load, Validate, and Correlate Baseline. **Action**: Check for `data/baseline_importance.json` first. If missing, check `data/literature_baseline_importance.json`. If both missing, use stability analysis as a fallback and log that SC-004 is "Partially Met". Calculate correlation between permutation importance (loaded from `results/permutation_importance.json`) and baseline. **Deliverable**: Correlation value in `results/metrics.json`. **Verify**: Value calculated or fallback logged.
- [ ] T031B [US3] [DEPENDS ON T026, T016C-4] Implement Uncertainty Quantification. **Action**: Calculate percentage of test samples in "high uncertainty" regions (σ > 2× median) and save to `results/metrics.json` as `high_uncertainty_percentage`. **Deliverable**: `results/metrics.json` updated. **Verify**: Value calculated.
- [ ] T055 [US2] [DEPENDS ON T029A, T026, T016C-4] Perform Residual Analysis. **Action**: Analyze residuals of GPR model. Test for non-linearity using permutation test. Save results to `results/residual_analysis.json`. **Deliverable**: `results/residual_analysis.json`. **Verify**: File exists.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Uncertainty Quantification and Visualization (Priority: P3)

**Goal**: A researcher views contour plots of predicted mechanical properties overlaid with uncertainty heatmaps to identify parameter regimes with high prediction confidence versus those requiring further experimentation.

**Independent Test**: Can be fully tested by running the visualization script, confirming PNG files are generated, and verifying that regions with high predicted standard deviation (σ) are correctly highlighted in red on the uncertainty heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for uncertainty threshold calculation (multiplier of median) in `tests/unit/test_viz.py`
- [X] T034 [P] [US3] Integration test for contour and heatmap generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T035 [US3] [DEPENDS ON T016C-4, T026] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/viz/contour_plots.py` to generate contour plots of predicted Yield Strength vs. Laser Power and Scan Speed. **Action**: Load `data/processed/normalization_bounds.json` to convert normalized axes back to physical units and annotate plot titles/labels accordingly.
- [X] T036 [US3] [DEPENDS ON T016C-4, T026] Extend `contour_plots.py` to generate uncertainty heatmaps where σ > 2× median is colored red. **Action**: Load `data/processed/normalization_bounds.json` to annotate axes with physical units.
- [X] T037 [US3] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/viz/importance.py` to generate Partial Dependence Plots (PDPs) for the top influential parameters (as identified by permutation importance).
- [ ] T040-1 [US3] [DEPENDS ON data/processed/train.csv, data/processed/test.csv] Measure total pipeline time (preprocessing → training → viz) using `time.time()`. **Deliverable**: Runtime value. **Verify**: Value recorded.
- [ ] T040-2 [US3] [DEPENDS ON T040-1] Dynamic limit detection. **Action**: Check `os.environ.get('GITHUB_ACTIONS')`. If `GITHUB_ACTIONS` is set (CI environment): Compare against `config.TIME_LIMIT_SECONDS` (default a standard duration of several hours). If runtime < limit: Set `feasibility_status: "PASSED"`. If runtime >= limit: **log** warning, set `feasibility_status: "FAILED"`, and **do not abort**. If `GITHUB_ACTIONS` is NOT set: Log warning if runtime exceeds a predefined threshold. **Deliverable**: Feasibility status. **Verify**: Status set correctly.
- [ ] T042A [US1] [DEPENDS ON data/processed/train.csv, data/processed/test.csv, data/processed/excluded_columns.yaml] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_us1.py` to orchestrate ONLY User Story 1 (download -> preprocess -> validate). CLI: `--input <raw.csv>` `--output <processed.csv>`. Validate file extensions, enforce `PYTHONHASHSEED=0`. **Note**: Optional orchestration helper for independent US1 testing.
- [ ] T042B [US2] [DEPENDS ON T029A, T031A, T031B, T039, T016C-4] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_us2.py` to orchestrate ONLY User Story 2 (preprocess -> train -> eval). **Action**: Wait for `results/metrics.json` to be fully populated by T029A, T031A, T031B, T039. Validate extensions, enforce reproducibility seed. **Note**: This task depends on the `results/metrics.json` artifact to ensure all metrics are ready for the orchestration flow. **Deliverable**: Orchestration script. **Verify**: Script runs successfully.
- [ ] T043 [US3] [DEPENDS ON results/metrics.json, results/contour_plots/, results/uncertainty_heatmaps/, results/confounder_analysis.json] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_e2e.py` to orchestrate the full pipeline (download -> preprocess -> train -> viz -> report). CLI: `--input <raw.csv>` `--output-dir <out_dir>`. Enforce `PYTHONHASHSEED=0`.
- [ ] T044 [US3] [DEPENDS ON T030, T040-3] Generate `docs/paper.md` compiling metrics, plots, and explicit data provenance acknowledgment (Draft version). This task consumes the scope‑reduction log entry from T016A-1 if applicable, references the baseline importance source used in T031A, and includes the confounder analysis from `results/confounder_analysis.json` (T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045A [P] Create/update `README.md` with installation steps, dependencies, and **manual data placement instructions**. **Action**: Explicitly state that the system requires manual data placement if automated download fails. Provide instructions: "Manual Data Placement: Download a valid AM alloy dataset and save it as `data/raw/am_raw_data.csv`."
- [ ] T045B [P] Finalize `docs/paper.md` with final metrics, plots, and data provenance acknowledgment (Final version).
- [X] T046 [P] Run `flake8` on all `code/` files. **Tool**: `flake8`. **Config**: `.flake8` (create if missing). **Flags**: `--ignore=E501,W605 --max-line-length=100`. **Output**: Save report to `results/linting_report.txt`. **Action**: Fix all errors except unused imports.
- [ ] T047A [P] Profile Memory and Save Report. **Action**: Ensure `memory_profiler` is installed (add to `requirements.txt`). Profile memory usage in `preprocess.py` using `memory_profiler`. **Command**: `python -m memory_profiler code/data/preprocess.py`. Use the `@profile` decorator on the main function. Write `results/memory_profile.json` with `max_memory_mb` and `status: "OK"` or `"WARNING"`. **Deliverable**: `results/memory_profile.json`. **Verify**: File exists.
- [ ] T047B [P] Optimize Memory Usage if Necessary. **Action**: Read `results/memory_profile.json`. If `max_memory_mb >= 7340` (7 GB): Convert numeric columns to `dtype='float32'`. Use chunked reading for large CSVs. Drop unused columns immediately. Re-run profile to verify optimized usage < 7340 MB. Log final result. **Deliverable**: Updated `results/memory_profile.json`. **Verify**: Usage < 7340 MB.
- [X] T051 [P] Unit test for manual data placement validation in T014B-1 in `tests/unit/test_download.py`. **Logic**: This test validates that the error message is correct AND that a `SystemExit` (or equivalent exception) is raised when `data/raw/am_raw_data.csv` is missing and download fails.
- [X] T052 [P] Unit test for 'baseline required' behavior in T031B-1 in `tests/unit/test_importance.py`. **Logic**: The test should verify that a `ValueError` is NOT raised if config citation is missing and no user file is found, ensuring the pipeline continues with null correlation or stability proxy.

---

## Phase 7: Revision & Review (Addressing Analysis Concerns)

**Purpose**: Address specific concerns raised during the `/speckit.analyze` phase regarding data integrity, reproducibility, and edge cases.

- [ ] T053 [P] [REVISION] Implement Strict Data Loader. **Action**: Remove any `try/except` blocks that fall back to synthetic data in `code/data/download.py`. Ensure that if the manual file check (T014B-1) fails, the script raises a `FileNotFoundError` and exits immediately. **Deliverable**: Updated `code/data/download.py`. **Verify**: No synthetic fallback logic exists; script raises error and exits.
- [ ] T054 [P] [REVISION] Update Metrics Documentation. **Action**: Add explicit sample size and sampling method documentation to `results/metrics.json`. If the dataset is sampled (e.g., for memory constraints), record `sample_size`, `sampling_method` (e.g., "first_N_rows", "random_seed_42"), and `representativeness_limitation` in the JSON output. **Deliverable**: Updated `results/metrics.json`. **Verify**: Keys present.
- [ ] T057 [P] [REVISION] Implement Sparse GPR Fallback. **Action**: In `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py`, if N > 500, automatically switch to `GPy` library using `GPy.models.GPRegression` with FITC (Fully Independent Training Conditional) or VFE (Variational Free Energy) approximation. **Constraint**: Only use `GPy` if `scikit-learn` GPR fails due to memory constraints. Document this dependency addition in `requirements.txt` and `results/memory_profile.json`. **Deliverable**: Updated `code/models/gpr_trainer.py`. **Verify**: Logic present and GPy used when N > 500.
- [ ] T058 [P] [REVISION] Implement Source Independence Validation. **Action**: In `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/validate_source_independence.py`, ensure that the predictor columns and target columns are strictly disjoint. If any overlap is detected, halt with a clear error message. **Deliverable**: Updated `code/data/validate_source_independence.py`. **Verify**: Logic present and script halts on overlap.