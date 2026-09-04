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
- [ ] T001C [P] Create `scripts/init_package.py` to generate `__init__.py` files. **Action**: Create a Python script at `projects/PROJ-053-unveiling-hidden-correlations-between-pr/scripts/init_package.py` that traverses the `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/` and `projects/PROJ-053-unveiling-hidden-correlations-between-pr/tests/` directories and creates an empty `__init__.py` file in every directory. Run this script to initialize the package structure.
- [ ] T001D [P] Create configuration and dependency files: `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/requirements.txt` (initially empty), `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` (initially empty), `contracts/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `contracts/dataset.schema.yaml` file. **Action**: Create the `contracts/` directory if it does not exist. Write the complete YAML content to `contracts/dataset.schema.yaml`. The schema must define required columns (`laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`) and optional `fatigue_life` using this structure:
```yaml
type: object
properties:
 laser_power: { type: number }
 scan_speed: { type: number }
 layer_thickness: { type: number }
 yield_strength: { type: number }
 ductility: { type: number }
 fatigue_life: { type: number }
required: [laser_power, scan_speed, layer_thickness, yield_strength, ductility]
```
- [ ] T006 [P] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/schema_validator.py` to validate CSV against `contracts/dataset.schema.yaml`. **Logic**: Load the YAML schema, read the CSV, and verify all required columns exist and contain numeric data. Raise a `ValueError` if validation fails.
- [X] T007 Setup `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` to manage paths (`data/raw/`, `data/processed/`, `results/`) and random seeds (fixed)
- [X] T009 Configure error handling and logging infrastructure in `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` and `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/utils/logger.py`
- [X] T010 Create `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` keys for manual data placement paths (e.g., `MANUAL_DATA_PATHS`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T005 and T006 must be completed before T014A starts.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: A researcher uploads or downloads a raw public AM alloy dataset and receives a clean, normalized CSV ready for modeling, with missing values handled and categorical variables encoded.

**Independent Test**: Can be fully tested by running the preprocessing script on a known raw dataset file and verifying the output CSV contains normalized numeric columns, one-hot encoded alloy types, and no missing values, with a log file confirming the imputation and normalization steps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for median imputation logic in `tests/unit/test_preprocess.py`
- [X] T012 [P] [US1] Unit test for one-hot encoding of `alloy_type` in `tests/unit/test_preprocess.py`
- [X] T013 [P] [US1] Integration test for full pipeline from raw CSV to processed CSV in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T014A [US1] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/download.py` to validate automated download and manual placement. **Action**:
 1. **Primary Check**: Attempt automated download (T014B) first.
 2. **Fallback**: If automated download fails (network error, 404), log a warning and check for `data/raw/am_data.csv` (manual placement).
 3. **Schema Validation**: If a file exists (downloaded or manual), validate it against `contracts/dataset.schema.yaml` (T005/T006).
 4. **Complete Records Check**: Verify that the required columns (`laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`) contain NO missing values (NaN). If any required column has missing values, log a `WARNING` to `data/processed/preprocessing.log`: "WARNING: Missing values detected in required columns. Imputation will be performed in T016B."
 5. **Constraint**: This task handles both automated download (primary) and manual placement (fallback).
 This satisfies FR‑001 (download/parse) by enforcing the automated download path and validating the loaded data.
- [ ] T014B [US1] [CONDITIONAL ON T014A] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/download.py` (Part 2: Automated Download). **Action**:
 1. **Trigger**: Execute if `data/raw/am_data.csv` is missing or if the previous manual check failed.
 2. **Fetch**: Download from verified source: Zenodo ID `` (AM-Machine-Learning dataset) using `requests` or `huggingface_hub`.
 3. **Validation**: Validate the downloaded file against `contracts/dataset.schema.yaml`.
 4. **Fail Gracefully**: If download fails after 3 retries, raise `FileNotFoundError` with instructions for manual placement.
 5. **Constraint**: This task implements the "MUST download" requirement of FR-001.
- [ ] T015B [US1] [DEPENDS ON T014A, T014B, T006] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/validate_source_independence.py`:
 1. **Direct Column Inspection**: Read the raw CSV (from T014A/T014B) to inspect column names directly.
 2. **Provenance Check**:
 - **Step 2a**: Check for `data/raw/metadata.json`. If present, parse it to verify that predictor variables (process settings) and target variables (mechanical properties) originate from distinct data streams (e.g., different file sources, timestamps, or authors).
 - **Step 2b**: If `metadata.json` is missing, check CSV header comments for provenance notes.
 - **Step 2c**: If neither is present, log a `WARNING` about unverifiable distinct streams but proceed with column inspection.
 3. **Derived Feature Check**: Check for the presence of derived feature columns (e.g., `energy_density`, `line_energy`, `volume_energy`, `energy_per_unit_length`, `heat_input`). Formula for `energy_density` = `laser_power / (scan_speed * layer_thickness)`. If found, log a `WARNING` and add to `data/processed/excluded_columns.yaml`.
 4. **Tautology Check**:
 - **Definition**: A predictor is a tautology if it is a direct mathematical transformation of a target variable.
 - **Logic**: Check if any predictor column has a Pearson correlation > 0.99 with any target variable (`yield_strength`, `ductility`, `fatigue_life`). If so, log a `WARNING` and flag as "data leakage".
 - **Selection Bias**: Check if the dataset contains only "successful prints" (e.g., all yield strength > threshold) or lacks failure cases. If detected, log a `WARNING` about potential selection bias.
 5. **Raw Parameter Identification**: Identify raw process parameters (`laser_power`, `scan_speed`, `layer_thickness`, `alloy_type`).
 6. **Output**: Write the final list of excluded columns to `data/processed/excluded_columns.yaml` in the format:
 ```yaml
 excluded_columns: [col1, col2]
 ```
 This fulfills Plan Task 0.2 (Source Independence & Tautology Check) by handling standard public datasets via direct inspection and enforcing Constitution Principle VII (Physical Measurement Independence) by detecting data leakage and selection bias.
- [ ] T016A [US1] [DEPENDS ON T015B, T005, T006] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 1: Scope & Validation). **Action**:
 1. **Scope Detection & Logging**: Check for column named exactly `fatigue_life` (case-sensitive). If missing, write a log entry to `data/processed/preprocessing.log`:
 ```
 [SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility. (See Plan Assumption: Dataset-variable fit)
 ```
 This entry is later referenced by T044.
 2. **Target Reconfiguration**: If `fatigue_life` is missing, write `data/processed/target_config.json` with `{"active_targets": ["yield_strength", "ductility"]}`. This ensures T026 does not expect missing columns.
 3. **Schema Validation & Column Filtering**: Load the CSV, validate against `contracts/dataset.schema.yaml` (T005/T006). **Crucially**: Load `data/processed/excluded_columns.yaml` (produced by T015B) and drop columns listed therein. If the file is missing or empty, proceed with all validated columns (graceful fallback).
 4. **Zero‑Variance Detection**: Detect columns with zero variance, log a WARNING per column to `preprocessing.log`, and drop them.
 5. **Sample Count Check**: Verify if N < 50. If so, halt execution immediately with error: "Insufficient data for GPR training; minimum 50 samples required."
- [ ] T016B [US1] [DEPENDS ON T016A] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 2: Imputation & Encoding). **Action**:
 1. **Imputation**: Median‑impute missing numeric values; log counts of imputed entries.
 2. **One‑Hot Encoding**: Encode `alloy_type` into binary columns (`is_<type>`), then drop the original column.
- [ ] T016C [US1] [DEPENDS ON T016B] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3: Split & Normalization). **Action**:
 1. **Train/Test Split**: Perform a train-test split (stratified by `alloy_type` if present) **before** any scaling.
 2. **Normalization**: Fit a `sklearn.preprocessing.MinMaxScaler` **only on the training set** and transform both train and test sets.
 3. **Artifact Generation**: Save the per‑feature min/max values to `data/processed/normalization_bounds.json` (replacing removed T019). **Structure**:
 ```json
 {
 "laser_power": {"min": float, "max": float},
 "scan_speed": {"min": float, "max": float},
 "...": {"min": float, "max": float}
 }
 ```
 4. **Output**: Write `data/processed/train.csv` and `data/processed/test.csv`, and persist the log file.
- [ ] T022 [US1] [DEPENDS ON T016C] Write log entries for imputation counts, dropped columns, and normalization stats to `data/processed/preprocessing.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gaussian Process Regression Model Training and Validation (Priority: P2)

**Goal**: A researcher trains a Gaussian Process Regression model to predict mechanical properties from processing parameters and receives performance metrics (R², RMSE) documenting the model's predictive capability.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed data, verifying the model object is saved, and checking a results JSON file for R² and RMSE values that are reported (without arbitrary pass/fail thresholds).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for GPR hyperparameter optimization in `tests/unit/test_gpr.py`
- [X] T024 [P] [US2] Integration test for model training and metric calculation in `tests/integration/test_pipeline.py`
 *Note: T024 MUST include a test case that simulates both literature fetch failure and missing user-baseline file to verify T031 handles the 'baseline required' behavior correctly.*

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/baseline_trainer.py` to train Linear Regression on the same training set for SC‑001 comparison
- [X] T026 [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py` to train GPR with RBF kernel using k‑fold cross‑validation to maximize log marginal likelihood
- [X] T027 [US2] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/metrics.py` to calculate R², RMSE, and MAE on the held‑out test set
- [ ] T029A [US2] [DEPENDS ON T026, T027] Save raw metrics (GPR R², RMSE, MAE; Baseline R², RMSE, MAE) to `results/metrics.json`. **Include**:
 - `rmse_percentage_of_range`: computed as `(rmse / (max(test_y) - min(test_y))) * 100` where `test_y` is the target vector from the **held-out test set** (strictly from T016C's test split, not the full dataset). **Edge Case**: If `max(test_y) == min(test_y)`, set `rmse_percentage_of_range` to `null` and log a warning to avoid division by zero.
 - **Constraint**: Ensure `test_y` is strictly the held-out test set values to prevent data leakage.
- [ ] T029B [US2] [DEPENDS ON T029A] Perform comparative analysis: Calculate `delta_r2 = gpr_r2 - baseline_r2` and `percentage_improvement = (delta_r2 / baseline_r2) * 100`. Append these fields (`gpr_vs_baseline_delta`, `gpr_vs_baseline_percent_improvement`) to `results/metrics.json`. This satisfies SC‑001.
- [X] T030 [US2] [DEPENDS ON T016C] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/stratified_analysis.py`:
 - Group the processed data by `alloy_type` (if present) and compute per‑group R², RMSE, MAE using the trained GPR model.
 - Write a structured JSON artifact `results/confounder_analysis.json` containing a dictionary keyed by alloy type with the metrics.
- [ ] T031 [US2] [DEPENDS ON T026, T016C, T029A] Implement permutation importance correlation analysis:
 1. Compute permutation importance on the trained GPR model.
 2. **Baseline Loading**:
 - **Step 1**: Attempt to load `data/baseline_importance.json` (user‑provided).
 - **Step 2**: If Step 1 fails, load the citation key `LITERATURE_BASELINE_CITATION` from `code/config.py`. This key MUST contain a verified DOI or Zenodo ID (default allow-list:, 10.1016/j.addma.2020.101456). Verify the citation against a primary source (e.g., crossref API) or the allow-list.
 - **Step 3**: If both Step 1 and Step 2 fail (or if the API verification fails due to transient errors), log a `WARNING`: "No verified baseline found. Setting permutation_importance_correlation to null." and set `permutation_importance_correlation` to `null` in `results/metrics.json`. Do NOT halt.
 3. **Calculation**: If a baseline was found, calculate Spearman correlation between model ranking and the baseline ranking from the verified source.
 4. **Output**: Append `permutation_importance_correlation` to `results/metrics.json`.
 5. **Note**: This task now correctly implements the 'user-provided' fallback path required by SC-004, with graceful handling of missing baselines.
- [X] T030 already satisfies Plan Task 2.4; output is now a JSON artifact for traceability.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Uncertainty Quantification and Visualization (Priority: P3)

**Goal**: A researcher views contour plots of predicted mechanical properties overlaid with uncertainty heatmaps to identify parameter regimes with high prediction confidence versus those requiring further experimentation.

**Independent Test**: Can be fully tested by running the visualization script, confirming PNG files are generated, and verifying that regions with high predicted standard deviation (σ) are correctly highlighted in red on the uncertainty heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for uncertainty threshold calculation (multiplier of median) in `tests/unit/test_viz.py`
- [X] T034 [P] [US3] Integration test for contour and heatmap generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T035 [US3] [DEPENDS ON T016C, T026] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/viz/contour_plots.py` to generate contour plots of predicted Yield Strength vs. Laser Power and Scan Speed. **Action**: Load `data/processed/normalization_bounds.json` to convert normalized axes back to physical units (e.g., "Laser Power (W)") and annotate plot titles/labels accordingly.
- [X] T036 [US3] [DEPENDS ON T016C, T026] Extend `contour_plots.py` to generate uncertainty heatmaps where σ > 2× median is colored red. **Action**: Load `data/processed/normalization_bounds.json` to annotate axes with physical units.
- [X] T037 [US3] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/viz/importance.py` to generate Partial Dependence Plots (PDPs) for the top influential parameters (as identified by permutation importance).
- [X] T039 [US3] Calculate percentage of test samples in "high uncertainty" regions and save to `results/metrics.json` with key `high_uncertainty_percentage` (SC‑003). **Logic**: `high_uncertainty_percentage = (count(σ > 2*median) / total_test_samples) * 100`.
- [X] T040 [US3] [DEPENDS ON results/metrics.json, data/processed/train.csv, data/processed/test.csv, results/contour_plots/, results/uncertainty_heatmaps/] Implement runtime instrumentation in `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py`:
 1. Measure total pipeline time (preprocessing → training → viz) using `time.time()`.
 2. Always write `total_runtime_seconds` to `results/metrics.json`.
 3. **Dynamic Limit Detection**: Check `os.environ.get('GITHUB_ACTIONS')`.
 - If `GITHUB_ACTIONS` is set (CI environment): Compare against `TIME_LIMIT_SECONDS` (default 21600) from `code/config.py`. If runtime exceeds the limit, **log** a warning, set `feasibility_status: "FAILED"` in `results/metrics.json`, and **do not abort**; continue to generate remaining artifacts.
 - If `GITHUB_ACTIONS` is NOT set (local environment): Log a warning if runtime exceeds 21600s but do not set `feasibility_status` to FAILED (local runs are not constrained by CI limits).
 4. **Note**: This task is primarily for CI environments; local runs use the default limit as a guideline.
- [ ] T042A [US1] [DEPENDS ON data/processed/train.csv, data/processed/test.csv, data/processed/excluded_columns.yaml] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_us1.py` to orchestrate ONLY User Story 1 (download -> preprocess -> validate). CLI: `--input <raw.csv>` `--output <processed.csv>`. Validate file extensions, enforce `PYTHONHASHSEED=0`.
- [ ] T042B [US2] [DEPENDS ON data/processed/train.csv, data/processed/test.csv, models/gpr_model.pkl, results/metrics.json] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_us2.py` to orchestrate ONLY User Story 2 (preprocess -> train -> eval). CLI: `--input <processed.csv>` `--output <results.json>`. Validate extensions, enforce reproducibility seed. **Note**: This task depends on the `results/metrics.json` artifact (produced by T029A/B/T031) to ensure all metrics are ready for the orchestration flow.
- [ ] T043 [US3] [DEPENDS ON results/metrics.json, results/contour_plots/, results/uncertainty_heatmaps/, results/confounder_analysis.json] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_e2e.py` to orchestrate the full pipeline (download -> preprocess -> train -> viz -> report). CLI: `--input <raw.csv>` `--output-dir <out_dir>`. Enforce `PYTHONHASHSEED=0`.
- [ ] T044 [US3] [DEPENDS ON T030, T040] Generate `docs/paper.md` compiling metrics, plots, and explicit data provenance acknowledgment (Draft version). This task consumes the scope‑reduction log entry from T016A if applicable, references the baseline importance source used in T031, and includes the confounder analysis from `results/confounder_analysis.json` (T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045A [P] Create/update `README.md` with installation steps, dependencies, and **automated download instructions**. **Action**: Explicitly state that the system attempts to download from Zenodo (ID:) by default. Provide a fallback section: "Manual Data Placement: If automated download fails, download a valid AM alloy dataset and save it as `data/raw/am_data.csv`."
- [ ] T045B [P] Finalize `docs/paper.md` with final metrics, plots, and data provenance acknowledgment (Final version).
- [X] T046 [P] Run `flake8` on all `code/` files. **Tool**: `flake8`. **Config**: `.flake8` (create if missing). **Flags**: `--ignore=E501,W605 --max-line-length=100`. **Output**: Save report to `results/linting_report.txt`. **Action**: Fix all errors except unused imports.
- [ ] T047 [P] Profile memory usage and optimize if necessary. **Action**:
 1. Profile memory usage in `preprocess.py` using `memory_profiler`. Log `max_memory_mb` to `results/memory_profile.log`.
 2. **Conditional Optimization**: If `max_memory_mb >= 7000`, apply the following specific techniques:
 - Convert all numeric columns to `dtype='float32'` instead of `float64`.
 - Use chunked reading with `chunksize` parameter when loading large CSVs.
 - Drop unused columns immediately after loading.
 - Log the memory savings achieved.
 3. **Verification**: Re‑run the profile to verify optimized memory usage is < 7000 MB. Log the final result.
- [X] T051 [P] Unit test for manual data placement validation in T014A in `tests/unit/test_download.py`. **Logic**: This test validates that the error message is correct AND that a `SystemExit` (or equivalent exception) is raised when `data/raw/am_data.csv` is missing and download fails.
- [X] T052 [P] Unit test for 'baseline required' behavior in T031 when no baseline is found in `tests/unit/test_importance.py`. **Logic**: The test should verify that a `ValueError` is NOT raised if the config citation is missing AND no user file is found, ensuring the pipeline continues with a null correlation.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel **ONLY AFTER T016C (data pipeline) are complete**
- Different user stories can be worked on in parallel by different team members
- T015B is explicitly NOT parallel (depends on T014A/T014B)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational → Foundation ready
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational together
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Orchestrator Strategy**: Orchestrator tasks (T042A, T042B, T043) depend on **Checkpoint Artifacts** (final output files) rather than individual implementation task IDs. This simplifies the dependency graph and ensures robustness against internal task reordering.
- Removed Tasks: T004 (merged into T005), T008 (duplicate), T017A/B (merged into T016), T018 (merged into T016 and removed from list), T019 (removed and integrated into T016C), T020 (merged into T016A), T021 (merged into T016A), T028A/B/C (no spec), T038 (merged into T035/T036), T041 (duplicate), T048 (conditional/removed), T049 (no spec), T050 (no spec).
- Merged Tasks: T047A/B/C merged into T047.