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
- [ ] T001C [P] Create Python package initialization files: `code/__init__.py`, `code/data/__init__.py`, `code/models/__init__.py`, `code/viz/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [ ] T001D [P] Create configuration and dependency files: `code/requirements.txt` (empty), `code/config.py` (empty), `contracts/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `contracts/dataset.schema.yaml` file. This task includes defining the required columns (`laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`) as required, `fatigue_life` as optional, and writing the complete YAML content to the file. The schema must follow this structure:
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
- [ ] T006 [P] Implement `code/data/schema_validator.py` to validate CSV against `contracts/dataset.schema.yaml`. **Logic**: Load the YAML schema, read the CSV, and verify all required columns exist and contain numeric data. Raise a `ValueError` if validation fails.
- [X] T007 Setup `code/config.py` to manage paths (`data/raw/`, `data/processed/`, `results/`) and random seeds (fixed)
- [X] T009 Configure error handling and logging infrastructure in `code/config.py` and `code/utils/logger.py`
- [X] T010 Create `code/config.py` keys for manual data placement paths (e.g., `MANUAL_DATA_PATHS`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. T005 and T006 must be completed before T016 starts.

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

- [ ] T014A [US1] Implement `code/data/download.py` to check for `data/raw/am_data.csv`. **Constraint**: NO automated download logic. **Logic**: Check if `data/raw/am_data.csv` exists. If missing, log a CRITICAL error: "Manual data placement required: `data/raw/am_data.csv` not found. Please place the dataset file manually." and raise an exception to halt execution. DO NOT attempt Zenodo, HuggingFace, or UCI downloads. This strictly adheres to the Plan's 'no automated download' constraint.
- [ ] T015B [US1] [DEPENDS ON T014A, T005, T006] Implement 'Source Independence & Tautology Check' as a standalone validation step in `code/data/validate_source_independence.py`. **DEPENDENCY CHECK**: This script MUST check if `data/raw/am_data.csv` exists (validated by T014A). **Logic**: If the file exists, verify predictors (process params) and targets (mechanical props) originate from distinct streams by checking for derived feature names defined in `code/config.py` or hardcoded: `['energy_density', 'line_energy', 'volume_energy', 'energy_per_unit_length', 'heat_input']`. **Action**: If any derived feature is found, log a WARNING. **Edge Case Handling**: If ALL available predictor columns are found in the excluded list, log a CRITICAL WARNING stating "All predictors are derived features; proceeding with caution as per 'Dataset-variable fit' assumption, but model validity may be compromised." and allow execution to continue with an empty exclusion list. **Output**: Write the list of excluded columns to `data/processed/excluded_columns.yaml` in the format: `excluded_columns: [col1, col2]`. If no columns are excluded, write `excluded_columns: []`. This file is consumed by T016.
- [ ] T016 [US1] [DEPENDS ON T014A, T015B, T005, T006] Implement `code/data/preprocess.py` to load raw CSV (at path validated by T014A), validate schema (T005/T006), and handle missing values via median imputation. **DEPENDENCY**: This task MUST read `data/processed/excluded_columns.yaml` (from T015B) and filter those columns from the dataset before processing. **Scope Reduction**: As Step 1 of this task, check if `fatigue_life` is present in the raw file headers. If missing, log a specific entry to `data/processed/preprocessing.log` with the format: `[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility.` Do NOT generate a JSON artifact for this. **Action**: Perform one-hot encoding for `alloy_type`, drop original column, split train/test, and apply MinMaxScaler **fit only on training set**.
- [ ] T019 [US1] Save `normalization_bounds.json` (train set min/max) to `data/processed/` for physical regime mapping. **Structure**: The JSON must contain: `{"laser_power": {"min": float, "max": float}, "scan_speed": {"min": float, "max": float}, ...}` for all numeric features. This file is required for T038 and T043.
- [X] T020 [US1] Implement zero-variance detection and column dropping in `code/data/preprocess.py`. For every zero-variance column detected, write a WARNING level log entry to `data/processed/preprocessing.log` with the specific column name and reason (e.g., "WARNING: Column 'layer_thickness' has zero variance; dropping to prevent singularity").
- [X] T021 [US1] Implement sample count check (N < 50) to halt execution with specific error message in `code/data/preprocess.py`
- [X] T022 [US1] Write log entries for imputation counts, dropped columns, and normalization stats to `data/processed/preprocessing.log`

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

- [X] T025 [P] [US2] Implement `code/models/baseline_trainer.py` to train Linear Regression on the same training set for SC-001 comparison
- [X] T026 [US2] Implement `code/models/gpr_trainer.py` to train GPR with RBF kernel using k-fold cross-validation to maximize log marginal likelihood
- [X] T027 [US2] Implement `code/models/metrics.py` to calculate R², RMSE, and MAE on the held-out test set
- [ ] T029A [US2] [DEPENDS ON T026, T027] Save raw metrics (GPR R², RMSE, MAE; Baseline R², RMSE, MAE) to `results/metrics.json`. **Include**: `rmse_percentage_of_range` (RMSE / (max_target - min_target) * 100) as required by SC-002. **CRITICAL**: The denominator (max_target - min_target) MUST be calculated strictly from the test subset data object passed from T027, ensuring no leakage from the full dataset.
- [ ] T029B [US2] [DEPENDS ON T029A] Perform comparative analysis: Calculate delta R² (GPR - Baseline) and percentage improvement. Save comparative results to `results/metrics.json` with key `gpr_vs_baseline_delta`. This satisfies SC-001 by explicitly measuring GPR against the baseline.
- [X] T030 [US2] [DEPENDS ON T016] Implement stratified analysis by `alloy_type` in `code/models/stratified_analysis.py` to assess confounder sensitivity (Plan Task 2.4). This task consumes the processed CSV from T016 and performs grouping/analysis WITHOUT requiring the GPR model (T026). Mark as parallel to T026 (after T016 completes). **Note**: Write output to `data/processed/stratified_analysis.log` to avoid shared state conflicts with T026.
- [ ] T031 [US2] [DEPENDS ON T026, T016, T029A] Implement permutation importance correlation analysis:
 1. Calculate permutation importance on the trained GPR model.
 2. **Baseline Requirement**: Attempt to load `data/baseline_importance.json`. If found, use this.
 3. **Failure Condition**: If no user-provided baseline is found, raise `FileNotFoundError` with message "No verified baseline found for permutation importance correlation (SC-004). Provide user-baseline or literature-cited baseline." **DO NOT** use a hardcoded fallback.
 4. Calculate the correlation between model rankings and baseline rankings. **Append** results to `results/metrics.json` (do not overwrite). **Constraint**: If the baseline is missing, the task fails immediately and NO results are appended.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Uncertainty Quantification and Visualization (Priority: P3)

**Goal**: A researcher views contour plots of predicted mechanical properties overlaid with uncertainty heatmaps to identify parameter regimes with high prediction confidence versus those requiring further experimentation.

**Independent Test**: Can be fully tested by running the visualization script, confirming PNG files are generated, and verifying that regions with high predicted standard deviation (σ) are correctly highlighted in red on the uncertainty heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for uncertainty threshold calculation (multiplier of median) in `tests/unit/test_viz.py`
- [X] T034 [P] [US3] Integration test for contour and heatmap generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T035 [US3] Implement `code/viz/contour_plots.py` to generate contour plots of predicted Yield Strength vs. Laser Power and Scan Speed
- [X] T036 [US3] Implement `code/viz/contour_plots.py` to generate uncertainty heatmaps where σ > 2× median is colored red
- [X] T037 [US3] Implement `code/viz/importance.py` to generate Partial Dependence Plots (PDPs) for top 3 influential parameters
- [ ] T038 [US3] [DEPENDS ON T019, T035, T036] Integrate `normalization_bounds.json` into visualizations (T035/T036 outputs) to annotate axes with physical units (W, mm/s, etc.). **Logic**: Load `normalization_bounds.json` and map the normalized axes back to physical units for the plot labels and titles.
- [X] T039 [US3] Calculate percentage of test samples in "high uncertainty" regions and save to `results/metrics.json` with key `high_uncertainty_percentage` (SC-003). **Assessment Logic**: Explicitly calculate the percentage of samples where σ > 2× median (as defined in FR-007). Log the percentage. Do NOT apply a hardcoded threshold or pass/fail condition for the *measurement*, but the *identification* of regions MUST use the 2× median rule.
- [X] T040 [US3] Implement runtime instrumentation in `code/main.py` to measure total pipeline time and **ALWAYS** save `total_runtime_seconds` to `results/metrics.json` regardless of the outcome.
 **CRITICAL**:
 1. Define `TIME_LIMIT_SECONDS = 21600` (6 hours) in `code/config.py`.
 2. Log `total_runtime_seconds` to `results/metrics.json` unconditionally.
 3. Compare `total_runtime_seconds` against `TIME_LIMIT_SECONDS`.
 4. If `total_runtime_seconds > TIME_LIMIT_SECONDS`:
    a. **Write Failure Status**: Update `results/metrics.json` to include `{"feasibility_status": "FAILED", "runtime_seconds": total_runtime_seconds}`.
    b. **Raise Exception**: Raise `SystemExit(1)` with message "Runtime exceeds 6-hour CI limit; feasibility check failed."
 5. Ensure the artifact `results/metrics.json` is written with the failure status BEFORE raising the exception.
- [ ] T042A [US1] [DEPENDS ON T014A, T016, T015B] Implement `code/main_us1.py` to orchestrate ONLY User Story 1 (download -> preprocess -> validate). **This is the primary execution path for Independent Testing of US1.** Note: T042A depends on T015B to ensure scope configuration is ready. **CLI**: Accept `--input` (path to raw CSV) and `--output` (path to processed CSV). **Env**: `PYTHONHASHSEED=0` for reproducibility.
- [ ] T042B [US2] [DEPENDS ON T016, T026, T027] Implement `code/main_us2.py` to orchestrate ONLY User Story 2 (preprocess -> train -> eval). **This is the primary execution path for Independent Testing of US2.** **CLI**: Accept `--input` (path to processed CSV) and `--output` (path to results JSON). **Env**: `PYTHONHASHSEED=0`.
- [X] T043 [US3] [DEPENDS ON T014A, T016, T026, T029A, T029B, T035, T036] Implement `code/main_e2e.py` to orchestrate the full pipeline (download -> preprocess -> train -> viz -> report). **This is strictly for End-to-End Integration testing, not the primary path for individual story validation.** Note: T043 orchestrates T031 as an internal step after T029A/B; T031 is NOT a prerequisite dependency for T043 to start. **CLI**: Accept `--input` (path to raw CSV) and `--output-dir` (path to output directory). **Env**: `PYTHONHASHSEED=0`.
- [ ] T044 [US3] Generate `docs/paper.md` compiling metrics, plots, and explicit data provenance acknowledgment (Draft version). **Note**: This task consumes the scope reduction log entry from T016 if applicable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045A [P] Create/update `README.md` with installation steps, dependencies, and manual data placement instructions
- [ ] T045B [P] Finalize `docs/paper.md` with final metrics, plots, and data provenance acknowledgment (Final version)
- [ ] T046 [P] Run `flake8` on all `code/` files. **Tool**: `flake8`. **Config**: `.flake8` (create if missing). **Flags**: `--ignore=E501,W605 --max-line-length=100`. **Output**: Save report to `results/linting_report.txt`. **Action**: Fix all errors except unused imports.
- [ ] T047A [P] Profile memory usage in `preprocess.py` using `memory_profiler`. Log `max_memory_mb` to `results/memory_profile.log`.
- [ ] T047B [P] Optimize memory usage in `preprocess.py` (chunked processing, dtype conversion) if `max_memory_mb` >= 7000.
- [ ] T047C [P] Verify optimized memory usage is < 7000 MB by re-running T047A.
- [ ] T051 [P] Unit test for manual data placement validation in T014A in `tests/unit/test_download.py`. **Logic**: This test validates that the error message is correct AND that a `SystemExit` (or equivalent exception) is raised when `data/raw/am_data.csv` is missing.
- [ ] T052 [P] Unit test for 'baseline required' behavior in T031 when no baseline is found in `tests/unit/test_importance.py` (Note: T031 now raises FileNotFoundError if baseline is missing, so this test validates the exception raising logic).

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
- Models within a story marked [P] can run in parallel **ONLY AFTER T016 (data pipeline) are complete**
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
- Removed Tasks: T004 (merged into T005), T008 (duplicate), T017A/B (merged into T016), T018 (merged into T016 and removed from list), T028A/B/C (no spec), T041 (duplicate), T048 (conditional/removed), T049 (no spec), T050 (no spec).