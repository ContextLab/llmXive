# Tasks: Exploring the Distribution of Smooth Numbers in Short Intervals

**Input**: Design documents from `/specs/001-exploring-the-distribution-of-smooth-numbers/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001 Create project structure per implementation plan: `projects/PROJ-549-exploring-the-distribution-of-smooth-num/` with `code/`, `data/`, `tests/`, `state/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing `numpy`, `scipy`, `matplotlib`, `pytest`
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/dickman.py`: Numerical solver for the Dickman function $\rho(u)$ via integration of the delay-differential equation (Tenenbaum method)
- [X] T005 [P] Create `code/utils.py`: Helper functions for logging, checksum generation, and deterministic random seed management
- [X] T006 Create `code/config.py`: Configuration loader for parameter grids ($x, y, h$) and CI constraints (RAM limits, timeouts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Validate Prime Sieve Data (Priority: P1) 🎯 MVP

**Goal**: Implement a memory-safe segmented sieve to generate all primes up to $10^9$ for use in factorization.

**Independent Test**: Execute the sieve script in isolation; verify output count matches $\pi(10^9) = 50,847,534$ within 1 second; verify peak memory < 4 GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for sieve boundary conditions in `tests/test_sieve.py`: Implement `test_sieve_empty_interval` (range [1,1] returns 0), `test_sieve_single_prime` (range [2,2] returns 1), and `test_sieve_boundary_1e9` (range [1e9, 1e9] checks primality).
- [X] T011 [P] [US1] Integration test for prime count verification in `tests/test_sieve.py`: Implement `test_prime_count_exact` asserting `50847534` and `test_sieve_runtime` asserting `runtime_seconds < 7200` (120 minutes).

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/sieve.py`: Segmented Sieve of Eratosthenes with a memory cap, writing output to `data/primes_1e9.csv`. **Must include**: Progress logging, runtime measurement, and a final check that loads the expected count from a verified constant (50,847,534) and asserts the generated count matches it. If runtime exceeds a predefined threshold, log a warning but do not crash. (per Spec feasibility measurement intent).
- [ ] T013 [US1] Implement and run `code/validate_sieve.py`: A separate script to verify the generated prime list from `data/primes_1e9.csv`. **Requirement**: Verify each prime against a known prime database or a secondary deterministic check (not self-referential trial division) to confirm [deferred] certainty of primality. **Output**: A checksum and a boolean flag indicating `validation_passed`. **Dependency**: Must complete after T012 (produces artifact) and before T020 (consumes validated artifact).
- [X] T014 [US1] Add CLI entry point in `code/main.py` to trigger sieve generation with progress logging.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Smooth Number Density Across Parameter Grid (Priority: P2)

**Goal**: Enumerate integers in short intervals $[x, x+h]$ across the Spec-defined grid to calculate $y$-smooth densities using the deviation ratio method.

