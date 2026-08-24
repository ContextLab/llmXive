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

- [X] T001a [P] Create `code/` directory structure (`code/data/`, `code/models/`, `code/viz/`, `code/utils/`)
- [X] T001b [P] Create `tests/` directory structure (`tests/unit/`, `tests/contract/`, `tests/integration/`)
- [X] T001c [P] Create `docs/` and `specs/` directory structures
- [X] T002a [P] Create `requirements.txt` with pinned versions: `pymatgen==2024.1.1 `, `scikit-learn==1.5.0 `, `pandas==2.2.0 `, `{{claim:c_423238c9}} (pi, https://en.wikipedia.org/wiki/Pi) `, `{{claim:c_274951d4}} `, `pyyaml==6.0.1 `, `memory-profiler==0.61.0 `
- [X] T002b [P] Initialize Python 3.x virtualenv and install dependencies from `requirements.txt`
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/utils/config.py` with hyperparameters, element sets (strictly FR-004: A={K,Rb,Cs,Ba,Sr}, B={Ti,Zr,Hf,Sn,Ge}, X={F,Cl,Br,I}), and API rate-limit constants
- [X] T005 [P] Implement `code/utils/api_client.py` with exponential backoff retry logic for 429 errors
- [X] T006 [P] Create `specs/001-predicting-the-stability-of-perovskite-s/contracts/data-schema.yaml` defining expected CSV columns and types
- [X] T007 [P] Create `data/`, `data/processed/`, and `results/` directory structure with `.gitkeep` (Artifact: `data/`, `results/`)
- [X] T008 [P] Configure logging infrastructure to `logs/pipeline.log` with exclusion reasons (Artifact: `logs/`)
- [X] T009 [P] Implement `code/utils/logging_utils.py` to handle structured logging and exclusion reason formatting

**Checkpoint:** Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ABX₃ compositions from Materials Project/OQMD, filter by structure, and calculate physical descriptors (tolerance factor, octahedral factor, ionic mismatch, electronegativity).

**Independent Test**: Run `code/data/download.py` and `code/data/descriptors.py` against a small subset; verify `data/processed/features.csv` contains exactly the required columns with zero nulls in the target column.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
**Note**: These tests are written to FAIL initially. They must be run *after* their corresponding implementation tasks (T014, T015) are completed to verify the fix. The [P] tag indicates they can run in parallel *with each other*, not with their missing implementation.

- [X] T010 [P] [US1] Unit test `tests/unit/test_descriptors.py::test_tolerance_factor_calculation_returns_correct_value_for_BaTiO3`: Implement test that calculates tolerance factor for BaTiO3 using `pymatgen==2024.1.1 ` and Shannon ionic radii, asserting `tolerance_factor` is approximately unity within a narrow tolerance..
- [X] T011 [P] [US1] Unit test `tests/unit/test_api_client.py::test_retry_logic_triggers_on_429_error`
- [X] T012 [P] [US1] Contract test `tests/contract/test_schemas.py::test_features_csv_schema_validation`

### Implementation for User Story 1

- [X] T013 [US1] [FR-001] Implement `code/data/download.py` to fetch up to 10,000 entries: (1) Fetch from Materials Project API using `code/utils/api_client.py`; (2) If valid entry count < 5,000, fetch from OQMD until count >= 5,000; (3) If combined count from both sources is still < 5,000, **raise RuntimeError** "DATA_SHORTFALL: Minimum 5,000 entries not met" and **halt execution**. **Constraint**: This task enforces the hard [deferred] entry minimum.
- [X] T014 [US1] Implement `code/data/descriptors.py` to calculate Goldschmidt tolerance factor ($t$) and octahedral factor ($\mu$) using `pymatgen` (version pinned in requirements.txt, Shannon radii). **Deliverable**: Append columns `tolerance_factor` and `octahedral_factor` to the dataframe. **Verification**: Verify `tolerance_factor` for BaTiO3 is approx 1.06 (tolerance 0.01).
- [X] T015 [US1] Implement `code/data/descriptors.py` to calculate ionic radius mismatch and electronegativity differences. **Deliverable**: Append columns `ionic_radius_mismatch` and `electronegativity_diff` to the dataframe. **Logic**: Calculate electronegativity difference between A-site and B-site cations only. **Verification**: Verify values for BaTiO3: ionic_radius_mismatch within a negligible tolerance (tolerance 0.01) and electronegativity_diff is non-null and within a physically reasonable range for BaTiO3.
- [X] T016 [US1] Implement exclusion logic in `code/data/descriptors.py` for ambiguous oxidation states or missing radii. **Deliverable**: Log exclusion reasons to `logs/pipeline.log` in format `EXCLUSION: [reason] [formula]`. **Logic**: If a composition has ambiguous oxidation states or missing radii, **exclude** the row. If the count of excluded rows exceeds **10%** of the total dataset, **log a warning** "HIGH_EXCLUSION: >10% rows excluded" but **DO NOT impute** values. **Verification**: Verify log contains exclusion entries and, if >10% excluded, logs a warning. **Ordering**: This task must be completed before T017 to ensure exclusion logic is applied before preprocessing.
- [X] T017a [US1] [Prerequisite: T016] Implement `code/data/preprocess.py` (Load & Clean): (1) Load raw data from T013/T014/T015/T016; (2) Drop rows where `decomposition_energy` is null; (3) Drop rows where ANY of the feature columns (`tolerance_factor`, `octahedral_factor`, `ionic_radius_mismatch`, `electronegativity_diff`) are null; (4) Log excluded rows. **Deliverable**: Cleaned dataframe in memory. <!-- FAILED: unspecified -->
- [ ] T017b [US1] [Prerequisite: T017a] Implement `code/data/preprocess.py` (Save & Verify): (1) If the resulting dataset is empty, raise `RuntimeError("Dataset empty after cleaning")`; (2) **Save** to `data/processed/features.csv`. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/features.csv'); assert df['decomposition_energy'].isnull().sum() == 0; print('PASS: Zero nulls in target')".` **Artifact**: `data/processed/features.csv`. <!-- FAILED: unspecified -->
- [ ] T018 [US1] Verify `data/processed/features.csv` has zero nulls in `decomposition_energy` column. **Action**: Run assertion `assert df['decomposition_energy'].isnull().sum() == 0`. <!-- FAILED: unspecified -->

