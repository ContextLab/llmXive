# Tasks: Predicting the Stability of Perovskite Structures Using Machine Learning

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `specs/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, requests, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `utils/config.py` with hyperparameters, element sets, and API rate-limit constants
- [ ] T005 [P] Implement `utils/api_client.py` with exponential backoff retry logic for 429 errors
- [ ] T006 [P] Create `contracts/data-schema.yaml` defining expected CSV columns and types
- [ ] T007 Create `data/` and `results/` directory structure with `.gitkeep`
- [ ] T008 Configure logging infrastructure to `logs/pipeline.log` with exclusion reasons

**Checkpoint:** Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ABX₃ compositions from Materials Project/OQMD, filter by structure, and calculate physical descriptors (tolerance factor, octahedral factor, ionic mismatch, electronegativity).

**Independent Test**: Run `code/data/download.py` and `code/data/descriptors.py` against a small subset; verify `data/processed/features.csv` contains exactly the required columns with zero nulls in the target column.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Unit test `tests/unit/test_descriptors.py::test_tolerance_factor_calculation_returns_correct_value_for_KCl3`
- [ ] T010 [P] [US1] Unit test `tests/unit/test_api_client.py::test_retry_logic_triggers_on_429_error`
- [ ] T011 [P] [US1] Contract test `tests/contract/test_schemas.py::test_features_csv_schema_validation`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch up to 10,000 entries from Materials Project API (using `utils/api_client.py`), validate the count, and raise a critical error if the initial MP fetch yields < 5,000 valid entries (merging the logic of T014.5 here).
- [ ] T013 [US1] Implement explicit OQMD ingestion logic in `code/data/download.py` (or a new `code/data/download_oqmd.py`): Fetch from the verified OQMD CSV URL, parse the specific columns (formula, space_group, decomposition_energy), and merge with MP data ONLY if MP yields < 5,000 valid entries. Ensure the merged dataset reaches the minimum threshold required for statistical validity..
- [ ] T014 [US1] Implement structural filtering in `code/data/download.py`: Filter entries where `space_group == 221` (Cubic) OR `space_group == 148` (Rhombohedral).
- [ ] T015 [US1] Implement `code/data/descriptors.py` using `pymatgen` to calculate Goldschmidt tolerance factor ($t$) and octahedral factor ($\mu$).
- [ ] T016 [US1] Implement `code/data/descriptors.py` to calculate ionic radius mismatch and electronegativity differences.
- [ ] T017 [US1] Implement exclusion logic in `code/data/descriptors.py` for ambiguous oxidation states or missing radii, logging reasons to `logs/pipeline.log`.
- [ ] T018 [US1] Create `code/data/preprocess.py` to clean data, handle missing values, and save `data/processed/features.csv`.
- [ ] T019 [US1] Verify `data/processed/features.csv` has zero nulls in `decomposition_energy` column.

**Checkpoint:** At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a RandomForestRegressor with 5-fold CV grid search, select best hyperparameters, and evaluate on a held-out test set.

**Independent Test**: Execute `code/models/train.py` on the training split; verify `results/model.pkl` is saved, `results/metrics.json` contains test RMSE, and the log confirms the selected `max_depth` and `min_samples_leaf`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test `tests/unit/test_model_utils.py::test_permutation_importance_returns_correct_scores`
- [ ] T021 [P] [US2] Integration test `tests/integration/test_pipeline.py::test_full_training_pipeline_with_sample_data`

### Implementation for User Story 2

- [ ] T022 [US2] Implement the `split_data` function in `code/data/preprocess.py` to perform an 80/20 stratified split into `train_set` and `test_set` variables, confirming the `stratify=y` logic matches the plan's nested CV description.
- [ ] T023 [US2] Implement `code/models/train.py` with `RandomForestRegressor` and `GridSearchCV` (cv=5) over `max_depth` {10, 15, 20} and `min_samples_leaf` {1, 2, 4}.
- [ ] T024 [US2] Implement inner-loop CV logic to select best hyperparameters based on lowest cross-validation error.
- [ ] T025 [US2] Implement re-training of the model on the full `train_set` using best parameters.
- [ ] T026 [US2] Implement evaluation on the held-out `test_set` and log test RMSE to `results/metrics.json`.
- [ ] T027 [US2] Implement "low confidence" flagging logic in `code/models/train.py`: Flag model if test RMSE > 0.15 eV/atom (matching SC-001).
- [ ] T028 [US2] Implement permutation-based sensitivity analysis in `code/models/train.py` to validate feature importance hypotheses.
- [ ] T029 [US2] Implement `code/viz/plot.py` to generate `predicted-vs-true.png` scatter plot.
- [ ] T030 [US2] Implement `code/viz/plot.py` to generate `feature-importance.png` bar chart.
- [ ] T031 [US2] Save trained model artifact to `results/model.pkl` and metrics to `results/metrics.json`.

**Checkpoint:** At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Virtual Screening and Candidate Ranking (Priority: P3)

**Goal**: Generate a combinatorial library of hypothetical ABX₃, filter for geometric feasibility, predict stability, and rank top candidates.

**Independent Test**: Run `code/models/predict.py` on a mock library; verify `results/screening_candidates.md` lists exactly 20 candidates sorted by predicted stability, with values < -0.1 eV/atom highlighted.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test `tests/unit/test_screening.py::test_combinatorial_library_generation_returns_correct_count`
- [ ] T033 [P] [US3] Unit test `tests/unit/test_screening.py::test_geometric_feasibility_filter_returns_correct_subset`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/models/predict.py` to generate combinatorial library using A={K, Rb, Cs, Ba, Sr}, B={Ti, Zr, Hf, Sn, Ge}, X={F, Cl, Br, I}. Note: Explicitly adhering to plan.md Phase 3 and Constitution Principle VII (5-element A-site) to ensure generation of >= 200 feasible candidates, overriding the narrower spec.md FR-004 list. Output format: save to `data/processed/hypothetical_library.csv`.
- [ ] T035 [US3] Implement geometric feasibility filter in `code/models/predict.py` (0.8 ≤ $t$ ≤ 1.1).
- [ ] T036 [US3] Implement OOD check in `code/models/predict.py`: Perform range check against training min/max for descriptors. Output: Log warning and add `is_ood` column to output CSV.
- [ ] T037 [US3] Implement prediction logic using `results/model.pkl` to calculate predicted decomposition energy for all feasible candidates.
- [ ] T038 [US3] Implement ranking logic to sort candidates by predicted energy (ascending).
- [ ] T039 [US3] Implement threshold flagging for candidates with predicted energy below a defined thermodynamic threshold.
- [ ] T040 [US3] Save full ranked list to `results/screening_full.csv`. Validation: Ensure the list contains at least 200 feasible candidates as required by the plan.
- [ ] T041 [US3] Generate `results/screening_candidates.md` containing a curated set of the top candidates with required descriptor summaries, derived from the >= 200 full list.

The research question, method, and references remain unchanged.

**Checkpoint:** All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Verify total pipeline runtime ≤ 6 hours: Run full pipeline with `time` command and parse output to confirm duration
- [ ] T043 [P] Verify memory usage ≤ 7 GB: Run pipeline with `memory_profiler` and assert max RSS < 7GB
- [ ] T044 [P] Add content hashes to all artifacts in `results/` and `data/`
- [ ] T045 [P] Verify DFT functional (PBE) is explicitly stated in model metadata (optional but recommended)
- [ ] T046 [P] Run `quickstart.md` validation to ensure reproducible execution
- [ ] T047 [P] Update `docs/README.md` with pipeline execution instructions

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
   - Developer B: User Story 2 (Model) - waits for T018 completion
   - Developer C: User Story 3 (Screening) - waits for T031 completion
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
- **CPU Constraint**: Ensure all tasks run on a limited number of CPU cores, approximately 7 GB RAM, no GPU. No 8-bit quantization or CUDA.
- **Data Integrity**: No fabricated data. All inputs must come from real API calls or defined combinatorial logic.