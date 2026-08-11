# Tasks: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

**Input**: Design documents from `/specs/001-evaluating-the-predictive-power-of-machi/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY as defined by the Spec's "Independent Test" sections.

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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root directories: `code/`, `data/raw/`, `data/processed/`, `data/models/`, `tests/unit/`, `tests/integration/`, `specs/`
- [ ] T001b [P] Create empty `__init__.py` files in all new directories to initialize Python packages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `code/config.py` with hyperparameters, random seeds (arbitrary), and path constants
- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, scipy, datasets, matplotlib, seaborn, pytest)
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 [P] Implement `code/__init__.py` and package structure
- [ ] T006 [P] Setup `tests/` directory structure (unit, integration)
- [X] T007 [P] Configure basic logging infrastructure in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Novel Composition Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest HEA thermodynamic data from `hmao/all_apis_for_multiapi`, generate `heas_train.csv`, `holdout_known.csv`, and `true_novel.csv` with strict separation and verification. The "Source API" for novelty verification is defined as the static `hmao` proxy dataset per Plan constraints.

**Independent Test**: Verify `heas_train.csv` contains only known entries, `holdout_known.csv` entries exist in source but not training, and `true_novel.csv` entries return "Not Found" against the `hmao` proxy index.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for data filtering logic in `tests/unit/test_ingestion.py` (verify 5+ element filter)
- [X] T011 [P] [US1] Integration test for dataset split logic in `tests/integration/test_split.py` (verify no overlap between train/holdout/novel)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_ingestion.py` to load `hmao/all_apis_for_multiapi` using `datasets.load_dataset(..., streaming=True)`. **Mapping**: `formation_energy_per_atom` -> `target_energy`, `mixing_enthalpy` -> `target_hmix`. Filter for + element systems.
- [ ] T013 [US1] Implement filtering logic in `code/data_ingestion.py` to select 5+ element systems and export to `data/processed/heas_train.csv`
- [ ] T014 [US1] **Sample** 5000 unique 5-element combinations from the periodic table using a fixed random seed (42). Filter for those present in the `hmao` proxy index but NOT in `heas_train.csv`. Export to `data/processed/holdout_known.csv`. **Constraint**: Must use a fixed random seed for reproducibility. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T014a [US1] Implement the sampling logic in `code/data_ingestion.py` to generate exactly 5000 unique 5-element combinations.
- [ ] T015 [US1] **Sample** 5000 unique 5-element combinations from the periodic table using a fixed random seed (42). Filter for those NOT present in `heas_train.csv` AND NOT present in the `hmao` proxy index (simulating a "Not Found" response). Export to `data/processed/true_novel.csv`. **Constraint**: Must use a fixed random seed for reproducibility. <!-- FAILED: unspecified -->
- [X] T016 [US1] Implement streaming integrity check in `code/data_ingestion.py`: Validate the dataset checksum against the known SHA256 hash in `config.py` and implement mock backoff logging (for spec compliance) if the static fetch fails. **Remove** live API retry logic as the source is static.
- [X] T017 [US1] Implement strict composition string comparison check to prevent hash collisions in `code/data_ingestion.py`. **Output**: Produce a `deduplicated composition index` artifact consumed by T018.
- [ ] T018 [US1] Add validation script `code/validate_splits.py` to verify disjoint sets and `hmao` proxy existence for holdout/novel sets.
- [ ] T019a [US1] **Documentation**: Create `docs/api_deviation.md` explicitly documenting the deviation from live "Materials Project/AFLOW API" verification to static `hmao` proxy verification for CI reproducibility, referencing FR-001 and US-1.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

**Goal**: Compute compositional descriptors via `pymatgen` and train Random Forest/Gradient Boosting models with k-fold cross-validation

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold cross-validation

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold cross-validation on CPU.

**Independent Test**: Verify 5-fold CV $R^2$ is calculated, model artifacts (`.pkl`) are generated, and execution completes within 6 hours on CPU without GPU errors.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T019 [P] [US2] Unit test for descriptor calculation in `tests/unit/test_descriptors.py` (verify weighted mean/variance for radius, electronegativity, VEC, melting point)
- [ ] T020 [P] [US2] Unit test for numerical stability in `tests/unit/test_descriptors.py` (verify clamping of near-zero values to $1e-6$)

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/feature_engineering.py` to calculate weighted mean and variance descriptors (atomic radius, electronegativity, VEC, melting point) using `pymatgen` for all datasets
- [ ] T022 [US2] Implement numerical clamping logic (min threshold) in `code/feature_engineering.py` to prevent division errors
- [ ] T023 [US2] Implement `code/train_models.py` to train `RandomForestRegressor` and `GradientBoostingRegressor` with 5-fold cross-validation
- [ ] T024 [US2] Implement hyperparameter tuning (max_depth, n_estimators) within `code/train_models.py`
- [ ] T025 [US2] Implement model saving logic in `code/train_models.py` to output `.pkl` artifacts to `data/models/`
- [ ] T026 [US2] Add logging for training metrics (mean $R^2$) and execution time in `code/train_models.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Extrapolation Evaluation and Uncertainty Analysis (Priority: P3)

