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

- [ ] T001a Create `code/` directory (`mkdir -p code`)
- [ ] T001b Create `data/raw/` and `data/processed/` directories (`mkdir -p data/raw data/processed`)
- [ ] T001c Create `results/plots/` and `results/reports/` directories (`mkdir -p results/plots results/reports`)
- [ ] T001d Create `tests/unit/` and `tests/integration/` directories (`mkdir -p tests/unit tests/integration`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create base configuration loader in `code/config.py`. Implement `load_config()` function returning a dictionary with these exact keys: `N` (int, default 1000000), `primes` (list of int, default [3, 5, 7, 11]), `memory_limit_mb` (int, default 6000), `seed` (int, default 42), and `memory_check_interval` (int, default 10000). Defaults must be defined in code but overridable via environment variables or CLI args.
- [X] T004 [P] Implement `MemoryGuard` class in `code/sieve.py` using `psutil` to enforce a hard limit on memory usage. **Depends on T005**: The limit must be read from `config['memory_limit_mb']` (the key defined in T005). Fail gracefully if usage reaches >= 90% of this configured limit (FR-007).
- [X] T007 [P] Implement global random seed pinning in `code/run_analysis.py`. **Depends on T005**: Set `numpy.random.seed`, `random.seed`, and any other RNG seeds using `config['seed']` at the entry point of `run_analysis.py` to ensure deterministic execution for all stochastic operations (Block Bootstrap, Monte Carlo).
- [X] T008 [P] [US1] Unit test for linear sieve correctness in `tests/unit/test_sieve.py` (verify $\phi(n)$ against small known values)
- [X] T009 [P] [US1] Unit test for memory guard trigger in `tests/unit/test_sieve.py` (mock memory spike to ensure graceful exit)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Totient Residues for Large Range (Priority: P1) 🎯 MVP

**Goal**: Generate the sequence of $\phi(n)$ for $n \in [1, N]$ and compute residues modulo $p$ using a linear sieve with arbitrary-precision integers.

**Independent Test**: Run on $N=100$ with $p=3, 5$ and verify output matches known mathematical values for $\phi(n) \pmod p$.

### Implementation for User Story 1

- [X] T010 [US1] Implement `compute_phi_linear_sieve(N)` in `code/sieve.py` using Python's native `int` (arbitrary precision) to calculate $\phi(n)$ for all $n \le N$.
- [X] T011 [US1] Implement `compute_residues(phi_values, prime)` in `code/sieve.py` to aggregate counts for residue classes $\{0, \dots, p-1\}$.
- [ ] T014 [US1] Implement error handling to log specific $n$ if sieve fails or overflow is detected, ensuring this logic executes BEFORE any data save operation (Edge Case: Error Scenario).
- [X] T012 [US1] Integrate `MemoryGuard` polling inside the sieve loop in `code/sieve.py` to check usage **every 10000 iterations** (default from T005) or when `psutil.virtual_memory.percent >= 90`, prioritizing the memory limit check (FR-007).
- [ ] T013 [US1] Save raw residue counts to `data/raw/residues_{prime}_{N}.json` (JSON serialization of `ResidueDataset`) - **Depends on T014** to ensure error handling runs before save.

**Checkpoint**: After T014 and T013 complete, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Statistical Goodness-of-Fit Tests (Priority: P2)

**Goal**: Apply BOTH Chi-squared/Exact tests (per Spec FR-003/FR-004) AND Block Bootstrap (per Plan) to determine deviation from theoretical bounds.

**Independent Test**: Feed synthetic biased dataset and verify p-value $< 0.05$; feed uniform dataset and verify p-value $> 0.05$.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test for Block Bootstrap logic in `tests/unit/test_stats.py` (verify resampling of contiguous blocks)
- [X] T016 [P] [US2] Unit test for Chi-squared fallback in `tests/unit/test_stats.py` (verify exact/Monte Carlo switch when expected bin count < 5)

### Implementation for User Story 2

- [~] T027a [US2] Implement theoretical error bound calculations in `code/constants.py` and `code/stats.py` using the formulas from literature (Lebowitz-Lockard, Pollack & Roy). **Define constants (C, c, δ) as configurable parameters in `constants.py`**. **STRICT CONSTRAINT**: Hard-coded placeholders are FORBIDDEN. If constants are missing from `data-model.md` or `research.md`, the task MUST fail with a clear error message directing the implementer to retrieve the specific values from the cited primary sources (Lebowitz-Lockard 2021; Pollack & Roy 2024) before coding. This is required to satisfy Constitution Principle II (Verified Accuracy). <!-- FAILED: unspecified -->
- [X] T018a [US2] Implement threshold logic in `code/stats.py` to determine when to switch to Block Bootstrap (e.g., if $N < 100$ or expected bin count $< 5$). **This task explicitly defines the trigger for the fallback mechanism required by FR-003 and the Plan.**
- [X] T018c [US2] Implement `exact_test_fallback(residue_counts, prime)` in `code/stats.py`: If any expected bin count $< 5$, compute the exact p-value using a multinomial test or Monte Carlo simulation of the null distribution (non-circular, using the specific observed counts). **This satisfies FR-003 requirement for 'exact test' fallback.**
- [ ] T018b [US2] Implement `calculate_chi_squared_statistic(residue_counts, prime)` in `code/stats.py`: Calculate expected counts $E_k = N/p$. Compute $\chi^2 = \sum (O_k - E_k)^2 / E_k$ and the standard asymptotic p-value. **This satisfies FR-004 requirement for the Chi-squared statistic and MUST be reported in the final results.**
- [ ] T018 [US2] Implement `check_bin_counts_and_fallback(residue_counts, prime)` in `code/stats.py`: Calculate expected counts $E_k = N/p$ for all $k$. If **any** $E_k < 5$ or $N$ is below the threshold (from T018a), trigger the **Exact Test** (T018c) or Block Bootstrap (T017) as appropriate.
- [ ] T017 [US2] Implement `block_bootstrap_residues(residue_sequence, block_size, num_samples)` in `code/stats.py` to generate null distribution for the deviation metric D.
- [ ] T019 [US2] Implement `calculate_deviation_metric_D(observed_counts, prime)` in `code/stats.py` to compute $D = \max_k |O_k - E_k^{theo}|$ where $E_k^{theo}$ is the **error-bound-adjusted theoretical expectation** (derived from formulas in T027a). Output D only for use by T019b. **Must integrate the fallback logic from T018. Depends on T027a.**
- [ ] T019b [US2] **Supplementary Deviation Test (Block Bootstrap)**: Implement `run_deviation_test(observed_counts, prime)` in `code/stats.py`. Compare $D_{obs}$ (from T019) against the bootstrap distribution (from T017). Calculate the p-value as the proportion of bootstrap samples where D_boot >= D_obs. **This test addresses the dependence structure as per the Plan's methodology but is supplementary to the primary Chi-squared test (T018b) required by FR-004. Both tests must be reported.** **Depends on T017, T019, T027a.**
- [ ] T020 [US2] **Error Term Residual Calculation**: Implement `calculate_error_term_residual(D_obs, E_bound)` in `code/stats.py` to compute the ratio of observed deviation to predicted error bound ($D_{obs} / E_{bound}$). **Depends on T027a** for the error bound formula/constants (which define $E_{bound}$). **This metric is a primary result required by the Plan's Statistical Methodology.** **Depends on T019b.**
- [ ] T022 [US2] Implement the primary pass/fail flag logic in `code/stats.py` based on the standard $\alpha = 0.05$ threshold as required by FR-006. This task must output a binary flag based strictly on the p-value from T018b (Chi-squared) compared to 0.05.
- [ ] T022b [US2] Implement Bonferroni-corrected sensitivity analysis in `code/stats.py` to determine a secondary pass/fail flag using $\alpha_{adj} = 0.05/4$. This task addresses the multiple testing concern without violating FR-006.
- [ ] T021 [US2] Save statistical results to `data/processed/stats_{prime}_{N}.json` (JSON serialization of `StatisticalResult`) including: Chi-squared statistic and p-value (from T018b), Exact test p-value (from T018c), Block Bootstrap p-value (from T019b), Error term residual (from T020), and pass/fail flags (from T022, T022b). **Depends on T018b, T018c, T019b, T020, T022, T022b.**

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
- [ ] T026 [US3] Implement `plot_residual_qq(residuals)` in `code/visualize.py` to generate QQ-plots. **Must use Chi-squared residuals** calculated as $(O_k - E_k) / \sqrt{E_k}$ derived from the Chi-squared test (T018b). **Depends on T018b.**
- [ ] T027 [US3] Implement `annotate_theoretical_bounds(plot, prime)` in `code/visualize.py` to overlay error bounds using formulas defined in T027a. **Must load data from `data/raw/residues_{prime}_{N}.json` and `data/processed/stats_{prime}_{N}.json`** to compare observed vs theoretical. **Depends on T027a.**
- [ ] T028 [US3] Generate summary report in `results/reports/summary_{N}.md` containing test statistics, p-values, and pass/fail flags (FR-006)
- [ ] T028b [US3] **Generate Visualization Report (FR-004)**: Generate a **Markdown** report in `results/reports/` containing the Chi-squared test statistic, p-value, degrees of freedom, Block Bootstrap p-value, and error term residual as required by FR-004 and the Plan. **Depends on T021** for stats data (including error term residual).
- [ ] T029 [US3] Ensure all output images are saved as PNG with high resolution (DPI equivalent) in `results/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Add `quickstart.md` with execution instructions for $N=5,000,000$
- [ ] T031 [P] Code cleanup: Refactor `run_analysis.py` to ensure clean separation of orchestration logic
- [ ] T032a [P] Add timing instrumentation and logging to the sieve loop in `code/sieve.py` to measure execution time per 10000 iterations.
- [ ] T032b [P] Run the benchmark on $N=5,000,000$ and record the total wall-clock time and memory peak to `results/reports/benchmark_N5M.json` (Target: < 1 hour).
- [ ] T033 [P] Add `pytest` integration test for full pipeline in `tests/integration/test_pipeline.py`
- [ ] T034 [P] Run `quickstart.md` validation to ensure reproducibility on fresh environment

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
- **Critical**: Ensure `code/stats.py` implements Block Bootstrap to handle sequence dependence, not simple i.i.d. bootstrapping, BUT ALSO implements the required Chi-squared test (FR-003/FR-004).
- **Critical**: T018 implements the fallback logic for small bin counts (FR-003) aligned with the Plan's Block Bootstrap methodology.
- **Critical**: T018b calculates the primary Chi-squared statistic required by FR-004.
- **Critical**: T019b implements the Plan-mandated deviation test against theoretical bounds as a supplementary test.
- **Critical**: T027a implements the error bound formulas using constants from `constants.py` (derived from `data-model.md`/`research.md`). **Hard-coded placeholders are FORBIDDEN.**
- **Critical**: T022 implements the FR-006 standard alpha=0.05 flag based on the Chi-squared test.
- **Critical**: T022b implements the Bonferroni correction as a secondary sensitivity analysis.
- **Critical**: T013 depends on T014 (Error handling) to ensure data integrity before saving.
- **Critical**: T021 depends on T018b, T018c, T019b, T020, T022, and T022b for p-values, residuals, and flags.
- **Critical**: T020 depends on T019b for the deviation metric and T027a for error bound formulas.
- **Critical**: T028b depends on T021 for statistical results.
- **Critical**: T027 (Phase 5) depends on T027a (Phase 4).
- **Critical**: T026 depends on T018b for Chi-squared residuals.
- **Critical**: Both Chi-squared (T018b) and Block Bootstrap (T019b) must be calculated and reported to satisfy both Spec and Plan requirements.