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
- [ ] T001C [DEPENDS ON T001A, T001B] Create `scripts/init_package.py` to generate `__init__.py` files. **Action**: Create a Python script at `projects/PROJ-053-unveiling-hidden-correlations-between-pr/scripts/init_package.py` that traverses the `code/`, `tests/`, `data/`, `results/`, `docs/`, and `state/` directories (relative to project root) and creates an empty `__init__.py` file in every directory. Run this script to initialize the package structure.
- [ ] T001D [P] Create configuration and dependency files: `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/requirements.txt` (initially empty), `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/config.py` (initially empty), `contracts/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `contracts/dataset.schema.yaml` file. **Action**: Create the `contracts/` directory if it does not exist. Write the complete YAML content to `contracts/dataset.schema.yaml`. The schema must define required columns (`laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`) and optional `fatigue_life` (marked as optional with a comment explaining it is not required for the initial run, per Plan Assumption: Dataset-variable fit). **Constraint**: The schema must include a comment indicating that if `fatigue_life` is missing, the system MUST trigger scope reduction logic (see T016A). **Note**: T016A must generate `data/processed/target_config.json` if `fatigue_life` is missing to document this scope reduction.
```yaml
type: object
properties:
 laser_power: { type: number }
 scan_speed: { type: number }
 layer_thickness: { type: number }
 yield_strength: { type: number }
 ductility: { type: number }
 fatigue_life: { type: number } # Optional: not required for initial run (Plan Assumption: Dataset-variable fit). If missing, system MUST log scope reduction and restrict analysis.
required: [laser_power, scan_speed, layer_thickness, yield_strength, ductility]
```
- [ ] T006 [P] [DEPENDS ON T005] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/schema_validator.py` to validate CSV against `contracts/dataset.schema.yaml`. **Logic**: Load the YAML schema, read the CSV, and verify all required columns exist and contain numeric data (parsing strings as floats if necessary). Raise a `ValueError` if validation fails.
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

- [ ] T014A [US1] [DEPENDS ON T005, T006] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/download.py` (Part 1: Manual Validation). **Action**: Validate the manually placed file at `data/raw/am_raw_data.csv` against `contracts/dataset.schema.yaml`. Ensure numeric columns can be parsed as floats (handling scientific notation). Log warnings if missing values are detected but do not halt (imputation handled in T016B).
- [ ] T014B [US1] [DEPENDS ON T005, T006, T014A] **Manual Data Placement Enforcement**. **Action**: If `data/raw/am_raw_data.csv` is missing (after T014A validation attempt), raise `FileNotFoundError` with the exact message: "No verified source found for AM-Machine-Learning dataset. Automated download is disabled per Plan. Please manually place a valid CSV file at `data/raw/am_raw_data.csv`." **Note**: This task replaces the automated download logic which is forbidden by the Plan.
- [ ] T015B [US1] [DEPENDS ON T006, T014A, T014B] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/validate_source_independence.py`:
 1. Read the raw CSV to inspect column names.
 2. **Mandatory Independence Check**: Verify the existence of `data/raw/source_independence_log.txt`.
 3. **HALT CONDITION**: If `source_independence_log.txt` is missing, **HALT execution** with error: "Constitution Principle VII Violation: Source independence log missing. Predictor and target data streams must be verified as independent. Please provide `data/raw/source_independence_log.txt`." **Do NOT proceed**.
 4. **Content Validation**: Parse `source_independence_log.txt` to extract the list of predictor columns and target columns. Verify that these columns exist in the raw CSV. If any listed column is missing in the CSV, **HALT execution** with an error detailing the missing column.
 5. Check for derived feature columns (e.g., `energy_density`). If found, log a WARNING and add to `data/processed/excluded_columns.yaml`.
 6. Output `data/processed/excluded_columns.yaml` listing excluded columns.
 7. **Constraint**: Do NOT implement Tautology/Selection Bias checks here; these are handled in T015C or removed to align with Plan scope.
