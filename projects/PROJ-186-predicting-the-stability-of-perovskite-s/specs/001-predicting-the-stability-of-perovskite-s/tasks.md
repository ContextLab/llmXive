# Tasks: Predicting the Stability of Perovskite Structures Using Machine Learning

**Input**: Design documents from `/specs/001-predicting-the-stability-of-perovskite-s/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `utils/config.py` with hyperparameters, element sets, and API rate-limit constants
- [X] T005 [P] Implement `utils/api_client.py` with exponential backoff retry logic for 429 errors
- [X] T006 [P] Create `contracts/data-schema.yaml` defining expected CSV columns and types
- [X] T007 [P] Create `data/` and `results/` directory structure with `.gitkeep` (Artifact: `data/`, `results/`)
- [X] T008 [P] Configure logging infrastructure to `logs/pipeline.log` with exclusion reasons (Artifact: `logs/`)

**Checkpoint:** Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ABX₃ compositions from Materials Project/OQMD, filter by structure, and calculate physical descriptors (tolerance factor, octahedral factor, ionic mismatch, electronegativity).

**Independent Test**: Run `code/data/download.py` and `code/data/descriptors.py` against a small subset; verify `data/processed/features.csv` contains exactly the required columns with zero nulls in the target column.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test `tests/unit/test_descriptors.py::test_tolerance_factor_calculation_returns_correct_value_for_KCl3` <!-- FAILED: unspecified -->
- [X] T010 [P] [US1] Unit test `tests/unit/test_api_client.py::test_retry_logic_triggers_on_429_error`
- [X] T011 [P] [US1] Contract test `tests/contract/test_schemas.py::test_features_csv_schema_validation`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/download.py` to fetch up to 10,000 entries: (1) Fetch from Materials Project API using `utils/api_client.py`; (2) If valid entry count < 5,000, perform a **Dataset Fit Check** on the OQMD API endpoint to verify `decomposition_energy` and `space_group` columns exist BEFORE attempting fetch; (3) If schema validation fails, raise a fatal error; (4) If schema valid, fetch OQMD data; (5) Merge datasets; (6) Filter strictly for Space Group (Cubic) or (Rhombohedral); (7) Raise critical error if total count < 5,000 after fallback.
- [X] T013 [US1] Implement `code/data/descriptors.py` using `pymatgen` to calculate Goldschmidt tolerance factor ($t$) and octahedral factor ($\mu$). <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement `code/data/descriptors.py` to calculate ionic radius mismatch and electronegativity differences. <!-- FAILED: unspecified -->
- [X] T015 [US1] Implement exclusion logic in `code/data/descriptors.py` for ambiguous oxidation states or missing radii, logging reasons to `logs/pipeline.log`. <!-- FAILED: unspecified -->
- [ ] T016 [US1] Create `code/data/preprocess.py` to clean data, handle missing values, and save `data/processed/features.csv` (Artifact: `data/processed/features.csv`).
- [ ] T017 [US1] Verify `data/processed/features.csv` has zero nulls in `decomposition_energy` column.

**Checkpoint:** At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a RandomForestRegressor with 5-fold CV grid search, select best hyperparameters, and evaluate on a held-out test set.

**Independent Test**: Execute `code/models/train.py` on the training split; verify `results/model.pkl` is saved, `results/metrics.json` contains test RMSE, and the log confirms the selected `max_depth` and `min_samples_leaf`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `tests/unit/test_model_utils.py::test_permutation_importance_returns_correct_scores`
- [X] T019 [P] [US2] Integration test `tests/integration/test_pipeline.py::test_full_training_pipeline_with_sample_data`

### Implementation for User Story 2

- [ ] T020 [US2] [FR-003] [SC-001] Implement `code/models/train.py` as a single cohesive module: (1) Load `data/processed/features.csv` from T016; (2) Perform a stratified split by target variable, allocating the majority of samples to the training set and the remainder to the testing set into `train_set` and `test_set`; (3) Run k-fold GridSearchCV on `train_set` only for `max_depth` {10, 15, 20} and `min_samples_leaf` {1, 2, 4}; (4) Select best params; (5) Re-train on full `train_set`; (6) Evaluate on `test_set`; (7) Log test RMSE; (8) Perform permutation importance analysis (SC-002); (9) Save `results/model.pkl`, `results/metrics.json` (including `dft_functional: PBE`), and `results/feature-importance.png`.
- [X] T021 [US2] Implement `code/viz/plot.py` to generate `predicted-vs-true.png` scatter plot (Artifact: `results/predicted-vs-true.png`).

**Checkpoint:** At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Virtual Screening and Candidate Ranking (Priority: P3)

**Goal**: Generate a combinatorial library of hypothetical ABX₃, filter for geometric feasibility, predict stability, and rank top candidates.

