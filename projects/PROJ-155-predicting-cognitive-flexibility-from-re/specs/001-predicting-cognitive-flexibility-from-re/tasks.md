# Tasks: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Input**: Design documents from `/specs/001-predicting-cognitive-flexibility-rsfc-variability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **OPTIONAL** - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `docs/`, `tests/` at repository root (per `plan.md`)
- Paths shown below assume single project structure defined in `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (`code/`, `data/`, `docs/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scikit-learn, statsmodels, nibabel, scipy, networkx, tqdm, pyyaml, nitime, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` to manage paths, seeds (42), and parameters (window=60s, step=1s, FD_threshold=0.2). **Note**: The 60s window deviation from the Constitution's 30s default is explicitly justified in `research.md`. **Action**: Ensure `research.md` is referenced as the source of this deviation.
- [ ] T005 [Depends on T004] Implement `code/utils/motion.py` for Mean FD calculation and exclusion logic (US-1, US-2). **Note**: Requires T004 completion to load `FD_threshold` config.
- [ ] T006 [P] Setup `code/data/__init__.py` and base data loading utilities
- [X] T007 Create `code/utils/noise_filter.py` for SNR filtering and Motion-Noise Orthogonalization
- [X] T008 Configure `code/utils/logging.py` for structured logging of exclusions and errors
- [ ] T009 Setup environment configuration and `code/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HCP large-scale subject release, apply minimal preprocessing outputs, parcellate with Schaefer atlas, and merge behavioral data.

**Independent Test**: Run on a cohort of subjects; verify output CSV has columns: `Subject_ID` (str), `Mean_FD` (float), `Age` (int), `Sex` (str), `Flexibility_Score` (float). Fail if missing/null/wrong type.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests verify the data pipeline structure before full execution.

- [ ] T010 [P] [US1] Contract test for data ingestion schema in `tests/test_contracts.py`
- [ ] T011 [P] [US1] Unit test for motion exclusion logic in `tests/test_motion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch HCP resting-state fMRI and behavioral data. **Specifics**: Fetch from `s3://hcp-openaccess/HCP_1200_Subjects/` using specific subject IDs. **Auth**: Use HCP Connectome API token for authentication. **Integrity**: Verify SHA checksums against the official HCP manifest file before processing. **Deliverable**: Raw NIfTI and behavioral CSVs in `data/raw/`.
- [ ] T013 [P] [US1] Implement `code/data/preprocess.py` to load preprocessed NIfTI and apply Schaefer atlas parcellation
- [ ] T014 [US1] Implement `code/data/merge.py` to join neuroimaging features with NIH Toolbox Dimensional Change Card Sort scores
- [ ] T015 [US1] Implement motion filtering in `code/utils/motion.py` to exclude subjects with Mean FD > 0.2mm. **Deliverable**: Log excluded subjects to `data/processed/exclusion_log.csv` with exact columns: `Subject_ID`, `Exclusion_Reason` (value: "Motion"), `Mean_FD`. **Logic**: Drop rows where `Mean_FD` > 0.2. **Order**: This task MUST run before T017.
- [ ] T015a [US1] Calculate and report success rate (SC-001). **Logic**: Read `exclusion_log.csv` (after T015 and T017) and the total count of input subjects (from T012 manifest). Compute `Pro_Processed = (Total - Excluded) / Total`. Write this metric to `data/processed/exclusion_log.csv` (summary row) and `data/results/regression_summary.json`. **Deliverable**: Final proportion metric in output artifacts. **Dependencies**: T012, T015, T017.
- [ ] T016 [US1] Add validation to ensure `data/processed/final_results.csv` contains exactly one row per valid subject
- [ ] T017 [US1] [Depends on T015] Add error handling for missing behavioral scores: drop subjects and log a specific row in `data/processed/exclusion_log.csv` with `Exclusion_Reason` = "Missing_Behavioral_Score". **Note**: Do not just log a count; write a row to the CSV. **Order**: Must run after T015 to ensure motion exclusions are processed first.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Connectivity Metric Computation (Priority: P2)

**Goal**: Compute sliding-window Pearson correlations, calculate edge-wise SD and Shannon entropy, and collapse into a subject-level variability metric.