**Goal**: Evaluate models on "Hold-out Known" (error) and "True Novel" (uncertainty) sets, perform statistical tests, and generate final report.

**Independent Test**: Compare $R^2$ on holdout vs training, verify ensemble variance correlates with convex hull distance, and generate ranked candidate report.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T027 [P] [US3] Integration test for evaluation pipeline in `tests/integration/test_evaluation.py` (verify t-test and Spearman correlation outputs)

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/evaluate.py` to load trained models and predict on `holdout_known.csv`
- [ ] T029 [US3] Implement $R^2$ and MAE calculation for `holdout_known.csv` in `code/evaluate.py` and compare to training $R^2$
- [ ] T030 [US3] Implement prediction on `true_novel.csv` in `code/evaluate.py` with ensemble variance calculation
- [ ] T031 [US3] Implement convex hull distance calculation for `true_novel.csv` entries in `code/evaluate.py` and prepare data for correlation analysis.
- [ ] T032 [US3] Implement statistical t-test (FR-006) to compare error distributions of training vs. holdout sets in `code/evaluate.py`
- [ ] T033 [US3] Implement Spearman rank correlation test (FR-007) between variance (from T030) and convex hull distance (from T031) in `code/evaluate.py` to verify uncertainty calibration.
- [ ] T035a [US3] Compute a lower-tail percentile of the training set's variance distribution. and validate top candidates against this threshold (SC-005) in `code/evaluate.py`. **Output**: Store threshold in `data/processed/variance_threshold.json` (runtime state file) to be consumed by T034.
- [ ] T034 [US3] Implement `code/report.py` to generate final report with novel candidates ranked by uncertainty

The research question is to identify novel candidates using uncertainty-based ranking. The method involves generating a ranked list of novel candidates based on uncertainty scores. References include [Citation]. (lowest variance). **Logic**: **Filter** candidates where variance <= 10th percentile threshold (from T035a's `data/processed/variance_threshold.json`) BEFORE ranking. **Output**: `data/processed/top_100_novel_candidates.csv` with columns: `composition_string`, `predicted_energy`, `variance`, `convex_hull_distance`, `rank`. **Dependency**: Input: Threshold from T035a.
- [ ] T035 [US3] Implement report generation for accuracy degradation metrics or uncertainty correlation coefficients in `code/report.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` with installation steps and data flow diagram
- [ ] T037 Refactor code to remove unused imports and ensure PEP8 compliance
- [ ] T038 Profile `code/data_ingestion.py` and optimize streaming logic to ensure <7GB RAM usage
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 Run quickstart.md validation

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces** `heas_train.csv`, `holdout_known.csv`, `true_novel.csv`.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **Depends on** US1 outputs (`heas_train.csv`). **Produces** trained models.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). **Depends on** US1 outputs (test sets) and US2 outputs (models). **Produces** evaluation metrics and final report.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading/filtering before feature engineering
- Feature engineering before model training
- Model training before evaluation
- Evaluation before report generation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for data filtering logic in tests/unit/test_ingestion.py"
Task: "Integration test for dataset split logic in tests/integration/test_split.py"

# Launch all implementation tasks for User Story 1:
Task: "Implement code/data_ingestion.py to load hmao/all_apis_for_multiapi with streaming=True"
Task: "Implement filtering logic in code/data_ingestion.py"
Task: "Sample 5000 unique 5-element combinations for 'Hold-out Known' in code/data_ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Splitting)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify disjoint sets and data integrity)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Models trained)
4. Add User Story 3 → Test independently → Deploy/Demo (Evaluation complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Feature Engineering & Training) - *Can start once US1 data is available or mocked for local dev*
 - Developer C: User Story 3 (Evaluation) - *Can start once US1 & US2 outputs are available*
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
- **Critical**: Ensure `code/data_ingestion.py` uses `streaming=True` for `hmao/all_apis_for_multiapi` to respect RAM constraints.
- **Critical**: Ensure `code/data_ingestion.py` samples exactly 5000 combinations (T014, T015) instead of enumerating all.
- **Critical**: Ensure `code/feature_engineering.py` clamps near-zero values to $1e-6$ to prevent numerical instability.
- **Critical**: Ensure `code/evaluate.py` performs strict composition string comparison to avoid hash collisions.
- **Critical**: Ensure `code/report.py` filters candidates by the 10th percentile variance threshold (T035a) before ranking (T034).
- **Critical**: The "Source API" for novelty verification is the static `hmao` proxy dataset per Plan constraints; live API calls are not implemented (documented in T019a).