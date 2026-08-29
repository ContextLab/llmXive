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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: Execute `mkdir -p code data tests state docs` and `touch code/__init__.py code/requirements.txt code/config.py tests/__init__.py`. Ensure all directories (`code`, `data`, `tests`, `state`, `docs`) exist before proceeding.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing `numpy`, `scipy`, `matplotlib`, `pytest`, `sympy`.
- [X] T003 [P] Configure linting and formatting: Create `.flake8` with content `[flake8] max-line-length = 100` and `pyproject.toml` with sections `[tool.black] line-length = 100 target-version = ['py311']` and `[tool.pytest]`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/dickman.py`: Numerical solver for the Dickman function $\rho(u)$ via integration of the delay-differential equation (Tenenbaum method). **Requirement**: Use `scipy.integrate.odeint` with tolerance `rtol=1e-6`, `atol=1e-9`.
- [X] T005 [P] Create `code/utils.py`: Helper functions for logging, checksum generation, and deterministic random seed management.
- [X] T006 Create `code/config.py`: Configuration loader for parameter grids ($x, y, h$) and CI constraints (RAM limits, timeouts).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Validate Prime Sieve Data (Priority: P1) 🎯 MVP

**Goal**: Implement a memory-safe segmented sieve to generate all primes up to $10^9$ for use in factorization.

**Independent Test**: Execute the sieve script in isolation; verify output count matches $\pi(10^9) = 50,847,534$ within 1 second; verify peak memory < 4 GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for sieve boundary conditions in `tests/test_sieve.py`: Implement `test_sieve_empty_interval` (range [1,1] returns 0), `test_sieve_single_prime` (range [2,2] returns 1), and `test_sieve_boundary_1e9` (range [1e9,1e9] checks primality).
- [X] T011 [P] [US1] Integration test for prime count verification in `tests/test_sieve.py`: Implement `test_prime_count_exact` asserting `len(primes) == 50847534` (verified value for $\pi(10^9)$) and `test_sieve_runtime` asserting `runtime_seconds < 7200` (120 minutes).

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/sieve.py`: Segmented Sieve of Eratosthenes with a memory cap. **Requirements**:
 1. Implement a hard runtime cap using `signal.SIGALRM` (with `threading.Timer` fallback for non-POSIX) set to 115 minutes.
 2. **Checkpoint Logic**: On timeout or memory limit, write a JSON checkpoint file to `data/checkpoint.json` with schema: `{"segment_index": int, "last_prime": int, "timestamp": "ISO8601"}`. Resume from this file on next run.
 3. Monitor peak memory usage (e.g., `psutil`) and log if it exceeds a predefined threshold.
 4. Perform a self-check: verify `last_prime < 10^9` and `len(set(primes)) == len(primes)` before writing.
 5. Output to `data/primes_1e9.csv` (one prime per line).
 **Dependency**: None.
- [ ] T013 [US1] Implement and run `code/validate_sieve.py`: A separate script to verify the generated prime list from `data/primes_1e9.csv`. **Requirements**: <!-- ATOMIZE: requested -->
 1. **DO NOT** use self-referential trial division (circular logic).
 2. Verify total count aligns with the expected theoretical magnitude.
 3. **Spot Check**: Sample a representative subset of primes from the list. using **stratified sampling** (evenly spaced indices) with a fixed seed (e.g., `seed=42`). Verify each sampled prime `p` using `sympy.isprime(p)` (an independent, deterministic library) to ensure primality.
 4. Output a JSON report to `data/sieve_validation_report.json` with schema: `{"count": int, "sample_size": 10000, "all_valid": bool, "checksum": str, "timestamp": str}`.
 5. The script must exit with code 0 only if `all_valid` is true and `count` matches.
 **Dependency**: Must complete after T012 (produces artifact).
- [X] T014 [US1] Add CLI entry point in `code/main.py` to trigger sieve generation with progress logging. **Dependency**: Must complete after T012 AND T013 to ensure the CLI only runs on validated data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Smooth Number Density Across Parameter Grid (Priority: P2)

**Goal**: Enumerate integers in short intervals $[x, x+h]$ across BOTH the Spec-defined and Plan-defined grids to calculate $y$-smooth densities. This dual-grid approach is required to satisfy Spec FR-002 (Baseline) and Plan SC-004 (Variance Analysis).

