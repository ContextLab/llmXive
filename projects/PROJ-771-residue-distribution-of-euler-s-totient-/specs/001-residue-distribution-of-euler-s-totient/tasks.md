# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Input**: Design documents from `/specs/001-residue-distribution-of-euler-s-totient/`
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

- [ ] T001a [P] Create `code/` directory (`mkdir -p code`)
- [ ] T001b [P] Create `data/raw/` and `data/processed/` directories (`mkdir -p data/raw data/processed`)
- [ ] T001c [P] Create `results/plots/` and `results/reports/` directories (`mkdir -p results/plots results/reports`)
- [ ] T001d [P] Create `tests/unit/` and `tests/integration/` directories (`mkdir -p tests/unit tests/integration`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `MemoryGuard` class in `code/sieve.py` using `psutil` to enforce a hard limit on memory usage, specifically failing if usage reaches >= 90% of the **configured system limit** (FR-007). **Depends on T005** to ensure the limit is defined.
- [X] T005 [P] Create base configuration loader in `code/run_analysis.py` to handle `N`, prime list `p ∈ {3, 5, 7, 11}`, and the memory limit configuration.
- [X] T007a [P] Initialize random seed pinning in `code/sieve.py` for any deterministic operations
- [X] T007b [P] Initialize random seed pinning in `code/stats.py` for Block Bootstrap and Monte Carlo simulations
- [X] T007c [P] Initialize random seed pinning in `code/visualize.py` for any stochastic visual elements
- [X] T007d [P] Initialize random seed pinning in `code/run_analysis.py` for orchestration-level randomness

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Totient Residues for Large Range (Priority: P1) 🎯 MVP

**Goal**: Generate the sequence of $\phi(n)$ for $n \in [1, N]$ and compute residues modulo $p$ using a linear sieve with arbitrary-precision integers.

**Independent Test**: Run on $N=100$ with $p=3, 5$ and verify output matches known mathematical values for $\phi(n) \pmod p$.

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for linear sieve correctness in `tests/unit/test_sieve.py` (verify $\phi(n)$ against small known values)
- [X] T009 [P] [US1] Unit test for memory guard trigger in `tests/unit/test_sieve.py` (mock memory spike to ensure graceful exit)

### Implementation for User Story 1

- [X] T010 [US1] Implement `compute_phi_linear_sieve(N)` in `code/sieve.py` using Python's native `int` (arbitrary precision) to calculate $\phi(n)$ for all $n \le N$
- [X] T011 [US1] Implement `compute_residues(phi_values, prime)` in `code/sieve.py` to aggregate counts for residue classes $\{0, \dots, p-1\}$
- [X] T012 [US1] Integrate `MemoryGuard` polling inside the sieve loop in `code/sieve.py` to check usage **every [deferred] iterations** or when `psutil.virtual_memory.percent >= 90`, prioritizing the memory limit check (FR-007).
- [ ] T014 [US1] Implement error handling to log specific $n$ if sieve fails or overflow is detected, ensuring this logic executes BEFORE any data save operation (Edge Case: Error Scenario)
- [ ] T013 [US1] Save raw residue counts to `data/raw/residues_{prime}_{N}.json` (JSON serialization of `ResidueDataset`) - **Depends on T014** to ensure error handling runs before save.

**Checkpoint**: After T014 and T013 complete, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Statistical Goodness-of-Fit Tests (Priority: P2)

**Goal**: Apply Block Bootstrap and Chi-squared tests to determine deviation from theoretical bounds, handling dependent data.

**Independent Test**: Feed synthetic biased dataset and verify p-value $< 0.05$; feed uniform dataset and verify p-value $> 0.05$.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test for Block Bootstrap logic in `tests/unit/test_stats.py` (verify resampling of contiguous blocks)
- [X] T016 [P] [US2] Unit test for Chi-squared fallback in `tests/unit/test_stats.py` (verify exact/Monte Carlo switch when expected bin count < 5)

### Implementation for User Story 2

- [X] T017 [US2] Implement `block_bootstrap_residues(residue_sequence, block_size, num_samples)` in `code/stats.py` to generate null distribution for the deviation metric D
- [X] T018 [US2] Implement `check_bin_counts_and_fallback(residue_counts, prime)` in `code/stats.py`: Calculate expected counts $E_k = N/p$ for all $k$. If **any** $E_k < 5$, trigger a fallback to `scipy.stats.chisquare` with `simulation_kwarg=2000` (Monte Carlo) or an exact test. **This task explicitly implements the FR-003 fallback logic and must include a unit test verifying the fallback triggers correctly.**
- [X] T018b [US2] **FR-003 Fallback Implementation**: Implement the specific fallback logic for small bin counts in `code/stats.py`. If `check_bin_counts_and_fallback` (T018) detects any expected bin count < 5, this task ensures the system switches to `scipy.stats.chisquare` with `simulation_kwarg=2000` (Monte Carlo) or an exact test, as mandated by FR-003. **This task must be tested to ensure it triggers correctly when N is small.**
- [ ] T019 [US2] Implement `calculate_chi_squared_statistic_D(observed_counts, expected_counts)` in `code/stats.py` to compute $D = \max_k |O_k - E_k^{theo}|$ where $E_k^{theo} = N/p$. Output D only for use by T020. **Must integrate the fallback logic from T018/T018b.**
- [ ] T019b [US2] **Primary Chi-squared Test**: Implement `run_chi_squared_goodness_of_fit(observed_counts, prime)` in `code/stats.py` to perform the Chi-squared test against the **uniform distribution hypothesis** ($H_0$: uniform) as required by FR-003 and US-2. This task must calculate the standard $\chi^2$ statistic and p-value (using the fallback from T018/T018b if needed) and output a `StatisticalResult` object.
- [ ] T020 [US2] **Block Bootstrap Deviation Test**: Integrate Block Bootstrap p-value calculation: compare $D_{obs}$ (from T019) against the bootstrap distribution (from T017) to compute the final p-value. **Explicitly define $E_k^{theo}$ as $N/p$ (uniform expectation)**. This test addresses the dependence structure as per the Plan's methodology.
- [ ] T027a [US2] Implement theoretical error bound calculations in `code/stats.py` using the following specific formulas from literature: 1) Lebowitz-Lockard bound: $E_{bound} = C \cdot N^{1 - 1/\phi(p)}$; 2) Pollack & Roy bound: $O(N \cdot \exp(-c \cdot \sqrt{\log N}))$. Implement these as constants/functions for use in T027. **Do not perform external research; use these formulas directly as asserted in the Plan.**
- [ ] T022 [US2] Implement the primary pass/fail flag logic in `code/stats.py` based on the standard $\alpha = 0.05$ threshold as required by FR-006. This task must output a binary flag based strictly on the p-value from T020 compared to 0.05.
- [ ] T022b [US2] Implement Bonferroni-corrected sensitivity analysis in `code/stats.py` to determine a secondary pass/fail flag using $\alpha_{adj} = 0.05/4$. This task addresses the multiple testing concern without violating FR-006.
- [ ] T021 [US2] Save statistical results to `data/processed/stats_{prime}_{N}.json` (JSON serialization of `StatisticalResult`) including the standard pass/fail flag (from T022) and Bonferroni flag (from T022b). **Depends on T020** for p-values and D statistic, **T022**, and **T022b**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize and Compare Against Theoretical Bounds (Priority: P3)

