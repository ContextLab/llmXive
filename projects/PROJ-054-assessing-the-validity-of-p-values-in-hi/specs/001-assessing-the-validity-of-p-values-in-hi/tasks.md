# Tasks: Assessing the Validity of p-Values in High-Dimensional Data

**Input**: Design documents from `/specs/001-assess-p-value-validity/`
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

- [X] T001 [P] Create `code/` directory at repository root
- [X] T002 [P] Create `data/` directory at repository root with subdirectories `raw/`, `synthetic/`, `results/`
- [X] T003 [P] Create `tests/` directory at repository root with subdirectories `unit/`, `integration/`
- [X] T004a [P] Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, pandas, matplotlib, seaborn, pytest)
- [X] T005 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.ruff.toml` and `code/.black`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Define error code `ERR_HIGH_DIMENSIONAL_INSTABILITY` in `code/utils/exceptions.py` specifically for condition number > 10^12 (required by T007)
- [X] T007 [P] Implement covariance regularization utility in `code/utils/regularization.py` (FR-009: handle singular matrices, condition number > 10^12, raise `ERR_HIGH_DIMENSIONAL_INSTABILITY`)
- [X] T008 [P] Create base `SyntheticDataset` data model and schema in `code/utils/simulation.py`
- [X] T009 [P] Setup simulation orchestration framework in `code/utils/simulation.py` (manages iterations, seeds, parameter sweeps)
- [X] T010 [P] Implement a memory monitor in `code/utils/simulation.py` that logs a warning if RSS > 6GB (per plan goal) but does NOT raise an error (spec FR-009 only requires handling singular matrices)
- [X] T011 [P] Implement power analysis utility in `code/utils/simulation.py` to calculate the minimum simulation iteration count required to achieve statistical power >= 0.8 for detecting a KS statistic deviation > 0.05. The task MUST verify that the selected number of iterations is sufficient or document the required count and update plan.md if the initial selection is insufficient (SC-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation with Controlled Correlation and Distribution Violations (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic high-dimensional datasets with precisely controlled correlation structures, sample-to-dimension ratios, and distributional violations (heavy-tailed or skewed) under known ground-truth null conditions.

**Independent Test**: Can be fully tested by verifying that generated data matrices have the exact correlation structure specified (within numerical tolerance) and that the null hypothesis is true by construction.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for correlation matrix generation accuracy in `tests/unit/test_data_gen.py`
- [X] T013 [P] [US1] Unit test for distribution shape validation (t-distribution, skewed normal) in `tests/unit/test_data_gen.py` (Verify `test_t_dist_df3` passes with KS distance < 0.01)
- [X] T014 [P] [US1] Integration test for null hypothesis validity (no mean differences) in `tests/integration/test_data_gen.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `generate_correlated_data` function in `code/generate_data.py` supporting discrete correlation thresholds $\rho$ spanning from no correlation to strong positive correlation.
- [X] T016 [P] [US1] Implement distributional violation generators (heavy-tailed t-distribution, skewed normal) in `code/generate_data.py`
- [X] T017 [US1] Implement parameter sweep logic for a range of $n$ values, $p \in \{500, 1000, 2000, 5000\}$, and $\rho \in \{0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$ in `code/generate_data.py`, using the iteration count determined by T011 (Power Analysis). Output a CSV file `data/sweep/params.csv` with columns `seed, n, p, rho`.
- [X] T018 [US1] Write `data/synthetic/{seed}.json` containing `sha256`, `rho`, `n`, `p`, `distribution_type`, and `seed` and verify file exists and `sha256` matches the generated dataset hash (Constitution Principle III)
- [X] T019 [US1] Store full RAW synthetic data trajectories (all raw data points per iteration) in `data/synthetic/trajectories/{seed}.npy` (NumPy binary for efficiency) with `dtype=float32` and shape `(N_iterations, n, p)`. Verify file exists, contains array of length N, and shape matches `(N_iterations, n, p)` (FR-001, SC-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hypothesis Test Execution and p-Value Collection (Priority: P2)

**Goal**: Apply standard t-tests and F-tests to the synthetic null data and collect all resulting p-values to empirically observe their distribution under violated assumptions.

**Independent Test**: Can be fully tested by running hypothesis tests on a known null dataset and verifying that p-values are collected for every test without missing values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for t-test/F-test execution on null data in `tests/unit/test_stats.py`
- [X] T021 [P] [US2] Integration test for full iteration loop (multiple iterations) without runtime errors in `tests/integration/test_stats.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement data ingestion pipeline in `code/run_tests.py` to load raw synthetic data from `data/synthetic/trajectories/{seed}.npy` (Depends on T019 completion)
- [X] T023 [P] [US2] Implement `run_hypothesis_tests` function in `code/run_tests.py` (scipy.stats t-test, f-test)
- [X] T024 [US2] Implement p-value collection logic ensuring exactly $p$ values per iteration (FR-003) and store in `data/results/pvalues_{seed}.csv`; verify row count equals p.
- [X] T025 [US2] Integrate with `generate_data.py` to run tests on each generated dataset. Depends on T017 (parameter sweep) and T022 (data ingestion) completion for dataset availability.

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - P-Value Distribution Analysis and Deviation Quantification (Priority: P3)

**Goal**: Analyze the collected p-values using Kolmogorov-Smirnov statistics and QQ-plots against a Gold Standard (permutation-based) reference to quantify anti-conservative bias.

**Independent Test**: Can be fully tested by running the analysis on a fixed dataset and verifying that KS statistics and QQ-plots are produced with correct statistical calculations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for KS statistic calculation against uniform/permutation reference in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for QQ-plot generation and visual validation in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement permutation test generator in `code/analyze_pvalues.py` (Gold Standard respecting correlation structure) (Requires data format from US1/US2 to be complete)
- [X] T029 [US3] Implement KS statistic calculation comparing standard tests to permutation reference (FR-004) and store results in `data/results/ks_stats.json`; verify against known uniform value.
- [X] T030 [US3] Implement QQ-plot generation for visual inspection (FR-005) and save to `docs/plots/qq_{seed}.png`; verify file exists and is non-empty.
- [X] T031 [US3] Implement sensitivity analysis sweep for discrete $\rho \in \{0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$ and report KS variations (FR-007); output `data/results/sensitivity.csv` with columns `rho, ks_stat`.
- [X] T032 [US3] Implement bootstrap confidence interval calculation for KS statistics and store results in `data/results/bootstrap_cis.json` with fields defined in `contracts/simulation_result.yaml`: `KS_statistic`, `bootstrap_ci_lower`, `bootstrap_ci_upper`, `rho`, `n`, `p`, `seed` (Constitution Principle VII)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` including methodology for data generation and analysis (Update `docs/methodology.md` and `docs/results.md`)
- [ ] T041 [P] Code cleanup and refactoring (Run `ruff check --fix`, ensure [deferred] type coverage with `mypy`)
- [ ] T042 [P] Profile full simulation sweep runtime and verify it completes within 6 hours on 2 CPU cores (SC-004)
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (T017, T018, T019)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 p-value collection AND US1 trajectory storage (T019)

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
Task: "Unit test for correlation matrix generation accuracy in tests/unit/test_data_gen.py"
Task: "Unit test for distribution shape validation in tests/unit/test_data_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement generate_correlated_data function in code/generate_data.py"
Task: "Implement distributional violation generators in code/generate_data.py"
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
- Avoid: vague tasks, cross-story dependencies that break independence
- **Revision Note**: Removed orphan tasks T033-T036 (Failure Mode/Embarrassing Theory) as they lacked spec requirements. Renumbered Phase N tasks to T040/T041. Fixed T004.5 to T004a/T004b. Clarified T017 (raw data) vs T024 (p-values) storage formats. Updated T007 to remove unauthorized hard stop.