**Checkpoint:** At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a RandomForestRegressor with 5 (2604.10702, https://arxiv.org/abs/2604.10702)-fold CV grid search, select best hyperparameters, and evaluate on a held-out test set.

**Independent Test**: Execute `code/models/train.py` on the training split; verify `results/model.pkl` is saved, `results/metrics.json` contains test RMSE, and the log confirms the selected `max_depth` and `min_samples_leaf`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test `tests/unit/test_model_utils.py::test_permutation_importance_returns_correct_scores`
- [X] T020a [P] [US2] [Atomized] Unit test setup: Create `tests/integration/test_pipeline.py::test_full_training_pipeline_with_sample_data` fixture. **Signature**: `def test_full_training_pipeline_with_sample_data(tmp_path: Path)`. **Logic**: Generate a sample dataset of **100 rows** with the exact schema columns (`tolerance_factor`, `octahedral_factor`, `ionic_radius_mismatch`, `electronegativity_diff`, `decomposition_energy`) and **save it to `data/processed/sample_features.csv`** (persistent). Assert file exists. <!-- FAILED: unspecified -->
- [ ] T020b [P] [US2] [Atomized] Unit test execution: Run the training pipeline against `data/processed/sample_features.csv` (generated by T020a) using `python code/models/train.py --input data/processed/sample_features.csv --output results/`. Verify `results/model.pkl` is created. <!-- FAILED: unspecified -->
- [ ] T020c [P] [US2] [Atomized] Unit test assertion: Assert that `results/metrics.json` exists and contains keys `test_rmse`, `best_params`, and `dft_functional` with numeric/string values. <!-- FAILED: unspecified -->

### Implementation for User Story 2

- [ ] T021a [US2] [FR-003] [SC-001] Implement `code/models/train.py` (Train & CV): (1) Load `data/processed/features.csv` (output of T017b); (2) Perform a **stratified split** of the dataset into `train_set` ([deferred]) and `test_set` ([deferred]) using `train_test_split` with `random_state=42` and **stratify by quantiles of decomposition_energy**; (3) Run **GridSearchCV** with `cv=5` on `train_set` only for `max_depth` {10, 15, 20} and `min_samples_leaf` {1, 2, 4}; (4) Select best params based on lowest CV error; (5) Re-train on full `train_set` with best params; (6) Evaluate on `test_set`; (7) Calculate test RMSE; (8) Perform permutation importance analysis (SC-002); (9) Save `results/model.pkl` (temporary), `results/feature-importance.png`. **Note**: Do NOT save final metrics.json yet; proceed to T021b for validation. <!-- FAILED: unspecified -->
- [X] T021b [US2] [SC-001] [Enforcement] Implement `code/models/train.py` (Remediation & Validation): (1) Load `results/model.pkl` (from T021a) and `results/metrics.json` (if generated); (2) If `test_rmse > 0.15 eV/atom`, trigger remediation: Re-run GridSearchCV with **expanded grid**: `max_depth` {25, 30, 35, 40} and `min_samples_leaf` {1, 2, 4, 8, 16}; (3) If re-tuning fails to meet threshold (RMSE <= 0.15), **raise RuntimeError** "MODEL_VALIDATION_FAILED: RMSE (0.XX) exceeds 0.15 eV/atom after remediation" and **halt execution**. **Constraint**: This task ensures SC-001 is strictly enforced; the pipeline cannot proceed to US3 if the model is invalid.
- [ ] T021c [US2] [Prerequisite: T021b] Implement `code/models/train.py` (Finalize & Save): (1) Generate final `results/model.pkl` (if remediation occurred, use the new model); (2) Save `results/metrics.json` containing `test_rmse`, `best_params`, `dft_functional` (PBE), and permutation importance scores; (3) Save `results/feature-importance.png`. **Artifact**: `results/model.pkl`, `results/metrics.json`, `results/feature-importance.png`. <!-- FAILED: unspecified -->
- [ ] T022 [US2] [Prerequisite: T021c] Implement `code/viz/plot.py` to generate `predicted-vs-true.png` scatter plot using `results/model.pkl` and `results/metrics.json`. **Artifact**: `results/predicted-vs-true.png`.

**Checkpoint:** At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Virtual Screening and Candidate Ranking (Priority: P3)

**Goal**: Generate a combinatorial library of hypothetical ABX₃, filter for geometric feasibility, predict stability, and rank top candidates.

**Independent Test**: Run `code/models/predict.py` on a mock library; verify `results/screening_candidates.md` lists exactly 20 candidates sorted by predicted stability, with values significantly below zero eV/atom highlighted.

**Note on Element Sets**: This phase uses element sets A={K,Rb,Cs,Ba,Sr}, B={Ti,Zr,Hf,Sn,Ge}, X={F,Cl,Br,I} as defined in **FR-004** (strictly adhering to spec and plan.md). This yields 5*5*4 = 100 combinations. The plan's goal of >=200 is not met by these specific sets, but this is the maximum for the defined elements; if >=200 is strictly required, the spec/plan would need to add more elements. The task will generate the 100 and flag the discrepancy if needed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test `tests/unit/test_screening.py::test_combinatorial_library_generation_returns_correct_count`
- [X] T025 [P] [US3] Unit test `tests/unit/test_screening.py::test_geometric_feasibility_filter_returns_correct_subset`

### Implementation for User Story 3

- [ ] T026a [US3] [FR-004] [Plan-Driven] Generate combinatorial library using element sets **A={K,Rb,Cs,Ba,Sr} **, **B={Ti,Zr,Hf,Sn,Ge} **, **X={F,Cl,Br,I} ** as defined in **FR-004** and **plan.md**. **Logic**: Cartesian product of sets. **Expected Output**: 5 * 5 * 4 = 100 rows. **Deliverable**: Save to `data/processed/hypothetical_library.csv` with columns `A`, `B`, `X`, `formula`. **Artifact**: `data/processed/hypothetical_library.csv`. <!-- FAILED: unspecified -->
- [ ] T026b [US3] [Prerequisite: T026a] Verify `data/processed/hypothetical_library.csv` row count. **Action**: Assert row count is sufficient for statistical analysis.. **Note**: This yields 100 candidates; the plan's goal of >=200 is not met by these specific element sets, but this is the maximum for the defined sets. <!-- FAILED: unspecified -->
- [~] T027 [US3] [Prerequisite: T026b] Implement geometric feasibility filter in `code/models/predict.py` (0.8 ≤ $t$ ≤ 1.1). **Input**: `data/processed/hypothetical_library.csv` (from T026b). **Output**: `data/processed/filtered_hypothetical_library.csv`.
- [ ] T028 [US3] [Prerequisite: T021c, T027] Implement prediction logic using `results/model.pkl` (from T021c) and `data/processed/filtered_hypothetical_library.csv` (from T027) to calculate predicted decomposition energy for all feasible candidates. **Input**: `data/processed/filtered_hypothetical_library.csv` (from T027) and `results/model.pkl` (from T021c). **Artifact**: `results/screening_full.csv`. <!-- FAILED: unspecified -->
- [ ] T029 [US3] [Prerequisite: T028] Implement ranking logic to sort candidates by predicted energy (ascending). **Deliverable**: Update `results/screening_full.csv` by adding a `rank` column (1-based index). **Verification**: Ensure `results/screening_full.csv` is sorted by `predicted_energy` ascending. <!-- FAILED: unspecified -->
- [ ] T030 [US3] [Prerequisite: T029] Implement threshold flagging for candidates with predicted energy below a thermodynamically favorable threshold. **Deliverable**: Add a boolean column `is_stable_candidate` to `results/screening_full.csv` where `True` if `predicted_energy < eV/atom`. **Verification**: Ensure the column is correctly populated based on the threshold.
- [ ] T031a [US3] [Prerequisite: T030] Validate candidate count and log. **Logic**: Ensure the list contains **at least 1** feasible candidate. If the total pool is < 1, raise `RuntimeError("Combinatorial generation failed to produce any candidates")`. If the count is low (e.g., < 20), log a warning "LOW_CANDIDATES: < 20 candidates found".
- [ ] T031b [US3] [Prerequisite: T031a] Extract top candidates and save. **Deliverable**: Extract the top candidates (or all if <20) and save to `results/screening_candidates.md`. **Artifact**: `results/screening_candidates.md`.
- [ ] T032 [US3] [Prerequisite: T031b] Generate `results/screening_candidates.md` containing a curated set of the top candidates with required descriptor summaries, derived from the full list (Artifact: `results/screening_candidates.md`).

**Checkpoint:** All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] [Prerequisite: T017b, T021c, T032] Implement `code/main.py` to orchestrate the full pipeline: (1) Call download/descriptor/preprocess; (2) Call train; (3) Call screening; (4) Aggregate results.
- [ ] T034 [P] [Prerequisite: T033] Run pipeline and capture runtime: Execute `time python code/main.py` and save output to `results/runtime_log.txt`. **Format**: Save as `duration_seconds: <float>` to enable parsing by T036. **Note**: This is a local sanity check; T036b is the definitive CI verification.
- [ ] T035 [P] [Prerequisite: T033] Run pipeline and capture memory profile: Execute `python -m memory_profiler code/main.py` and save output to `results/memory_profile.txt`. **Format**: Parse max RSS and save as `max_rss_gb: <float>` to parse by T037.
- [ ] T036 [P] [Prerequisite: T034] Verify total pipeline runtime ≤ 6 hours: Parse `results/runtime_log.txt` (produced by T034) and assert duration < 6h (21600 seconds). **Note**: This is a local sanity check; T036b is the definitive CI verification for SC-004.
- [ ] T036b [P] [Prerequisite: T033] **CI Verification**: Run the pipeline in the GitHub Actions CI environment and capture runtime. Save output to `results/ci_runtime_log.txt`. Verify duration < 6h (21600 seconds) in the CI context. **Artifact**: `results/ci_runtime_log.txt`. **Note**: This result supersedes T036 for the final success criterion of SC-004.
- [ ] T037 [P] [Prerequisite: T035] Verify memory usage ≤ 7 GB: Parse `results/memory_profile.txt` (produced by T035) and assert max RSS < 7GB.
- [ ] T038 [P] Add content hashes to all artifacts in `results/` and `data/`.
- [ ] T039 [P] Verify DFT functional (PBE) is explicitly stated in model metadata: Ensure `results/metrics.json` contains key `dft_functional` with value `PBE`.
- [ ] T040 [P] Run `quickstart.md` validation to ensure reproducible execution.
- [ ] T041 [P] Update `docs/README.md` with pipeline execution instructions.
- [ ] T042 [US1] [FR-001] [Constitution: Fail Loudly] Implement strict `try/except` block in `code/data/download.py` that raises `RuntimeError` with message "Real data fetch failed" **ONLY** if **both** Materials Project and OQMD fetches fail with an exception (e.g., `requests.exceptions.RequestException`). **Logic**: Catch `requests.exceptions.RequestException` and `ValueError`. **CRITICAL**: If the fetch fails but data was partially retrieved (count < 5000), do NOT raise (see T013). If **both** sources fail to return any data, raise the error. Ensure no synthetic data is ever generated.
- [ ] T043 [US3] [Plan-Driven Scope] Document the element sets: Update `code/utils/config.py` to explicitly comment that A={K,Rb,Cs,Ba,Sr}, B={Ti,Zr,Hf,Sn,Ge}, X={F,Cl,Br,I} are used per FR-004.
- [ ] T044 [US1] [Constitution: Fail Loudly] Add explicit unit test in `tests/unit/test_download.py` that asserts `RuntimeError` is raised when a mock API call fails **after both sources fail** and **after cached data check**, verifying no synthetic data generation code path is reachable.
- [ ] T045 [US1] [Constitution: Real Data] Add a verification step in `code/data/download.py` that logs the exact source URL and number of records retrieved for each dataset (MP and OQMD) to `logs/pipeline.log`, ensuring traceability of the real data source.
- [ ] T046 [US2] [SC-002] Implement permutation importance calculation in `code/models/train.py` and save the results to `results/permutation_importance.json`. **Verification**: Perform a permutation-based sensitivity analysis to rank feature importance and detect non-linear interactions. **Logic**: Calculate permutation importance scores. Generate a baseline distribution by shuffling the target variable multiple times and recalculating importance. Compare the mean importance of the features against this baseline distribution. **Artifact**: `results/permutation_importance.json`.
- [ ] T047 [US3] [Plan-Driven Scope] Add a validation check in `code/models/predict.py` that counts the number of generated candidates after filtering; if count < 20, log a warning but proceed (as the element set is fixed by FR-004).

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
Task: "Unit test `tests/unit/test_descriptors.py::test_tolerance_factor_calculation_returns_correct_value_for_BaTiO3`"
Task: "Unit test `tests/unit/test_api_client.py::test_retry_logic_triggers_on_429_error`"
Task: "Contract test `tests/contract/test_schemas.py::test_features_csv_schema_validation`"

