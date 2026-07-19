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
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001A [P] Create directory structure: `projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/`, `data/`, `data/raw/`, `data/processed/`, `tests/`, `tests/unit/`, `tests/integration/`, `results/`, `docs/`, `state/`
- [ ] T001B [P] Create Python package initialization files: `code/__init__.py`, `code/data/__init__.py`, `code/models/__init__.py`, `code/viz/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [ ] T001C [P] Create configuration and dependency files: `code/requirements.txt` (empty), `code/config.py` (empty), `contracts/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/dataset.schema.yaml` defining required columns: `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`. Define `fatigue_life` as OPTIONAL.
- [ ] T005 [P] Implement `code/data/schema_validator.py` to validate CSV against `contracts/dataset.schema.yaml`
- [X] T006 Setup `code/config.py` to manage paths (`data/raw/`, `data/processed/`, `results/`) and random seeds (fixed)
- [X] T007 Create `code/__init__.py` and empty `tests/` directory structure (Note: T001E covers subdirs, T007 ensures root)
- [X] T008 Configure error handling and logging infrastructure in `code/config.py` and `code/utils/logger.py`
- [X] T009 Create `code/config.py` keys for manual data placement paths (e.g., `MANUAL_DATA_PATHS`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: A researcher uploads or downloads a raw public AM alloy dataset and receives a clean, normalized CSV ready for modeling, with missing values handled and categorical variables encoded.

**Independent Test**: Can be fully tested by running the preprocessing script on a known raw dataset file and verifying the output CSV contains normalized numeric columns, one-hot encoded alloy types, and no missing values, with a log file confirming the imputation and normalization steps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for median imputation logic in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Unit test for one-hot encoding of `alloy_type` in `tests/unit/test_preprocess.py`
- [X] T012 [P] [US1] Integration test for full pipeline from raw CSV to processed CSV in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013A [US1] Implement `code/data/download.py` to attempt automated download from verified sources:
 1. Zenodo (ID: - AM-Machine-Learning)
 2. UCI Machine Learning Repository (Dataset: 'Alloy Properties' or similar)
 3. HuggingFace Datasets (Dataset: 'materials-project' or similar)
 Implement retry logic with exponential backoff (limited to a predefined maximum number of attempts) for network failures. If all sources fail or schema mismatch occurs after retries, exit with a non-zero error code. and log specific manual placement instructions to `data/processed/preprocessing.log` (e.g., "Manual download required: place 'am_data.csv' in 'data/raw/'"). DO NOT fallback to synthetic data.
- [ ] T013C [US1] [DEPENDS ON T013A] If automated download fails (exit code 2), the system MUST halt. The user MUST manually place 'am_data.csv' in 'data/raw/'. Re-run the pipeline. If file still missing, raise FileNotFoundError.
- [ ] T016B [US1] [DEPENDS ON T013A, T013C] Implement 'Source Independence & Tautology Check' as a standalone validation step in `code/data/validate_source_independence.py`. This script MUST run on the raw file (whether from T013A or manual T013C) BEFORE preprocessing. It must verify predictors (process params) and targets (mechanical props) originate from distinct streams by checking for derived feature names: 'energy_density', 'line_energy', 'volume_energy', 'energy_per_unit_length', 'heat_input'. If any derived feature is found, log a WARNING and halt execution with error: "Tautology detected: derived features found. Ensure input data contains only raw process parameters."
- [X] T014 [US1] Implement `code/data/preprocess.py` to load raw CSV (from TA or manual), validate schema, and handle missing values via median imputation
- [ ] T015A [US1] Implement one-hot encoding for `alloy_type` in `code/data/preprocess.py` and drop original column
- [ ] T015B [US1] [DEPENDS ON T004] Implement dynamic scope reduction: if `fatigue_life` is missing, restrict analysis to `yield_strength` and `ductility`, log the scope reduction. **Additionally**, prepare the scope reduction note text and save it to a persistent state file `data/processed/scope_reduction_note.txt`. The file MUST contain a JSON object: `{"missing_fields": ["fatigue_life"], "active_fields": ["yield_strength", "ductility"], "timestamp": "..."}`. This replaces the logic previously in T015C to avoid forward-referencing issues.
- [X] T016 [US1] Implement train-test split (majority-minority) and MinMaxScaler **fit only on training set** in `code/data/preprocess.py`
- [ ] T017 [US1] Save `normalization_bounds.json` (train set min/max) to `data/processed/` for physical regime mapping
- [X] T018 [US1] Implement zero-variance detection and column dropping in `code/data/preprocess.py`. For every zero-variance column detected, write a WARNING level log entry to `data/processed/preprocessing.log` with the specific column name and reason (e.g., "WARNING: Column 'layer_thickness' has zero variance; dropping to prevent singularity").
- [X] T019 [US1] Implement sample count check (N < 50) to halt execution with specific error message in `code/data/preprocess.py`
- [X] T020 [US1] Write log entries for imputation counts, dropped columns, and normalization stats to `data/processed/preprocessing.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gaussian Process Regression Model Training and Validation (Priority: P2)

