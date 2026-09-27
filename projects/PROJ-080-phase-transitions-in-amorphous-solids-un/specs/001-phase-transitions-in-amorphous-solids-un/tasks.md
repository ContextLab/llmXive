# Tasks: Phase Transitions in Amorphous Solids Under Shear Stress

**Input**: Design documents from `/specs/001-phase-transitions-in-amorphous-solids/`
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

- [ ] T001 Create project structure per implementation plan: Create directories `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `specs/contracts` in `projects/PROJ-080-phase-transitions-in-amorphous-solids-un/`
- [ ] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: numpy, scipy, pandas, h5py, scikit-learn, matplotlib, datasets, tqdm)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils.py` with global `SEED = 42` and streaming helpers for HDF5/Parquet
- [ ] T007 Create base data schema definitions in `specs/contracts/` (trajectory.schema.yaml, precursor_metrics.schema.yaml)
- [ ] T008 Configure logging infrastructure to capture warnings for indeterminate trajectories (US1)
- [ ] T009 Setup environment configuration for dataset source verification (HuggingFace `amorphous-silicon-shear-trajectories`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Precursor Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw MD trajectory data, compute $D^2_{min}$ and local shear strain, and identify the yielding timestep.

**Independent Test**: Process a single small trajectory (≤ 10,000 steps) and verify the output CSV contains per-particle $D^2_{min}$ and a flagged yielding index.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for Falk-Langer $D^2_{min}$ calculation in `tests/unit/test_preprocess.py`
- [ ] T011 [P] [US1] Integration test for stress-drop detection logic in `tests/unit/test_preprocess.py`
- [ ] T012 [US1] Integration test for "indeterminate" flagging when stress drop is ambiguous in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 1

- [ ] T013a [US1] Implement `code/preprocess.py`: Create streaming loader function for HDF5/Parquet files. **MUST enforce FR-006**: Check particle count; if > 100k, raise an explicit exception and exit. No synthetic fallbacks.
- [ ] T014a [US1] Implement `code/preprocess.py`: Implement neighbor list builder for particle proximity calculation
- [ ] T014b [US1] Implement `code/preprocess.py`: Implement Falk-Langer $D^2_{min}$ calculation loop for every particle (FR-001)
- [ ] T015a [US1] Implement `code/preprocess.py`: Implement stress-strain curve extraction from trajectory data
- [ ] T015b [US1] Implement `code/preprocess.py`: Implement a drop detection over timesteps to identify yielding onset (FR-002)
- [ ] T016 [US1] Implement `code/preprocess.py`: Flag datasets as "indeterminate" if no sharp stress peak is found and log warnings
- [ ] T036 [P] [US1] Implement robust error handling in `code/preprocess.py` for corrupted or incomplete trajectory files (missing frames, NaN values)
- [ ] T037 [P] [US1] Implement logic to handle trajectories with multiple yielding events (complex plasticity) by flagging them as "multi-yield" and logging detailed metrics
- [ ] T038 [P] [US1] Add numerical stability checks in `code/preprocess.py` to detect and handle NaN/Infinity values in $D^2_{min}$ calculations (e.g., due to neighbor list issues)
- [ ] T039 [P] [US1] Implement a strict "fail loud" policy in data loading: raise explicit exceptions on real data fetch failure; NO synthetic fallbacks allowed
- [ ] T040 [P] [US1] Add unit tests for edge cases: corrupted files, missing frames, NaN values, and multiple yielding events in `tests/unit/test_preprocess.py`
- [ ] T017 [US1] Write output artifacts: `data/processed/precursor_metrics.csv` (per-particle $D^2_{min}$) and `data/processed/yield_flags.json` (yielding timestep)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compare $D^2_{min}$ distributions between brittle and ductile trajectories to identify structural precursors.

**Independent Test**: Run analysis on two labeled datasets (brittle, ductile) and verify output includes KS-test statistic and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for shear-band aggregation logic in `tests/unit/test_analysis.py`
- [ ] T019 [P] [US2] Unit test for Kolmogorov-Smirnov test implementation in `tests/unit/test_analysis.py`
- [ ] T020 [P] [US2] Integration test for "Power Limitation" warning when sample size < 30 in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 2

- [ ] T021 [US2] Aggregate $D^2_{min}$ values to shear bands using **k-means clustering (k=3)** with seed=42 (from `utils.py`) to account for spatial autocorrelation and ensure Numerical Determinism (Constitution Principle VII).
- [ ] T022 [US2] Perform a **two-sample Kolmogorov-Smirnov (KS) test** to compare brittle vs. ductile distributions as mandated by FR-003. **Output**: Generate `data/processed/permutation_p_value.json` (renamed to `ks_test_results.json`) containing the KS statistic, p-value, and explicit metadata framing the result as an "associational finding" (not causal).
- [ ] T023 [US2] Check sample size (N ≥ 30). If < 30, halt and report "Power Limitation" warning (US2 Acceptance)
- [ ] T024 [US2] Apply Bonferroni correction (FR-005) if multiple hypothesis tests are run across strain rates/temperatures
- [ ] T025 [US2] Generate output artifacts: `data/processed/ks_test_results.json` (statistic, p-value, framing), `data/processed/histograms.png` (overlay of distributions)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Threshold Validation (Priority: P3)

**Goal**: Validate a specific $D^2_{min}$ threshold for predicting time-to-failure and perform sensitivity analysis.

**Independent Test**: Apply derived threshold to held-out validation set and verify FPR/FNR and F-score are reported correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_predict.py`
- [ ] T027 [P] [US3] Integration test for confusion matrix generation in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T028a [US3] Derive the base threshold value from US1/US2 outputs (e.g., via optimization or prior analysis) to establish the reference for the sweep. **Dependency**: Must run after T025.
- [ ] T028b [US3] Define 'time-to-failure' as an independent ground truth (total strain at catastrophic failure)
- [ ] T029 [US3] Sweep $D^2_{min}$ threshold over the specific range: `{threshold - 0.05, threshold, threshold + 0.05}` as mandated by FR-004.
- [ ] T030 [US3] Calculate False Positive Rate (FPR), False Negative Rate (FNR), **True Positives (TP), True Negatives (TN), and F-score (F1)** for each threshold step (US3 Acceptance). **Output**: Confusion matrix components.
- [ ] T031 [US3] Generate output artifacts: `data/processed/prediction_results.json` (confusion matrix, F-score, FPR, FNR), `data/processed/sensitivity_table.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Performance & Validation (Cross-Cutting)

**Purpose**: Ensure the pipeline meets runtime and memory constraints on the target CI environment.

- [ ] T032a [P] [SC-004] Implement `code/metrics.py`: Runtime instrumentation wrapper to measure execution time
- [ ] T033a [P] [SC-005] Implement `code/metrics.py`: Peak memory tracking logic
- [ ] T035 [SC-004, SC-005] Execute full pipeline on GitHub Actions runner to verify runtime and memory constraints (requires T032a/T033a completion AND US1/US2/US3 implementation). **Dependency**: Runs after all implementation tasks.
- [ ] T032b [P] [SC-004] Implement `code/metrics.py`: 6-hour limit check and reporting logic using metrics from T035. **Dependency**: Runs after T035.
- [ ] T033b [P] [SC-005] Implement `code/metrics.py`: 7GB limit check and reporting logic using metrics from T035. **Dependency**: Runs after T035.
- [ ] T034 [P] Generate `data/processed/performance_report.json` with all measured outcomes

**Dependencies**: T032b and T033b depend on T035 output; T035 depends on T032a and T033a being implemented.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`precursor_metrics.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Ensure `code/preprocess.py` fails loudly if real data fetch fails; no synthetic fallbacks allowed.
- **Memory Safety**: All data loading must use streaming/chunking to stay under 7GB RAM.
- **Execution Order**: T032a/T033a must be completed before T035; T035 must be completed before T032b/T033b.
- **Constraint Preservation**: All statistical tests and clustering methods must strictly adhere to FR-003 and Constitution Principle VII (KS-test, k-means k=3).