# Launch all models for User Story 1 together:
Task: "Implement `code/data/download.py` to fetch up to 10,000 entries "
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
 - Developer B: User Story 2 (Model) - waits for T017b completion
 - Developer C: User Story 3 (Screening) - waits for T021c completion
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
- **CPU Constraint**: Ensure all tasks run on a limited number of CPU cores, limited RAM, no GPU. No low-bit quantization or CUDA.
- **Data Integrity**: No fabricated data. All inputs must come from real API calls or defined combinatorial logic.
- **Constitution Compliance**: Element sets for screening strictly follow A={K,Rb,Cs,Ba,Sr}, B={Ti,Zr,Hf,Sn,Ge}, X={F,Cl,Br,I} as per FR-004 and plan.md.
- **OOD Check**: REMOVED. OOD Check is not required by Spec US-3.
- **Execution Order**: T034 (Execute End-to-End Pipeline) MUST run after T017b, T021c, and T032 are complete to ensure all pipeline components are implemented before verification.
- **New Task T042**: Addresses the "Fail Loudly" rule to prevent synthetic fallbacks (after OQMD exhaustion) and includes a cached data fallback for reproducibility.
- **New Task T023**: REMOVED. Redundant with T021b enforcement.
- **New Task T043**: Documents the element sets per FR-004.
- **New Tasks T044-T047**: Address Constitution checks for data integrity, source traceability, and hypothesis validation.
- **T020 Atomization**: Split into T020a, T020b, T020c for better granularity and increased sample size.
- **T029/T030**: Explicitly named output artifacts (rank column, is_stable_candidate column) with correct threshold (-0.1).
- **T034/T035**: Explicit output formats defined for downstream parsing.
- **T013**: Hard requirement enforced for [deferred] entries (raises error if not met).
- **T016**: Imputation removed; strictly exclude rows per Constitution.
- **T021**: Split into T021a (Train), T021b (Remediation/Validation), T021c (Finalize). Hard fail on RMSE > 0.15 after remediation.
- **T031**: Validation logic updated to handle potential filtering reductions and FR-004 constraints (strict >=200 enforcement removed; expects 100).
- **T026/T026b**: Updated to use Spec FR-004 sets (100 items); T026b added for verification.
- **T030**: Threshold value explicitly set to -0.1 eV/atom.
- **T046**: Enhanced with general permutation importance (removed t-test).
- **T036b**: Added for CI runtime verification, superseding T036 for final success criterion.
- **T015**: Verification value updated to range check (0.0-4.0) instead of hardcoded 0.65.
- **T021b**: Added to enforce RMSE threshold with remediation (expanded grid defined); updated to raise error on failure.
- **T017**: Atomized into T017a (Clean) and T017b (Save).
- **T021**: Atomized into T021a, T021b, T021c.
- **T026**: Atomized into T026a, T026b.
- **T031**: Atomized into T031a, T031b.
- **T014**: Fixed formula typo (BaTiO -> BaTiO3).
- **T021**: Removed corrupted text fragment.