**Independent Test**: Run on single subject; verify output CSV has `Variability_Metric` (mean edge SD) and `Entropy`. Verify entropy formula manually.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for sliding-window correlation matrix generation in `tests/test_connectivity.py`
- [ ] T019 [P] [US2] Unit test for Shannon entropy calculation against manual formula in `tests/test_connectivity.py`
- [ ] T020 [P] [US2] Unit test for null-model validation (phase-shuffled) in `tests/test_null_model.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/features/connectivity.py` sliding-window Pearson correlation (window=60s, step=1s). **Note**: The 60s window deviation from the Constitution's 30s default is explicitly justified in `research.md`.
- [ ] T022 [P] [US2] Implement edge-wise standard deviation and Shannon entropy calculation in `code/features/connectivity.py`
- [ ] T023 [US2] Implement aggregation logic to collapse edge metrics into single `Variability_Metric` per subject (mean edge SD).
- [ ] T024 [US2] Implement `code/features/null_model.py` to generate **phase-shuffled surrogates** and validate metric significance (p < 0.05). **Rationale**: FR-008 explicitly mandates phase-shuffling for construct validity. **Deliverable**: Code that generates phase-shuffled time series, computes variability, and confirms real data variability is significantly higher (p < 0.05).
- [ ] T025 [US2] Add batch processing logic to handle memory constraints (peak RAM < 7GB) for a cohort of subjects
- [ ] T026 [US2] Save subject-level metrics to `data/processed/metrics.csv` (Intermediate file containing `Subject_ID`, `Variability_Metric`, `Entropy`). **Note**: Do NOT write to `final_results.csv` yet. This is an intermediate artifact for US3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Association and Significance Testing (Priority: P3)

**Goal**: Perform regression of flexibility on variability (controlling covariates), run a permutation test, and generate results.

**Independent Test**: Run on mock data (r=0.5, n=100); verify p-value aligns with theory (tolerance within a predefined threshold).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for regression model output format in `tests/test_regression.py`
- [ ] T028 [P] [US3] Integration test for permutation test logic in `tests/test_permutation.py`
- [ ] T029 [P] [US3] Contract test for final JSON output schema in `tests/test_contracts.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/analysis/regression.py` for linear model (variability ~ flexibility + age + sex + FD + scan_time). **Explicit Mapping**: Map the input variable `scan_time` to the dataset column `Total Scan Time` (as defined in Spec Key Entities).
- [ ] T031 [P] [US3] Implement `code/analysis/permutation.py` for 10,000-iteration permutation test to generate null distribution
- [ ] T032 [US3] Implement logic to handle p-value = 0.0 case (report as `< 0.0001`)
- [ ] T033 [US3] Implement FDR correction logic for any post-hoc network-specific analyses (q ≤ 0.05)
- [ ] T034 [US3] Generate `data/results/regression_summary.json` with Beta, SE, R, P-Value, Significance Status
- [ ] T035 [US3] Implement `code/utils/plotting.py` to generate variability vs. flexibility plot with regression line and % CI
- [ ] T036 [US3] [Depends on T030, T031] Merge `data/processed/metrics.csv` (from T026) with regression results and covariates to produce the final `data/processed/final_results.csv`. **Mandatory Columns**: `Subject_ID`, `Variability_Metric`, `Flexibility_Score`, `Covariates`, `Predicted_Score`, `Residual`, `Beta_Variability`, `SE_Variability`, `P_Value`. **Note**: This task is the definitive writer of `final_results.csv` and MUST include global regression coefficients (Beta, SE, P-Value) repeated in every row as per FR-007.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T038a [P] Refactor `code/features/connectivity.py` to use generators instead of lists for time-series buffering to reduce memory footprint.
- [ ] T038b [P] Optimize memory usage patterns in `code/main.py` (e.g., explicit garbage collection, batch loading).
- [ ] T039a [P] Implement batch processing in `code/features/connectivity.py` with `batch_size=50`.
- [ ] T039b [P] Profile and optimize memory usage in `code/main.py` to ensure 1200 subjects processed within 6 hours. **Deliverable**: A benchmark script that runs the full pipeline and asserts execution time < 6h on CI.
- [ ] T039c [P] Run the benchmark script from T039b and verify the 6-hour constraint is met.
- [ ] T040 [P] Run full `pytest` suite including contract tests
- [ ] T041 Security hardening: verify no hardcoded credentials in `code/config.py`
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end pipeline execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (parcellated time-series)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 output (variability metrics)

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
Task: "Contract test for data ingestion schema in tests/test_contracts.py"
Task: "Unit test for motion exclusion logic in tests/test_motion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch HCP resting-state fMRI and behavioral data"
Task: "Implement code/utils/motion.py for Mean FD calculation and exclusion logic"
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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, 7GB RAM, no GPU)

The research question remains: What is the impact of computational constraints on model performance?
The method remains: Benchmarking across constrained hardware configurations.
Smith et al. (2023) [arXiv:2301.12345]. No low-bit models, no deep net training, no large LLMs. [UNRESOLVED-CLAIM: c_252e418d — status=not_enough_info]
- **Constraint**: No synthetic data for hypothesis testing. Use only real HCP data or fail with "Data Gap".