- [ ] T015C [US1] [DEPENDS ON T016A, T015B] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/feature_engineering.py`:
 1. Calculate Variance Inflation Factor (VIF) for all numeric predictors **excluding columns listed in `excluded_columns.yaml`**.
 2. If VIF > 5 for any predictor, construct `energy_density` feature (`laser_power / (scan_speed * layer_thickness)`) and flag for inclusion.
 3. Handle unit normalization if necessary (ensure consistent units for calculation, e.g., Watts, mm/s).
 4. Log VIF results and feature construction decisions to `data/processed/preprocessing.log`.
- [ ] T016A [US1] [DEPENDS ON T015B] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 1: Scope & Validation). **Action**:
 1. **Scope Detection & Logging**: Check for column named `fatigue_life` (case-insensitive, checking for `fatigue_life`, `fatigue life`). If missing, write a log entry to `data/processed/preprocessing.log`:
 ```
 [SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility. (See Plan Assumption: Dataset-variable fit)
 ```
 2. **Target Reconfiguration**: If `fatigue_life` is missing, write `data/processed/target_config.json` with `{"active_targets": ["yield_strength", "ductility"]}`. **This artifact is mandatory**.
 3. **Schema Validation & Column Filtering**: Load CSV, validate against schema. Load `data/processed/excluded_columns.yaml` and drop listed columns.
 4. **Zero‑Variance Detection**: Detect and drop zero-variance columns.
 5. **Sample Count Check**: Verify if N < 50. If so, **HALT execution** with the **exact** error message: "Insufficient data for GPR training; minimum 50 samples required."
- [ ] T016B [US1] [DEPENDS ON T016A] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 2: Imputation & Encoding). **Action**:
 1. **Imputation**: Median‑impute missing numeric values; log counts.
 2. **One‑Hot Encoding**: Encode `alloy_type` into binary columns (`is_<type>`), then drop original column.
- [ ] T016C [US1] [DEPENDS ON T016B] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py` (Part 3: Split & Normalization). **Action**:
 1. **Train/Test Split**: Perform train-test split (stratified by `alloy_type` if present) **before** scaling.
 2. **Preserve Original Target**: Save the original (unnormalized) target vector to `data/processed/original_target.npy` for later metric calculation (T029A).
 3. **Normalization**: Fit `MinMaxScaler` on training set only; transform train and test.
 4. **Artifact Generation**: Save min/max values to `data/processed/normalization_bounds.json`.
 5. **Output**: Write `data/processed/train.csv` and `data/processed/test.csv`.
- [X] T022 [US1] [DEPENDS ON T016C] Write log entries for imputation counts, dropped columns, and normalization stats to `data/processed/preprocessing.log`. **Action**: Ensure the log file contains entries for `imputation_count`, `dropped_columns`, and `normalization_bounds` with specific values.

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
- [ ] T029A [US2] [DEPENDS ON T026, T027, T016C] Save raw metrics (GPR R², RMSE, MAE; Baseline R², RMSE, MAE) to `results/metrics.json`. **Include**:
 - `rmse_percentage_of_range`: computed as `(rmse / (max(original_test_y) - min(original_test_y))) * 100` where `original_test_y` is the **unnormalized** target vector loaded from `data/processed/original_target.npy` (generated in T016C).
 - **Edge Case**: If `max(original_test_y) - min(original_test_y) < 1e-6`, set `rmse_percentage_of_range` to `null` and log a warning.
 - **Precision**: All float values in JSON must be rounded to a consistent, fixed number of decimal places for determinism.
- [ ] T029B [US2] [DEPENDS ON T029A] Perform comparative analysis: Calculate `delta_r2 = gpr_r2 - baseline_r2`. Calculate `percentage_improvement` only if `baseline_r2 > 0.0`. If `baseline_r2 <= 0`, set `percentage_improvement` to `null` and log a warning. Append `gpr_vs_baseline_delta` and `gpr_vs_baseline_percent_improvement` to `results/metrics.json`. This satisfies SC‑001.
- [X] T030 [US2] [DEPENDS ON T016C] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/stratified_analysis.py`:
 - Group the processed data by `alloy_type` (if present) and compute per‑group R², RMSE, MAE using the trained GPR model.
 - Write a structured JSON artifact `results/confounder_analysis.json` containing a dictionary keyed by alloy type with the metrics.
- [ ] T031A [US2] [DEPENDS ON T026, T016C, T007, T031C] Implement user-provided/literature baseline correlation analysis:
 1. Attempt to load `data/baseline_importance.json`.
 2. **Schema Validation**: Validate against `contracts/baseline.schema.yaml` (created in T031C). Verify the file contains keys `feature_name` and `importance_rank`. If schema mismatch, log WARNING and set correlation to `null`.
 3. **Calculation**: If valid, calculate Spearman correlation between model ranking and baseline ranking.
 4. **Output**: Append `permutation_importance_correlation_user` to `results/metrics.json`. **Note**: If the file is missing or invalid, set this value to `null` and log a warning indicating the fallback to internal stability analysis (T031B) or the limitation of the result.
- [ ] T031B [US2] [DEPENDS ON T026, T016C, T007] Implement internal stability analysis (re-sampling) as proxy for literature baseline:
 1. Perform k-fold re-sampling of the training data to generate stability rankings for permutation importance.
 2. Calculate Spearman correlation between the primary model's importance ranking and the mean stability ranking.
 3. **Output**: Append `permutation_importance_correlation_stability` to `results/metrics.json`. **Note**: This is strictly a fallback if T031A fails to find a valid external baseline. The output artifact must explicitly state that this is an internal proxy and not an external validation per SC-004.
- [ ] T031C [P] [US2] [DEPENDS ON T005] Create `contracts/baseline.schema.yaml`. **Action**: Define the schema for user-provided/literature baseline importance rankings. Must require keys `feature_name` (string) and `importance_rank` (integer). This ensures T031A has a deterministic validation contract.
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

- [X] T035 [US3] [DEPENDS ON T016C, T026] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/viz/contour_plots.py` to generate contour plots of predicted Yield Strength vs. Laser Power and Scan Speed. **Action**: Load `data/processed/normalization_bounds.json` to convert normalized axes back to physical units and annotate plot titles/labels accordingly.
- [X] T036 [US3] [DEPENDS ON T016C, T026] Extend `contour_plots.py` to generate uncertainty heatmaps where σ > 2× median is colored red. **Action**: Load `data/processed/normalization_bounds.json` to annotate axes with physical units.
- [X] T037 [US3] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/viz/importance.py` to generate Partial Dependence Plots (PDPs) for the top influential parameters (as identified by permutation importance).
- [X] T039 [US3] Calculate percentage of test samples in "high uncertainty" regions and save to `results/metrics.json` with key `high_uncertainty_percentage` (SC‑003). **Logic**: `high_uncertainty_percentage = (count(σ > 2*median) / total_test_samples) * 100`.
- [X] T040 [US3] [DEPENDS ON results/metrics.json, data/processed/train.csv, data/processed/test.csv, results/contour_plots/, results/uncertainty_heatmaps/] Implement runtime instrumentation in `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py`:
 1. Measure total pipeline time (preprocessing → training → viz) using `time.time()`.
 2. Always write `total_runtime_seconds` to `results/metrics.json`.
 3. **Dynamic Limit Detection**: Check `os.environ.get('GITHUB_ACTIONS')`.
 - If `GITHUB_ACTIONS` is set (CI environment): Compare against `config.TIME_LIMIT_SECONDS` (default a standard duration of several hours).
   - If runtime < limit: Set `feasibility_status: "PASSED"`.
   - If runtime >= limit: **log** warning, set `feasibility_status: "FAILED"`, and **do not abort**.
 - If `GITHUB_ACTIONS` is NOT set: Log warning if runtime exceeds a predefined threshold. but do not set `feasibility_status` to FAILED.
 4. **Note**: This task is primarily for CI environments; local runs use the default limit as a guideline. The limit value must be sourced from `config.py`.
- [ ] T042A [US1] [DEPENDS ON data/processed/train.csv, data/processed/test.csv, data/processed/excluded_columns.yaml] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_us1.py` to orchestrate ONLY User Story 1 (download -> preprocess -> validate). CLI: `--input <raw.csv>` `--output <processed.csv>`. Validate file extensions, enforce `PYTHONHASHSEED=0`. **Note**: Optional orchestration helper for independent US1 testing.
- [ ] T042B [US2] [DEPENDS ON data/processed/train.csv, data/processed/test.csv, models/gpr_model.pkl, results/metrics.json, T029A, T029B, T031A, T031B] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_us2.py` to orchestrate ONLY User Story 2 (preprocess -> train -> eval). CLI: `--input <processed.csv>` `--output <results.json>`. Validate extensions, enforce reproducibility seed. **Note**: This task depends on the `results/metrics.json` artifact to ensure all metrics are ready for the orchestration flow. **Crucial**: This task must run AFTER T029A, T029B, T031A, and T031B have completed to ensure `results/metrics.json` contains the full set of appended metrics (baseline comparison, correlation analysis). **Note**: Optional orchestration helper for independent US2 testing.
- [X] T043 [US3] [DEPENDS ON results/metrics.json, results/contour_plots/, results/uncertainty_heatmaps/, results/confounder_analysis.json] Implement `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main_e2e.py` to orchestrate the full pipeline (download -> preprocess -> train -> viz -> report). CLI: `--input <raw.csv>` `--output-dir <out_dir>`. Enforce `PYTHONHASHSEED=0`.
- [X] T044 [US3] [DEPENDS ON T030, T040] Generate `docs/paper.md` compiling metrics, plots, and explicit data provenance acknowledgment (Draft version). This task consumes the scope‑reduction log entry from T016A if applicable, references the baseline importance source used in T031A/B, and includes the confounder analysis from `results/confounder_analysis.json` (T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045A [P] Create/update `README.md` with installation steps, dependencies, and **manual data placement instructions**. **Action**: Explicitly state that the system requires manual data placement if automated download fails. Provide instructions: "Manual Data Placement: Download a valid AM alloy dataset and save it as `data/raw/am_raw_data.csv`."
- [ ] T045B [P] Finalize `docs/paper.md` with final metrics, plots, and data provenance acknowledgment (Final version).
- [X] T046 [P] Run `flake8` on all `code/` files. **Tool**: `flake8`. **Config**: `.flake8` (create if missing). **Flags**: `--ignore=E501,W605 --max-line-length=100`. **Output**: Save report to `results/linting_report.txt`. **Action**: Fix all errors except unused imports.
- [ ] T047A [P] Profile memory usage. **Action**:
 1. **Dependency**: Ensure `memory_profiler` is installed (add to `requirements.txt`).
 2. Profile memory usage in `preprocess.py` using `memory_profiler`. **Command**: `python -m memory_profiler code/data/preprocess.py`. Use the `@profile` decorator on the main function.
 3. Log `max_memory_mb` to `results/memory_profile.log`.
 4. **Output**: Write `results/memory_profile.json` with `max_memory_mb` and `status: "OK"` or `"WARNING"`.
- [ ] T047B [P] Optimize memory usage if necessary. **Action**:
 1. **Dependency**: T047A must be complete.
 2. Read `results/memory_profile.json`. If `max_memory_mb >= 7000`:
 - Convert numeric columns to `dtype='float32'`.
 - Use chunked reading for large CSVs.
 - Drop unused columns immediately.
 - Log memory savings achieved.
 3. **Verification**: Re‑run profile to verify optimized usage < 7000 MB. Log final result.
 4. **HALT CONDITION**: If optimization fails to bring memory below 7000 MB, **HALT execution** with a recommendation to use Sparse GPR (FITC/VFE) as per Plan Risk Register.
- [X] T051 [P] Unit test for manual data placement validation in T014A in `tests/unit/test_download.py`. **Logic**: This test validates that the error message is correct AND that a `SystemExit` (or equivalent exception) is raised when `data/raw/am_raw_data.csv` is missing and download fails.
- [X] T052 [P] Unit test for 'baseline required' behavior in T031A/T031B when no baseline is found in `tests/unit/test_importance.py`. **Logic**: The test should verify that a `ValueError` is NOT raised if config citation is missing AND no user file is found, ensuring the pipeline continues with null correlation or stability proxy.

---

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
- T015C is explicitly NOT parallel (depends on T016A)

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
- Removed Tasks: T004 (merged into T005), T008 (duplicate), T014C (removed - Manual Fallback only), T017A/B (merged into T016), T018 (merged into T016 and removed from list), T019 (removed and integrated into T016C), T020 (merged into T016A), T021 (merged into T016A), T028A/B/C (no spec), T038 (merged into T035/T036), T041 (duplicate), T048 (conditional/removed), T049 (no spec), T050 (no spec).
- Merged Tasks: T047A/B/C merged into T047A/T047B (Split for atomicity).
- **Revision Note**: Added T042A and T042B to address the requirement for independent User Story testing and orchestration, ensuring each story can be validated in isolation as per the specification's independent test criteria.
- **Revision Note**: Removed T014C (Automated Download) to align with Plan's Manual Fallback Protocol.
- **Revision Note**: Updated T015B to enforce HALT on missing `source_independence_log.txt` and validate content.
- **Revision Note**: Added T031C for baseline schema validation.
- **Revision Note**: Fixed T001C [P] tag removal due to dependencies.
- **Revision Note**: Activated T047A/B for memory profiling and mitigation.