**Independent Test**: Run on a small fixed subset ($x=10^6, y=100$); verify count matches brute-force calculation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for smoothness classification logic in `tests/test_smoothness.py`: Implement `test_factor_all_smaller_y` (returns True), `test_factor_larger_y` (returns False), and `test_empty_interval_count` (returns 0).
- [X] T019 [P] [US2] Integration test for density calculation in `tests/test_smoothness.py`: Implement `test_density_small_interval` with parameters $x=10^6, y=100, h=1000$. Verify count matches brute-force ground truth.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/smoothness.py`: Factorization logic using trial division against primes $\le y$ from `data/primes_1e9.csv`. **Dependency**: Must wait for T012 AND T013 (validated prime list).
- [X] T021 [US2] Implement `code/smoothness.py`: Interval enumeration loop that handles edge cases (empty intervals, $x+h > 10^9$) without crashing. **Dependency**: Must wait for T012 AND T013.
- [X] T022 [US2] Implement `code/smoothness.py`: Aggregation logic to compute density $\rho = \text{count}/h$ and deviation ratio $R = \rho_{obs} / \rho_{Dickman}(u)$ for **50** random starting positions per configuration. **Dependency**: Must wait for T012, T013, AND T004 (Dickman function).
- [X] T023 [US2] Implement `code/main.py` orchestration to run **TWO** distinct parameter sweeps. **Justification**: The Spec grid satisfies FR-002; the Plan grid satisfies SC-004 (Variance analysis) and the Plan's methodological revision.
 1. **Spec-Defined Grid (Baseline)**: $y \in \{100, 1000, 10000 (OEIS A114856, https://oeis.org/A114856)\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$, with $h \in \{x^{0.1}, x^{0.3}, x^{0.5}, x^{0.7}, x^{0.9}\}$. Save results to `data/density_measurements_spec.csv` with a `source` column set to 'spec'. **Multiple random starts per configuration**.
 2. **Plan-Defined Grid (Variance Analysis)**: $y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$, with **fixed interval lengths** $h \in \{10^3, 10^4, 10^5, 10^6\}$. Save results to `data/density_measurements_plan.csv` with a `source` column set to 'plan'. **Multiple random starts per configuration**.
 **Dependency**: Must wait for T012 AND T013.
- [ ] T023b [US2] **Verify Grid Generation**: Validate the output of T023. **Requirements**:
 1. Confirm `data/density_measurements_spec.csv` and `data/density_measurements_plan.csv` exist.
 2. Verify non-zero row counts for both files.
 3. Verify the `source` column contains exactly 'spec' and 'plan' values respectively.
 4. Verify the schema matches the expected columns (x, y, h, start_offset, count, density, ratio).
 5. Output `grid_verification.json` with status `{"spec_valid": bool, "plan_valid": bool}`.
 **Dependency**: Must wait for T023.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization of Density Trends (Priority: P3)

**Goal**: Fit power-law models to the observed density data (both grids), perform BOTH Chi-Square (Spec) and KS (Plan) tests, and generate visualizations.

**Independent Test**: Run analysis on synthetic data with known $\beta$; verify regression recovers $\beta$ within margin.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for WLS regression implementation in `tests/test_analysis.py`: Implement `test_wls_recovery` using synthetic data: 10 points, slope=2.0, noise=0.1. Assert `abs(beta_estimated - 2.0) < 0.05 `.
- [X] T025 [P] [US3] Unit test for Chi-Square test logic in `tests/test_analysis.py`: Implement `test_chi_square_logic` with synthetic observed/expected counts. Assert p-value is calculated and within expected range.

### Implementation for User Story 3

- [X] T026a [P] [US3] Implement `code/analysis.py`: **Plan-Primary (Exploratory)** Power-law regression to fit $R \propto h^\beta$ (deviation ratio) for each $y$-group using the Plan-defined grid (`density_measurements_plan.csv`). **Note**: This metric has no Spec-defined success threshold (SC-001 applies to raw density). (Satisfies Plan Summary). **Dependency**: Must wait for T023 AND T004.
- [X] T026b [P] [US3] Implement `code/analysis.py`: **Spec-Mandatory (Baseline)** Power-law regression to fit $\rho = c \cdot h^\beta$ (raw density) for each $y$-group using the Spec-defined grid (`density_measurements_spec.csv`). This satisfies FR-004 and SC-001. **Dependency**: Must wait for T023.
- [X] T027a [P] [US3] Implement `code/analysis.py`: **Plan-Primary (Additional)** Kolmogorov-Smirnov (KS) test comparing observed vs. Dickman distributions for the Plan-defined grid. This is an additional requirement per Plan Principle VII. (Satisfies Plan Principle VII). **Dependency**: Must wait for T023 AND T004.
- [X] T027b [P] [US3] Implement `code/analysis.py`: **Spec-Mandatory (Baseline)** Chi-Square Goodness-of-Fit test comparing observed counts vs. Dickman expectations for the Spec-defined grid. **Method**:
 1. Input: `data/density_measurements_spec.csv`.
 2. **Binning**: Bin on **observed density values**. Use Sturges' rule to determine number of bins $k = \lceil 1 + \log_2(N) \rceil$.
 3. **Merge Strategy**: If any bin has expected count < 5, merge adjacent bins, prioritizing the bins with the **lowest expected counts**, until all bins have expected count >= 5.
 4. Calculate expected counts for each bin: $E_i = \sum (\rho_{Dickman}(u) \cdot h \cdot \text{bin\_width})$.
 5. Compute $\chi^2$ statistic and p-value.
 6. Output: Write `chi_square_p_value` to `data/model_fits.json`.
 **Note**: This test satisfies FR-005 and is mandatory. **Dependency**: Must wait for T023.
- [X] T028 [US3] Implement `code/viz.py`: Generate density vs. interval length plots with confidence intervals and theoretical curves for BOTH grids; save to `data/` as PNG. **Requirement**: Generate captions directly from the data (e.g., "Observed: {rho}, Expected: {exp}, p={p}") and save as text next to the image. **Dependency**: Must wait for T026/T027.
- [ ] T029 [US3] Implement `code/main.py` to orchestrate analysis. **Requirements**:
 1. Aggregate results from T026a, T026b, T027a, T027b.
 2. **Verification**: Explicitly verify that the analysis logic prioritizes the 'plan' grid for the deviation ratio regression (T026a) and KS test (T027a) as per the Plan's methodological revision. Log a warning if the 'spec' grid is used for these specific metrics.
 3. Save to `data/model_fits.json` with exact schema:
 ```json
 {
 "plan_beta": <float or null>,
 "plan_beta_se": <float or null>,
 "plan_r_squared": <float or null>,
 "plan_ks_p": <float>,
 "spec_beta": <float or null>,
 "spec_beta_se": <float or null>,
 "spec_r_squared": <float or null>,
 "spec_chi2_p": <float>
 }
 ```
 **Handling Non-Convergence**: If a regression fails to converge (e.g., `R^2 < 0.0` or `scipy.optimize` raises a `RuntimeError` after multiple iterations), set the corresponding beta, se, and r_squared values to `null` and log a warning with the specific error message: `WARNING: Regression failed for {group}: {error_message}`.
 **Note**: `plan_beta` is an exploratory metric with no Spec-defined success threshold. `spec_beta` is the only metric with a defined threshold (SC-001).
 **Dependency**: Must wait for T023, T026a, T026b, T027a, T027b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior research-stage reviews

- [X] T030 [P] **Visualization Annotation**: Update `code/viz.py` to add specific text annotations at coordinates (x,y) for each plot indicating "Associational Trend Only" (per Spec Assumptions). Update `code/analysis.py` docstrings to explicitly state "Correlation does not imply causation".
- [X] T031 [P] Documentation updates: Create `docs/methodology.md` containing sections: "Sieve Implementation", "Smoothness Logic", "Statistical Tests (KS & Chi-Square)", "Dual-Grid Rationale". Ensure reproducibility steps are detailed.
- [X] T032a [P] **Performance Profiling**: Profile `code/smoothness.py` loop using `cProfile`. **Output**: Save detailed profiling report to `data/profiles/smoothness_baseline.txt` (cProfile pstats text format).
- [ ] T032b [US2] **Performance Optimization**: Implement vectorized factorization using `numpy` broadcasting. **Method**: Create boolean masks for primes $\le y$ and use `np.all` to check smoothness across the interval array. **Dependency**: Must wait for T032a.
- [ ] T032c [US2] **Benchmark Verification**: Run the optimized `smoothness.py` against the same parameters as T032a and record the runtime comparison. **Output**: Save results to `data/benchmark_results.json` with schema `{"baseline_ms": float, "optimized_ms": float, "speedup_factor": float, "passed": bool}`. **Dependency**: Must wait for T032b.
- [ ] T033a [P] **Reproducibility Execution**: Execute the `quickstart.md` script end-to-end in a clean environment using Docker image `python:3.11-slim` on an `ubuntu-latest` runner. **Output**: Capture stdout/stderr to `data/ci_logs/repro_run.log`. **Dependency**: None.
- [ ] T033b [P] **Reproducibility Verification**: Verify the output of T033a. **Requirements**:
 1. Check exit code is 0.
 2. Verify `data/primes_1e9.csv` exists and matches the checksum in `state/`.
 3. Verify `data/density_measurements_plan.csv` exists and has non-zero rows.
 4. Output `repro_verified: true` to `data/repro_status.json`.
 **Dependency**: Must wait for T033a.
- [ ] T036 [US3] **Draft Narrative**: Write the initial `research.md` artifact. **Requirements**:
 1. Create `research.md` with sections: "Introduction", "Methodology", "Results", "Narrative Interpretation".
 2. **Constraint**: Do NOT insert pre-scripted metaphors (e.g., "forest density", "moments of tension") based on simulated feedback. Narrative must emerge strictly from the empirical results in `data/model_fits.json` and `data/density_measurements_*.csv`.
 3. Ensure the file is saved to `docs/research.md`.
 **Dependency**: Must wait for T029 (for data context).

**Checkpoint**: All tasks complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **CRITICAL**: User Stories are SEQUENTIAL due to data dependencies:
 - US1 (Sieve) -> US2 (Density) -> US3 (Analysis).
 - US2 tasks (T020-T023) CANNOT start until T012 (US1) produces `data/primes_1e9.csv` AND T013 validates it.
 - US3 tasks (T026-T029) CANNOT start until T023 (US2) produces `data/density_measurements_*.csv`.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: **STRICT DEPENDENCY** on US1 (needs `data/primes_1e9.csv` AND validation from T013).
- **User Story 3 (P3)**: **STRICT DEPENDENCY** on US2 (needs `data/density_measurements_*.csv`) and US1 (for Dickman function context).

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
Task: "Implement T026a (Deviation Ratio Regression - Plan-Primary)"
Task: "Implement T026b (Raw Density Regression - Spec-Baseline)"
Task: "Implement T027a (KS Test - Plan-Primary)"
Task: "Implement T027b (Chi-Square Test - Spec-Mandatory)"
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
- **Critical**: Ensure `code/analysis.py` implements BOTH Chi-Square (Spec/FR-005) and KS (Plan) tests to satisfy FR-005 and Plan Principle VII, with clear labeling of Spec-Mandatory vs Plan-Primary.
- **Critical**: Task T012 must enforce the 120-minute runtime constraint via checkpoint/resume logic, not just warning log.
- **Critical**: Task T030 must strictly adhere to "associational" framing as per Spec Assumptions.
- **Critical**: Task T013 MUST use `sympy.isprime` for verification (not self-referential trial division) to satisfy Constitution Principle VI and runtime constraints.
- **Critical**: Task T036 must ensure narrative captions are strictly data-derived, moving metaphors to `research.md` to preserve the Single Source of Truth.
- **Critical**: Task T023 must execute BOTH the Spec's $x^\alpha$ grid and the Plan's fixed $h$ grid to satisfy both methodological requirements and SC-004.
- **Critical**: Task T032b must focus on runtime compliance, specifically targeting a [deferred] reduction via numpy broadcasting.
- **Critical**: Task T029 must explicitly state that `plan_beta` is exploratory and lacks a Spec-defined success threshold, AND must verify that the analysis prioritizes the 'plan' grid for the deviation ratio and KS tests.
- **Critical**: Task T023b must only verify data generation (T023) and NOT reference future analysis tasks (T026/T027).