**Goal**: A researcher trains a Gaussian Process Regression model to predict mechanical properties from processing parameters and receives performance metrics (R², RMSE) documenting the model's predictive capability.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed data, verifying the model object is saved, and checking a results JSON file for R² and RMSE values that are reported (without arbitrary pass/fail thresholds).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for GPR hyperparameter optimization in `tests/unit/test_gpr.py`
- [X] T022 [P] [US2] Integration test for model training and metric calculation in `tests/integration/test_pipeline.py`
 *Note: T022 MUST include a test case that simulates both literature fetch failure and missing user-baseline file to verify T030 halts correctly.*

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement `code/models/baseline_trainer.py` to train Linear Regression on the same training set for SC-001 comparison
- [X] T024 [US2] Implement `code/models/gpr_trainer.py` to train GPR with RBF kernel using k-fold cross-validation to maximize log marginal likelihood
- [X] T025 [US2] Implement `code/models/metrics.py` to calculate R², RMSE, and MAE on the held-out test set
- [ ] T026A [US2] [NEW] Implement 'Synthetic Data Validation (Power Analysis Proxy)' in `code/models/synthetic_validation.py`. Generate synthetic non-linear data (N=50) with known noise levels and a known non-linear relationship (e.g., `y = sin(x) + noise`). Train GPR on this synthetic data and verify if the model can recover the signal. **Success Metric**: The model must achieve an R² score > 0.5 on the synthetic test set. If R² <= 0.5, flag high uncertainty in the final report. This validates the GPR's ability to work at N=50.
- [ ] T027A [US2] Save raw metrics (GPR R², RMSE, MAE; Baseline R², RMSE, MAE) to `results/metrics.json`
- [ ] T027B [US2] [DEPENDS ON T027A] Perform comparative analysis: Calculate delta R² (GPR - Baseline) and percentage improvement. Save comparative results to `results/metrics.json` with key `gpr_vs_baseline_delta`. This satisfies SC-001 by explicitly measuring GPR against the baseline.
- [ ] T026 [US2] Save trained GPR model artifact and Linear Regression baseline to `results/models/` (NOT data/processed/)
- [X] T029 [US2] [P] [DEPENDS ON T014, T015A] Implement stratified analysis by `alloy_type` in `code/models/stratified_analysis.py` to assess confounder sensitivity (Plan Task 2.4). This task consumes the processed CSV from T014/T015 and performs grouping/analysis WITHOUT requiring the GPR model (T024). Mark as parallel to T024.
- [ ] T030 [US2] [DEPENDS ON T024, T016] Implement permutation importance correlation analysis: <!-- FAILED: unspecified -->
 1. Calculate permutation importance on the trained GPR model.
 2. Attempt to fetch literature baseline from DOI '10.1016/j.addma.2020.101632' using the `crossref` API.
 3. **FALLBACK LOGIC**: If the fetch fails, check for a user-provided JSON file at `data/baseline_importance.json`. The expected JSON schema is: `{"parameters": [{"name": "string", "rank": int},...]}`.
 4. If BOTH fetch and user file fail, HALT execution with error: "SC-004 requires a verified literature baseline. Fetch failed and no user baseline provided."
 5. If either source is found, calculate the correlation between model rankings and baseline rankings. Save results to `results/metrics.json`.
 **NOTE**: This task implements the 'OR' logic required by SC-004. Verification: The integration test (T022) must verify that the system halts ONLY when both sources are missing.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Uncertainty Quantification and Visualization (Priority: P3)

**Goal**: A researcher views contour plots of predicted mechanical properties overlaid with uncertainty heatmaps to identify parameter regimes with high prediction confidence versus those requiring further experimentation.

