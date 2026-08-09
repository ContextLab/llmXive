# Tasks: Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

**Input**: Design documents from `/specs/001-predict-plant-biomass/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create project data directories: `mkdir -p projects/PROJ-337-predicting-plant-biomass-from-publicly-a/data/{raw,processed,final}` <!-- FAILED: unspecified -->
- [ ] T001b [P] Create project code directories: `mkdir -p projects/PROJ-337-predicting-plant-biomass-from-publicly-a/code/{data,models,analysis,utils,validation}`
- [ ] T001c [P] Create project test directories: `mkdir -p projects/PROJ-337-predicting-plant-biomass-from-publicly-a/tests/{unit,integration,contract}`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 Setup configuration management for seeds, paths, and data sources (`code/utils/config.py`)
- [X] T005 [P] Implement logging infrastructure with exclusion rate tracking (`code/utils/logger.py`)
- [X] T006 [P] Setup runtime timer and resource monitoring (`code/utils/timer.py`)
- [X] T007 Implement Pydantic schemas in `code/models/schemas.py` as defined in `data-model.md`; verify with unit tests that schemas parse valid JSON from `data-model.md` examples
- [ ] T008 Implement chunked data loading utilities to manage RAM constraints.
- [ ] T009 Setup checksum verification utilities for data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HyBiomass/NEON data, apply atmospheric correction, and extract ground-truth labels.

**Independent Test**: The pipeline can be fully tested by running the download and preprocessing scripts on a sample subset (e.g., 5 sites) and verifying that the output CSV contains valid spectral bands, corrected reflectance values, and non-null biomass labels.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement HyBiomass and NEON download script with checksum verification (`code/data/download.py`, FR-001)
- [X] T011 [P] [US1] Implement atmospheric correction module (LEDAPS/FLAASH) ensuring reflectance range [0, 1] (`code/data/preprocess.py`, FR-002); include cloud masking logic to flag/exclude scenes due to cloud cover (per spec Edge Cases) and ensure output CSV contains a `cloud_flag` column; log exclusion counts
- [X] T011b [US1] Validate atmospheric correction output: implement logic in `code/data/preprocess.py` to clip or reject values outside [0, 1] and assert this in unit tests
- [X] T012 [US1] Implement ground-truth extraction script in `code/data/extract_labels.py` with dynamic site subsampling logic: iteratively select sites to ensure the final exclusion rate is ≤ 5%; if the full dataset cannot meet the threshold even after subsampling, log the minimum achievable rate and exit with code 1; log rate and reason
- [X] T013 [US1] Implement `ChunkedHyperspectralLoader` class in `code/data/loader.py` to process full cubes without OOM; verify memory usage < 7GB on full dataset
- [X] T015 [US1] Create integration test for end-to-end data pipeline (download → process → extract) in `tests/integration/test_data_pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Model Training and Evaluation (Priority: P2)

**Goal**: Train Random Forest and TabPFN models, evaluate against null baseline with statistical significance.

**Independent Test**: The modeling step can be tested independently by running the training script on a fixed random seed and verifying that the output metrics (RMSE, MAE, R²) are generated. If TabPFN fails, the fallback Random Forest must complete within the established CPU time limit.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement Random Forest training with 5-fold cross-validation (`code/models/train.py`, FR-004); use `code/utils/timer.py` (T006) to measure execution time
- [ ] T017 [P] [US2] Implement TabPFN training with CPU-only execution and automatic fallback to Random Forest on failure (`code/models/train.py`, FR-004, FR-009); use `code/utils/timer.py` (T006) to measure execution time
- [ ] T018 [US2] Create `NullBaselinePredictor` class in `code/models/baseline.py`; unit test asserts mean prediction matches dataset mean within 1e-6
- [ ] T019 [US2] Implement evaluation script in `code/models/evaluate.py` that consumes the 5-fold CV R² distributions from T016/T017; compute the vector of 5 differences (R²_model - R²_null) per fold; apply the Nadeau & Bengio corrected paired t-test to this vector of 5 values; log significance (FR-005)
- [ ] T021 [US2] Create unit tests for model training logic and fallback mechanism in `tests/unit/test_models.py`
- [ ] T021b [US2] Create integration test in `tests/integration/test_runtime.py` that asserts total time <= 6h using `code/utils/timer.py` (T006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Ablation Study and Sensitivity Analysis (Priority: P3)

**Goal**: Quantify impact of atmospheric correction and structural complexity via ablation and sensitivity analysis.

**Independent Test**: The ablation study can be tested by re-running the training pipeline with specific feature subsets disabled and verifying that the performance metrics change as expected.

### Implementation for User Story 3

- [ ] T022 [P] [US3] Implement ablation study framework toggling atmospheric correction and structural features (`code/models/ablation.py`, FR-006); output delta metrics to `data/final/ablation/`
- [ ] T023 [US3] Implement sensitivity analysis sweeping feature importance cutoffs across a range of low to moderate thresholds (`code/analysis/sensitivity.py`, FR-007); calculate the variance in MAE across the sweep and write the result to `data/final/sensitivity/variance_report.json` to satisfy SC-004; depends on: T016, T017
- [ ] T024 [US3] Implement multiple-comparison correction (Bonferroni/FDR) in `code/models/ablation.py` for the entire set of ablation hypotheses AND the sensitivity analysis thresholds (0.01, 0.05, 0.1) as required by FR-008 and FR-007; consume T022 output and T023 results; report corrected p-values; depends on: T019, T022, T023
- [ ] T025 [US3] Generate comparative reports: write `ablation_results.json` to `data/final/ablation/` containing delta in RMSE/R² for correction, delta for structural features, MAE variance for sensitivity, and corrected p-values from T024; depends on: T022, T023, T024
- [ ] T026 [US3] Create integration tests for ablation and sensitivity workflows in `tests/integration/test_ablation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Update `README.md` with "Quickstart" section detailing: 1. pip install, 2. python code/data/download.py --sample
- [ ] T028a [P] Run `ruff check` on all code and fix all errors
- [ ] T028b [P] Run `black` on all code and verify formatting compliance
- [ ] T029 [P] Vectorize the cloud masking loop in `code/data/preprocess.py` to reduce runtime by >20%; verify in `tests/integration/test_performance.py`
- [ ] T031 [P] Run `bash docs/quickstart.sh` and assert exit code 0

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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