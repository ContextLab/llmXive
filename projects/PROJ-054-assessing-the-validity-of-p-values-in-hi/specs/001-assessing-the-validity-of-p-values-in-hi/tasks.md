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

- [X] T006 [P] Define error code `ERR_HIGH_DIMENSIONAL_INSTABILITY` in `code/utils/exceptions.py` specifically for condition number > 10^12 (required by T010b)
- [X] T007 [P] Implement covariance regularization utility in `code/utils/regularization.py` (FR‑009: handle singular matrices, condition number > 10^12, apply ε = 10⁻⁶ regularization OR raise `ERR_HIGH_DIMENSIONAL_INSTABILITY`; also detect p/n > 10 and raise the same error)
- [X] T008 [P] Create base `SyntheticDataset` data model and schema in `code/utils/simulation.py`
- [X] T009 [P] Setup simulation orchestration framework in `code/utils/simulation.py` (manages iterations, seeds, parameter sweeps)
- [X] T010a [P] Implement a memory monitor in `code/utils/simulation.py` that logs a warning if RSS > 6 GB (per plan goal) but does NOT raise an error (FR‑009 applies to singular matrices, not general memory usage)
- [X] T010b [P] Implement covariance singularity detector in `code/utils/regularization.py` that checks condition number > 10^12 and raises `ERR_HIGH_DIMENSIONAL_INSTABILITY` if regularization fails (FR‑009)
- [X] T011a [P] Implement power analysis utility function in `code/utils/simulation.py` to calculate the minimum simulation iteration count required to achieve statistical power ≥ 0.8 for detecting a KS statistic deviation > 0.05
- [X] T011b [P] Execute power analysis utility with default parameters (n=100, p=1000, rho=0.5). If the calculated iterations > 1000, create a file `data/sweep/plan_update_request.md` containing the new `required_iterations` value and a note to update `plan.md` Design Parameters. Output `data/sweep/power_analysis_result.json` with `required_iterations` and `status` (sufficient/insufficient) (SC‑005)

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation with Controlled Correlation and Distribution Violations (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic high‑dimensional datasets with precisely controlled correlation structures, sample‑to‑dimension ratios, and distributional violations (heavy‑tailed or skewed) under known ground‑truth null conditions.

**Independent Test**: Can be fully tested by verifying that generated data matrices have the exact correlation structure specified (within numerical tolerance) and that the null hypothesis is true by construction.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for correlation matrix generation accuracy in `tests/unit/test_data_gen.py`
- [X] T013 [P] [US1] Unit test for distribution shape validation (t‑distribution, skewed normal) in `tests/unit/test_data_gen.py` (Verify `test_t_dist_df3` passes with KS distance < 0.01)
- [X] T014 [P] [US1] Integration test for null hypothesis validity (no mean differences) in `tests/integration/test_data_gen.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `generate_correlated_data` function in `code/generate_data.py` supporting discrete correlation thresholds ρ ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}.
- [X] T016 [P] [US1] Implement distributional violation generators (heavy‑tailed t‑distribution, skewed normal) in `code/generate_data.py`
- [X] T017 [US1] Implement parameter sweep logic in `code/generate_data.py` for **n** ∈ {50, 100, 200, 500}, **p** ∈ {500, 1000, 2000, 5000}, and **ρ** ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}. **Dependency**: Must read `required_iterations` from `data/sweep/power_analysis_result.json` to **set the simulation loop bounds**. Output `data/sweep/params.csv` with columns `seed,n,p,rho,distribution_type,iteration`.
- [X] T018 [US1] Write `data/synthetic/{seed}.json` containing `sha256` (of the parameter row), `rho`, `n`, `p`, `distribution_type`, and `seed` for each unique parameter combination. **Serialization**: Serialize the parameter row as a JSON object with keys sorted alphabetically before hashing. Verify file exists and `sha256` matches the parameter hash (Constitution Principle III).
- [X] T019 [US1] Implement a **streaming data generator** in `code/generate_data.py` that iterates through `data/sweep/params.csv`, sets `np.random.seed(seed_value)` **immediately before** generating each matrix, produces the data on‑the‑fly, and **yields numpy arrays to a downstream callback function** to keep memory low. The generator must raise `ERR_HIGH_DIMENSIONAL_INSTABILITY` if `p/n > 10` (FR‑009) or if the covariance matrix is near‑singular after regularization attempts.
- [X] T019b [US1] Generate a **seed map** file `data/sweep/seed_map.json` that maps each unique `(n, p, rho, distribution_type)` tuple to a list of deterministic integer seeds. **Dependency**: Explicitly depends on T017 completion to ensure parameter rows exist. **Algorithm**: read master seed from `data/sweep/master_seed.txt` (create if missing, default = 42); for each parameter combination, assign sequential seeds starting at the master seed and incrementing by 1 for each required simulation iteration. This file serves as the single source of truth for reproducible on‑the‑fly regeneration in later phases.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hypothesis Test Execution and p-Value Collection (Priority: P2)

**Goal**: Apply standard t‑tests and F‑tests to the synthetic null data and collect all resulting p‑values to empirically observe their distribution under violated assumptions.

**Independent Test**: Can be fully tested by running hypothesis tests on a known null dataset and verifying that p‑values are collected for every test without missing values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for t‑test/F‑test execution on null data in `tests/unit/test_stats.py`
- [X] T021 [P] [US2] Integration test for full iteration loop (multiple iterations) without runtime errors in `tests/integration/test_stats.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement data ingestion pipeline in `code/run_tests.py` that **regenerates data on‑the‑fly** using the seeds and parameters from `data/sweep/seed_map.json` and `data/sweep/params.csv`. **Pre‑condition**: both files must exist and pass schema validation. **Dependency**: Explicitly depends on T019b completion. For each iteration, set `np.random.seed(seed_value)` **immediately before** matrix generation to guarantee deterministic correspondence with the original synthetic data. Generate the matrix, run tests, and discard the matrix.
- [X] T023 [P] [US2] Implement `run_hypothesis_tests` function in `code/run_tests.py` (scipy.stats t‑test, F‑test)
- [X] T024 [US2] Implement p‑value collection logic ensuring exactly **p** values per iteration (FR‑) and store in `data/results/pvalues_{seed}.csv`; verify row count equals **p**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - P-Value Distribution Analysis and Deviation Quantification (Priority: P3)

**Goal**: Analyze the collected p‑values using Kolmogorov-Smirnov statistics and QQ-plots against a Gold Standard (permutation-based) reference to quantify anti-conservative bias.

**Independent Test**: Can be fully tested by running the analysis on a fixed dataset and verifying that KS statistics and QQ-plots are produced with correct statistical calculations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for KS statistic calculation against uniform/permutation reference in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for QQ‑plot generation and visual validation in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement permutation test generator in `code/analyze_pvalues.py` (Gold Standard respecting correlation structure). **Dependency**: Explicitly depends on T019b completion. **Deterministic regeneration**: for each seed, set `np.random.seed(seed_value)` **immediately before** generating the matrix (using the same seed map) to ensure the permutation respects the original correlation structure. **Constraint**: Must use the exact same seed sequence as T022 to ensure valid comparison. No raw data files are used.
- [X] T029 [US3] Implement KS statistic calculation comparing standard tests to the permutation reference (FR‑004) and store results in `data/results/ks_stats.json`; each entry must contain the exact KS value.
- [X] T030 [US3] Implement QQ‑plot generation for visual inspection (FR‑005) and save to `docs/plots/qq_{seed}.png`. **Visual Style**: Highlight the point of maximum deviation with a red circle and a text annotation showing the KS value. Verify file existence and non‑emptiness.
- [X] T031 [US3] Implement sensitivity analysis sweep for **ρ** ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}. Output `data/results/sensitivity.csv` with columns `rho,n,p,ks_stat,worst_case_flag`. **Tie-breaking**: If multiple rows share the exact maximum KS for a given rho, select the one with the highest p/n ratio, then highest rho. Set `worst_case_flag` to True for the selected row (FR‑007).
- [X] T032 [US3] Implement bootstrap confidence interval calculation for KS statistics. **Justification**: Constitution Principle VII mandates reporting KS + bootstrap CI. **Storage**: Store only the KS statistic and its 95 % bootstrap CI in `data/results/bootstrap_cis.csv` with columns `seed,n,p,rho,KS_statistic,bootstrap_ci_lower,bootstrap_ci_upper`. Do **not** store raw permutation p‑value arrays to satisfy Data Hygiene (Principle III) and size constraints.

**Checkpoint**: At this point, User Story 3 is complete and all core research outputs are generated.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` including methodology for data generation and analysis. **Must** extract the "worst‑case" scenario from `data/results/sensitivity.csv` and report the exact KS deviation (e.g., "At ρ = 0.9, KS = 0.XX") to satisfy Constitution Principle IV. **Template**: Include a "Validity Breakdown" section calculating the false positive rate (X%) for the standard test vs the permutation test (Y%) at alpha=0.05 for the worst-case scenario. Update `docs/methodology.md` and `docs/results.md`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T019b (seed map)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T019b (seed map) and T022/T024 (p-values)
- **Revision Tasks**: None (Phase 6 removed to prevent scope creep)

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