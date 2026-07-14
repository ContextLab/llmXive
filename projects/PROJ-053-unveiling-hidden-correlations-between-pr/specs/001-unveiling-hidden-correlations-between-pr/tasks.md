# Tasks: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Input**: Design documents from `/specs/001-unveiling-hidden-correlations/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001A Create project directory tree structure per implementation plan in `projects/PROJ-053-unveiling-hidden-correlations-between-pr/` (code/, data/, tests/, docs/, state/)
- [ ] T001B Create `__init__.py` files in all `code/` subdirectories and `tests/` directories
- [ ] T001C Create empty `code/requirements.txt` and `code/config.py` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/dataset.schema.yaml` defining required columns: `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`, `alloy_type`
- [ ] T005 [P] Implement `code/data/schema_validator.py` to validate CSV against `contracts/dataset.schema.yaml`
- [ ] T006 Setup `code/config.py` to manage paths (`data/raw/`, `data/processed/`, `results/`) and random seeds (42)
- [ ] T007 Create `code/__init__.py` and empty `tests/` directory structure (Note: T001B covers code/ subdirs, T007 ensures root)
- [ ] T008 Configure error handling and logging infrastructure in `code/config.py` and `code/utils/logger.py`
- [ ] T009 Create `code/config.py` keys for manual data placement paths (e.g., `MANUAL_DATA_PATHS`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: A researcher uploads or downloads a raw public AM alloy dataset and receives a clean, normalized CSV ready for modeling, with missing values handled and categorical variables encoded.

**Independent Test**: Can be fully tested by running the preprocessing script on a known raw dataset file and verifying the output CSV contains normalized numeric columns, one-hot encoded alloy types, and no missing values, with a log file confirming the imputation and normalization steps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for median imputation logic in `tests/unit/test_preprocess.py`
- [ ] T011 [P] [US1] Unit test for one-hot encoding of `alloy_type` in `tests/unit/test_preprocess.py`
- [ ] T012 [P] [US1] Integration test for full pipeline from raw CSV to processed CSV in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013A [US1] Implement check in `code/data/download.py` to verify `data/raw/am_data.csv` exists; log specific manual placement instructions from plan.md to error log BEFORE raising FileNotFoundError if missing
- [ ] T013B [US1] Implement `code/data/download.py` logic for 'Source Independence & Tautology Check': verify predictors (process params) and targets (mechanical props) originate from distinct data streams and exclude derived features (e.g., energy_density)
- [ ] T014 [US1] Implement `code/data/preprocess.py` to load raw CSV, validate schema, and handle missing values via median imputation
- [ ] T015 [US1] Implement one-hot encoding for `alloy_type` in `code/data/preprocess.py` and drop original column
- [ ] T016 [US1] Implement train-test split (majority-minority) and MinMaxScaler **fit only on training set** in `code/data/preprocess.py`
- [ ] T017 [US1] Save `normalization_bounds.json` (train set min/max) to `data/processed/` for physical regime mapping
- [ ] T018 [US1] Implement zero-variance detection and column dropping in `code/data/preprocess.py`
- [ ] T019 [US1] Implement sample count check (N < 50) to halt execution with specific error message in `code/data/preprocess.py`
- [ ] T020 [US1] Write log entries for imputation counts, dropped columns, and normalization stats to `data/processed/preprocessing.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gaussian Process Regression Model Training and Validation (Priority: P2)

**Goal**: A researcher trains a Gaussian Process Regression model to predict mechanical properties from processing parameters and receives performance metrics (R², RMSE) documenting the model's predictive capability.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed data, verifying the model object is saved, and checking a results JSON file for R² and RMSE values that are reported (without arbitrary pass/fail thresholds).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for GPR hyperparameter optimization in `tests/unit/test_gpr.py`
- [ ] T022 [P] [US2] Integration test for model training and metric calculation in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `code/models/baseline_trainer.py` to train Linear Regression on the same training set for SC-001 comparison
- [ ] T024 [US2] Implement `code/models/gpr_trainer.py` to train GPR with RBF kernel using k-fold cross-validation to maximize log marginal likelihood
- [ ] T025 [US2] Implement `code/models/metrics.py` to calculate R², RMSE, and MAE on the held-out test set
- [ ] T026 [US2] Save trained GPR model artifact and Linear Regression baseline to `data/processed/`
- [ ] T027 [US2] Save metrics (GPR vs Baseline) to `results/metrics.json` including standard R²/RMSE/MAE AND `rmse_as_percentage_of_range` (SC-002)
- [ ] T028 [US2] Implement `code/models/gpr_trainer.py` logic to detect and handle zero-variance features if not already caught in preprocessing
- [ ] T029 [US2] [DEPENDS ON T015] Implement stratified analysis by `alloy_type` in `code/models/gpr_trainer.py` to assess confounder sensitivity (Plan Task 2.4)
- [ ] T030 [US2] [DEPENDS ON T024] Implement permutation importance correlation analysis: load user-provided or literature baseline from configurable path (default: `data/baseline_importance.json`), calculate correlation with model rankings, and save results to `results/baseline_correlation.json` (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Uncertainty Quantification and Visualization (Priority: P3)

**Goal**: A researcher views contour plots of predicted mechanical properties overlaid with uncertainty heatmaps to identify parameter regimes with high prediction confidence versus those requiring further experimentation.

**Independent Test**: Can be fully tested by running the visualization script, confirming PNG files are generated, and verifying that regions with high predicted standard deviation (σ) are correctly highlighted in red on the uncertainty heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for uncertainty threshold calculation (2× median) in `tests/unit/test_viz.py`
- [ ] T033 [P] [US3] Integration test for contour and heatmap generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/viz/contour_plots.py` to generate contour plots of predicted Yield Strength vs. Laser Power and Scan Speed
- [ ] T035 [US3] Implement `code/viz/contour_plots.py` to generate uncertainty heatmaps where σ > 2× median is colored red
- [ ] T036 [US3] Implement `code/viz/importance.py` to generate Partial Dependence Plots (PDPs) for top 3 influential parameters
- [ ] T037 [US3] [DEPENDS ON T017] Integrate `normalization_bounds.json` into visualizations to annotate axes with physical units (W, mm/s, etc.)
- [ ] T038 [US3] Calculate percentage of test samples in "high uncertainty" regions and save to `results/metrics.json` with key `high_uncertainty_percentage` (SC-003)
- [ ] T039 [US3] Implement runtime instrumentation in `code/main.py` to measure total pipeline time and save to `results/metrics.json` (SC-005)
- [ ] T040 [US3] Implement `code/main.py` to orchestrate the full pipeline: invoke scripts from T013-T039 in sequence (download -> preprocess -> train -> viz -> report)
- [ ] T041 [US3] Generate `docs/paper.md` compiling metrics, plots, and explicit data provenance acknowledgment (Draft version)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042A [P] Update `README.md` with installation steps, dependencies, and manual data placement instructions
- [ ] T042B [P] Finalize `docs/paper.md` with final metrics, plots, and data provenance acknowledgment (Final version)
- [ ] T043 Code cleanup and refactoring
- [ ] T044 Performance optimization across all stories
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