**Independent Test**: Run `code/models/predict.py` on a mock library; verify `results/screening_candidates.md` lists exactly 20 candidates sorted by predicted stability, with values significantly below zero eV/atom highlighted.

**Note on Element Sets**: This phase strictly adheres to `spec.md` FR-004 and `Constitution` Principle VII, defining the A-site as {K, Rb, Cs}. The Plan.md Phase 3 expansion to {K, Rb, Cs, Ba, Sr} is noted as a deviation from the Constitution and is NOT implemented here to ensure constitutional compliance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test `tests/unit/test_screening.py::test_combinatorial_library_generation_returns_correct_count`
- [X] T023 [P] [US3] Unit test `tests/unit/test_screening.py::test_geometric_feasibility_filter_returns_correct_subset`

### Implementation for User Story 3

- [ ] T024 [US3] Generate combinatorial library using strictly defined sets A={K, Rb, Cs}, B={Ti, Zr, Hf, Sn, Ge}, X={F, Cl, Br, I}. Output: save to `data/processed/hypothetical_library.csv` (Artifact: `data/processed/hypothetical_library.csv`).
- [X] T025 [US3] Implement geometric feasibility filter in `code/models/predict.py` (0.8 ≤ $t$ ≤ 1.1).
- [X] T026 [US3] Implement prediction logic using `results/model.pkl` to calculate predicted decomposition energy for all feasible candidates (Artifact: `results/screening_full.csv`).
- [X] T027 [US3] Implement ranking logic to sort candidates by predicted energy (ascending).
- [X] T028 [US3] Implement threshold flagging for candidates with predicted energy **< -0.1 eV/atom**.
- [X] T029 [US3] Save full ranked list to `results/screening_full.csv`. Validation: Ensure the list contains at least 200 feasible candidates (Artifact: `results/screening_full.csv`).
- [X] T030 [US3] Generate `results/screening_candidates.md` containing a curated set of the top candidates with required descriptor summaries, derived from the >= 200 full list (Artifact: `results/screening_candidates.md`).

**Checkpoint:** All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Execute End-to-End Pipeline: Run `time python code/main.py` and `python -m memory_profiler code/main.py` in a single step to generate `results/runtime_log.txt` and `results/memory_profile.txt`. (Artifact: `results/runtime_log.txt`, `results/memory_profile.txt`). **Prerequisite**: Must only run after T016, T020, and T030 are complete.
- [X] T032 [P] Verify total pipeline runtime ≤ 6 hours: Parse `results/runtime_log.txt` (produced by T031) and assert duration < 6h.
- [X] T033 [P] Verify memory usage ≤ 7 GB: Parse `results/memory_profile.txt` (produced by T031) and assert max RSS < 7GB.
- [X] T034 [P] Add content hashes to all artifacts in `results/` and `data/`.
- [X] T035 [P] Verify DFT functional (PBE) is explicitly stated in model metadata: Ensure `results/metrics.json` contains key `dft_functional` with value `PBE`.
- [X] T036 [P] Run `quickstart.md` validation to ensure reproducible execution.
- [X] T037 [P] Update `docs/README.md` with pipeline execution instructions.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (features.csv)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model.pkl)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion (download) before descriptor calculation
- Descriptor calculation before model training
- Model training before virtual screening
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Unit tests for different user stories can run in parallel
- Different user stories can be worked on in parallel by different team members (once data/model artifacts are available)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test `tests/unit/test_descriptors.py::test_tolerance_factor_calculation_returns_correct_value_for_KCl3`"
Task: "Unit test `tests/unit/test_api_client.py::test_retry_logic_triggers_on_429_error`"
Task: "Contract test `tests/contract/test_schemas.py::test_features_csv_schema_validation`"

# Launch all models for User Story 1 together:
Task: "Implement `code/data/download.py` to fetch up to 10,000 entries"
Task: "Implement `code/data/descriptors.py` to calculate Goldschmidt tolerance factor"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify features.csv)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Model trained)
4. Add User Story 3 → Test independently → Deploy/Demo (Screening complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Model) - waits for T016 completion
 - Developer C: User Story 3 (Screening) - waits for T020 completion
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
- **CPU Constraint**: Ensure all tasks run on a limited number of CPU cores, limited RAM, no GPU. No 8-bit quantization or CUDA.
- **Data Integrity**: No fabricated data. All inputs must come from real API calls or defined combinatorial logic.
- **Constitution Compliance**: Element sets for screening strictly follow {K, Rb, Cs} per Constitution Principle VII. The Plan.md expansion to {K, Rb, Cs, Ba, Sr} is a deviation that is NOT implemented.
- **OOD Check**: REMOVED. Spec US3 does not require OOD flagging; only ranking by energy. The Plan.md mention of OOD is a non-binding suggestion overridden by the Spec.
- **Execution Order**: T031 (Execute End-to-End Pipeline) MUST run after T016, T020, and T030 are complete to ensure all pipeline components are implemented before verification.