**Independent Test**: Can be fully tested by running the visualization script, confirming PNG files are generated, and verifying that regions with high predicted standard deviation (σ) are correctly highlighted in red on the uncertainty heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for uncertainty threshold calculation (multiplier of median) in `tests/unit/test_viz.py`
- [X] T033 [P] [US3] Integration test for contour and heatmap generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement `code/viz/contour_plots.py` to generate contour plots of predicted Yield Strength vs. Laser Power and Scan Speed
- [X] T035 [US3] Implement `code/viz/contour_plots.py` to generate uncertainty heatmaps where σ > 2× median is colored red
- [X] T036 [US3] Implement `code/viz/importance.py` to generate Partial Dependence Plots (PDPs) for top 3 influential parameters
- [ ] T037 [US3] [DEPENDS ON T017, T034, T035] Integrate `normalization_bounds.json` into visualizations (T034/T035 outputs) to annotate axes with physical units (W, mm/s, etc.)
- [ ] T038 [US3] Calculate percentage of test samples in "high uncertainty" regions and save to `results/metrics.json` with key `high_uncertainty_percentage` (SC-003). **Assessment Logic**: Compare this percentage against a threshold (e.g., 20%). If > 20%, log a WARNING: "High uncertainty region coverage > 20%: Model may be unreliable in significant portions of parameter space." This satisfies the "assess model ability" requirement.
- [ ] T039 [US3] Implement runtime instrumentation in `code/main.py` to measure total pipeline time and save to `results/metrics.json` (SC-005). **Threshold**: Define `TIME_LIMIT_SECONDS = 21600` (6 hours) in `code/config.py`. Assert that `total_runtime_seconds < TIME_LIMIT_SECONDS`. If exceeded, raise an error or log a CRITICAL warning: "Runtime exceeds 6-hour CI limit."
- [ ] T048 [US3] [DEPENDS ON T039] Explicitly log the result of the runtime measurement against the limit. If `total_runtime_seconds < TIME_LIMIT_SECONDS` (where `TIME_LIMIT_SECONDS = 21600`), log "PASS: Runtime within 6-hour limit". Else, log "FAIL: Runtime exceeds limit". This ensures the "measurement against a limit" part of SC-005 is explicitly implemented and verifiable.
- [ ] T040A [US1] [P] [DEPENDS ON T013A, T013C, T014, T015A, T016] Implement `code/main_us1.py` to orchestrate ONLY User Story 1 (download -> preprocess -> validate). **This is the primary execution path for Independent Testing of US1.**
- [ ] T040B [US2] [P] [DEPENDS ON T014, T016, T024, T025] Implement `code/main_us2.py` to orchestrate ONLY User Story 2 (preprocess -> train -> eval). **This is the primary execution path for Independent Testing of US2.**
- [ ] T040C [US3] [P] [DEPENDS ON T040A, T040B, T034, T035, T030] Implement `code/main_e2e.py` to orchestrate the full pipeline (download -> preprocess -> train -> viz -> report). **This is strictly for End-to-End Integration testing, not the primary path for individual story validation.**
- [ ] T041 [US3] Generate `docs/paper.md` compiling metrics, plots, and explicit data provenance acknowledgment (Draft version). **Note**: This task consumes the `data/processed/scope_reduction_note.txt` prepared by T015B if applicable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042A [P] Create/update `README.md` with installation steps, dependencies, and manual data placement instructions
- [ ] T042B [P] Finalize `docs/paper.md` with final metrics, plots, and data provenance acknowledgment (Final version)
- [ ] T043A [P] Run `flake8` or `pylint` on all `code/` files and generate linting report
- [ ] T043B [P] Fix linting errors identified in T043A
- [ ] T043C [P] Remove unused imports and variables identified by linter
- [ ] T044A [P] Optimize memory usage in `preprocess.py` to ensure < 7GB peak usage on N=500 samples. **Method**: Use `memory_profiler` to decorate the main pipeline function. Assert that `max_memory_mb` recorded in the log is < 7000. If not, optimize using chunked processing or dtype conversion.
- [ ] T044B [P] Optimize GPR training loop in `gpr_trainer.py` to ensure runtime < 30 minutes
- [ ] T045 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T046 Security hardening (input validation)
- [ ] T047 Run quickstart.md validation

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
- Models within a story marked [P] can run in parallel **ONLY AFTER T014/T015 (data pipeline) are complete**
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for median imputation logic in tests/unit/test_preprocess.py"
Task: "Unit test for one-hot encoding of alloy_type in tests/unit/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to check for data/raw/am_data.csv"
Task: "Implement code/data/preprocess.py to load raw CSV and handle missing values"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
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