**Independent Test**: Run on a small fixed subset ($x=10^6, y=100$); verify count matches brute-force calculation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for smoothness classification logic in `tests/test_smoothness.py`: Implement `test_factor_all_smaller_y` (returns True), `test_factor_larger_y` (returns False), and `test_empty_interval_count` (returns 0).
- [X] T019 [P] [US2] Integration test for density calculation in `tests/test_smoothness.py`: Implement `test_density_small_interval` with parameters $x=10^6, y=100, h=1000$. Verify count matches brute-force ground truth.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/smoothness.py`: Factorization logic using trial division against primes $\le y$ from `data/primes_1e9.csv`. **Dependency**: Must wait for T012 AND T013 (validated prime list).
- [X] T021 [US2] Implement `code/smoothness.py`: Interval enumeration loop that handles edge cases (empty intervals, $x+h > 10^9$) without crashing. **Dependency**: Must wait for T012 AND T013.
- [X] T022 [US2] Implement `code/smoothness.py`: Aggregation logic to compute density $\rho = \text{count}/h$ and deviation ratio $R = \rho_{obs} / \rho_{Dickman}(u)$ for Multiple random starting positions per configuration. **Dependency**: Must wait for T012, T013, AND T004 (Dickman function).
- [ ] T023 [US2] Implement `code/main.py` orchestration to run the **Spec-defined grid**: $y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$, with interval lengths $h \in \{x^{0.1}, x^{0.3}, x^{0.5}, x^{0.7}, x^{0.9}\}$. This run computes the deviation ratio $R$ as the primary scientific output. Save all results to `data/density_measurements.csv`. **Dependency**: Must wait for T012 AND T013.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization of Density Trends (Priority: P3)

**Goal**: Fit power-law models to the observed density data, perform Chi-Square (Spec) and KS (Plan) tests, and generate visualizations.

**Independent Test**: Run analysis on synthetic data with known $\beta$; verify regression recovers $\beta$ within margin.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for WLS regression implementation in `tests/test_analysis.py`: Implement `test_wls_recovery` using synthetic data: 10 points, slope=2.0, noise=0.1. Assert `abs(beta_estimated - 2.0) < 0.05 `.
- [X] T025 [P] [US3] Unit test for Chi-Square test logic in `tests/test_analysis.py`: Implement `test_chi_square_logic` with synthetic observed/expected counts. Assert p-value is calculated and within expected range.

### Implementation for User Story 3

- [ ] T026a [US3] Implement `code/analysis.py`: **Spec-Baseline** Power-law regression to fit $\rho = c \cdot h^\beta$ (raw density) for each $y$-group. This serves as a comparative baseline but is NOT the primary scientific conclusion. (Satisfies FR-004). **Dependency**: Must wait for T023.
- [ ] T026b [US3] Implement `code/analysis.py`: **Plan-Exploratory** Power-law regression to fit $R \propto h^\beta$ (deviation ratio) for each $y$-group. This is an exploratory output per the Plan. **Dependency**: Must wait for T023 AND T004.
- [ ] T027a [US3] Implement `code/analysis.py`: **Spec-Required** Chi-Square Goodness-of-Fit test comparing observed counts vs. Dickman expectations. **Method**: Bin the interval data into k bins, calculate expected counts using Dickman(u) * h for each bin, and compute p-values. Output to `data/model_fits.json`. This is the mandatory deliverable for FR-005. (Satisfies FR-005, SC-002). **Dependency**: Must wait for T023.
- [ ] T027b [US3] Implement `code/analysis.py`: **Plan-Exploratory** Kolmogorov-Smirnov (KS) test comparing observed vs. Dickman distributions. This is an exploratory test per Plan Principle VII. (Satisfies Plan Principle VII). **Dependency**: Must wait for T023 AND T004.
- [ ] T028 [US3] Implement `code/viz.py`: Generate density vs. interval length plots with 95% confidence intervals and theoretical curves; save to `data/` as PNG. **Dependency**: Must wait for T026/T027.
- [ ] T029 [US3] Implement `code/main.py` to orchestrate analysis, saving BOTH raw density and deviation ratio fits, and BOTH KS and Chi-Square p-values to `data/model_fits.json`. **Dependency**: Must wait for T023.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior research-stage reviews

- [ ] T030 [P] **Visualization Annotation**: Update `code/viz.py` to add specific text annotations at coordinates (x,y) for each plot indicating "Associational Trend Only" (per Spec Assumptions). Update `code/analysis.py` docstrings to explicitly state "Correlation does not imply causation".
- [ ] T031 [P] Documentation updates in `docs/` explaining the methodology and dual-test approach (Chi-Square + KS).
- [ ] T032a [P] **Performance Profiling**: Profile `code/smoothness.py` loop using `cProfile` to establish a baseline measurement of per-interval processing overhead. **Output**: A detailed profiling report identifying bottlenecks.
- [ ] T032b [P] **Performance Optimization**: Implement vectorized factorization using `numpy` broadcasting on the factorization loop. **Target**: Reduce per-interval processing overhead by at least 50% compared to the baseline measured in T032a.
- [ ] T033 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility on CI.
- [ ] T034 [P] **Narrative Contextualization**: Update `code/viz.py` and `docs/research.md` to explicitly frame short intervals $[x, x+h]$ as "Snapshot of Prime Density". Add a caption referencing the "forest density" metaphor to elevate the interpretation from pure calculation to a story of number distribution. **Dependency**: Must wait for T028 (visualization generation).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **CRITICAL**: User Stories are SEQUENTIAL due to data dependencies:
 - US1 (Sieve) -> US2 (Density) -> US3 (Analysis).
 - US2 tasks (T020-T023) CANNOT start until T012 (US1) produces `data/primes_1e9.csv` AND T013 validates it.
 - US3 tasks (T026-T029) CANNOT start until T023 (US2) produces `data/density_measurements.csv`.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: **STRICT DEPENDENCY** on US1 (needs `data/primes_1e9.csv` AND validation from T013).
- **User Story 3 (P3)**: **STRICT DEPENDENCY** on US2 (needs `data/density_measurements.csv`) and US1 (for Dickman function context).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Logic before orchestration
- Core implementation before integration
- Story complete before moving to next priority
- **Note on Parallelism**: Within a User Story, sub-tasks (e.g., T026a and T026b) marked [P] can run in parallel if they operate on the same input artifact and do not depend on each other's output. However, T020, T021, T022, and T023 are sequentially dependent on the output of T012 and T013 and must be executed in order.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- **User Stories CANNOT run in parallel** with each other due to data flow (US1 -> US2 -> US3).
- Within a User Story, sub-tasks (e.g., T026a and T026b) marked [P] can run in parallel if they operate on the same input artifact.

---

## Parallel Example: User Story 3

```bash
# Launch parallel sub-tasks within US3 (after T023 completes):
Task: "Implement T026a (Raw Density Regression - Baseline)"
Task: "Implement T026b (Deviation Ratio Regression - Exploratory)"
Task: "Implement T027a (Chi-Square Test - Spec Required)"
Task: "Implement T027b (KS Test - Plan Exploratory)"
# These can run in parallel as they all consume T023 output.
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

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Sieve).
 - Developer B: **Wait** for T012 completion, then start User Story 2 (Density).
 - Developer C: **Wait** for T023 completion, then start User Story 3 (Analysis).
 - *Note: Due to data dependencies, US2 and US3 cannot start until their predecessors finish.*

---

## Notes

- [P] tasks = different files, no dependencies (within the same phase/artifact set).
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Critical**: Ensure `code/dickman.py` is implemented accurately as it is the theoretical baseline for US2 and US3.
- **Critical**: Ensure `code/smoothness.py` handles the "empty interval" edge case by recording density 0.0 as per spec.
- **Critical**: Ensure `code/analysis.py` implements BOTH Chi-Square (Spec/FR-005) and KS (Plan) tests to satisfy FR-005 and Plan Principle VII, with clear labeling of Spec-Required vs Plan-Exploratory.
- **Critical**: Task T012 must enforce the 120-minute runtime constraint via warning log, not hard crash.
- **Critical**: Task T030 must strictly adhere to "associational" framing as per Spec Assumptions.
- **Critical**: Task T013 MUST use deterministic verification against an external source, not self-referential, to satisfy Constitution Principle VI.
- **Critical**: Task T034 must explicitly integrate the "Snapshot of Prime Density" framing to elevate the scientific interpretation without poetic ambiguity.