**Goal**: Generate bar plots and QQ-plots comparing observed frequencies to uniform expectation and annotated theoretical error bounds.

**Independent Test**: Generate plots for $p=5$ and verify "Uniform Expectation" line is at $N/5$ and error bounds are annotated.

### Tests for User Story 3

- [ ] T023 [P] [US3] Unit test for plot generation in `tests/unit/test_visualize.py` (verify image file creation and dimensions)
- [ ] T024 [P] [US3] Integration test for full report generation in `tests/integration/test_pipeline.py` (verify all artifacts created)

### Implementation for User Story 3

- [ ] T025 [US3] Implement `plot_bar_frequencies(residue_counts, prime)` in `code/visualize.py` to create bar plots with $N/p$ reference line. **Must load data from `data/raw/residues_{prime}_{N}.json`**.
- [ ] T026 [US3] Implement `plot_residual_qq(residuals)` in `code/visualize.py` to generate QQ-plots for $\chi^2$ residuals
- [ ] T027 [US3] Implement `annotate_theoretical_bounds(plot, prime)` in `code/visualize.py` to overlay error bounds using formulas defined in T027a. **Must load data from `data/raw/residues_{prime}_{N}.json` and `data/processed/stats_{prime}_{N}.json`** to compare observed vs theoretical.
- [ ] T028 [US3] Generate summary report in `results/reports/summary_{N}.md` containing test statistics, p-values, and pass/fail flags (FR-006)
- [ ] T029 [US3] Ensure all output images are saved as PNG with high resolution (DPI equivalent) in `results/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Add `quickstart.md` with execution instructions for $N=5,000,000$
- [ ] T031 Code cleanup: Refactor `run_analysis.py` to ensure clean separation of orchestration logic
- [ ] T032a [P] Add timing instrumentation and logging to the sieve loop in `code/sieve.py` to measure execution time per [deferred] iterations.
- [ ] T032b [P] Run the benchmark on $N=5,000,000$ and record the total wall-clock time and memory peak to `results/reports/benchmark_N5M.json` (Target: < 1 hour).
- [ ] T033 [P] Add `pytest` integration test for full pipeline in `tests/integration/test_pipeline.py`
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility on fresh environment

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (residue data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (statistical results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core algorithms (sieve, stats) before visualization
- Data generation before analysis
- Analysis before reporting

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for linear sieve correctness in tests/unit/test_sieve.py"
Task: "Unit test for memory guard trigger in tests/unit/test_sieve.py"

# Launch all models for User Story 1 together:
Task: "Implement compute_phi_linear_sieve(N) in code/sieve.py"
Task: "Implement compute_residues(phi_values, prime) in code/sieve.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify $\phi(n)$ values)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Statistical Analysis)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualization)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Sieve & Data)
 - Developer B: User Story 2 (Stats & Bootstrap)
 - Developer C: User Story 3 (Visualization & Reports)
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
- **Critical**: Ensure `code/sieve.py` uses Python's native `int` (arbitrary precision) as per Constitution Principle VI.
- **Critical**: Ensure `code/stats.py` implements Block Bootstrap to handle sequence dependence, not simple i.i.d. bootstrapping.
- **Critical**: {{claim:c_0c7700eb}} (golden_ratio, https://en.wikipedia.org/wiki/Golden_ratio); optimize sieve loop if necessary.
- **Critical**: T018/T018b implements the fallback logic for small bin counts (FR-003) and includes a test.
- **Critical**: T019b implements the Spec-mandated Chi-squared test against uniform distribution.
- **Critical**: T020 implements the Plan-mandated Block Bootstrap deviation test.
- **Critical**: T027a implements the error bound formulas directly without external research.
- **Critical**: T022 implements the FR-006 standard alpha=0.05 flag.
- **Critical**: T022b implements the Bonferroni correction as a secondary sensitivity analysis.
- **Critical**: T013 depends on T014 (Error handling) to ensure data integrity before saving.
- **Critical**: T021 depends on T020 for p-values and D statistics.