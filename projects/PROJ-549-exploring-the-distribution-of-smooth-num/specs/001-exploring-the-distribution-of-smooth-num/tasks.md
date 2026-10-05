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
- [X] T003 [P] Configure linting and formatting: Create `.flake8` with content `[flake8] max-line-length = 100 ` and `pyproject.toml` with sections `[tool.black] line-length = 100 target-version = ['py311'] ` and `[tool.pytest]`.

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

**Independent Test**: Execute the sieve script in isolation; verify output count matches $\pi(10^9) = 50,847,534$ within 1 second; verify peak memory < 4 GB [UNRESOLVED-CLAIM: c_ef67e926 — status=not_enough_info].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for sieve boundary conditions in `tests/test_sieve.py`: Create `tests/test_sieve.py` with functions `test_sieve_empty_interval`, `test_sieve_single_prime`, and `test_sieve_boundary_1e9`. Ensure these tests fail initially by asserting specific incorrect values: `assert count == 0` for empty interval, `assert count == 1` for single prime, and `assert count == 50847533` (off-by-one) for boundary 1e9.
- [X] T011 [P] [US1] Integration test for prime count verification in `tests/test_sieve.py`: Implement `test_prime_count_exact` asserting `50847534 (OEIS A006880, https://oeis.org/A006880)` (verified value for $\pi(10^9)$) and `test_sieve_runtime` asserting `7200` (120 minutes in seconds).

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/sieve.py`: Segmented Sieve of Eratosthenes with a memory cap. **Requirements**:
 1. Implement a hard runtime cap using `signal.SIGALRM` (with `threading.Timer` fallback for non-POSIX) set to **7200 seconds** (120 minutes). **Fallback Logic**: If `signal.SIGALRM` is unavailable (e.g., Windows), skip timeout enforcement and rely on the `threading.Timer` fallback to log a warning and exit.
 2. **Checkpoint Logic**: On timeout or memory limit, write a JSON checkpoint file to `data/checkpoint.json` with schema: `{"segment_index": int, "last_prime": int, "timestamp": "ISO8601"}`. Resume from this file on next run.
 3. Monitor peak memory usage (e.g., `psutil`) and log if it exceeds a predefined threshold.
 4. Perform a self-check: verify `last_prime < 10^9` and `len(set(primes)) == len(primes)` before writing.
 5. Output to `data/primes_1e9.csv` (one prime per line).
 **Dependency**: None.
- [X] T013 [US1] Implement and run `code/validate_sieve.py`: A separate script to verify the generated prime list from `data/primes_1e9.csv`. **Requirements**:
 1. **DO NOT** use self-referential trial division (circular logic).
 2. Verify total count aligns with the expected theoretical magnitude.
 3. **Spot Check**: Sample a representative subset of primes from the list using **stratified sampling** with `numpy.linspace` to select indices at intervals of `N/10000 (OEIS A051021, https://oeis.org/A051021)` with a fixed seed (e.g., `seed=42`). Verify each sampled prime `p` using `sympy.isprime(p)` (an independent, deterministic library) to ensure primality.
 4. Output a JSON report to `data/sieve_validation_report.json` with schema: `{"count": int, "sample_size": 10000, "all_valid": bool, "checksum": str, "timestamp": str}`.
 5. The script must exit with code 0 only if `all_valid` is true and `count` matches.
 **Dependency**: Must complete after T012 (produces artifact).
- [X] T014 [US1] Add CLI entry point in `code/main.py` to trigger sieve generation with progress logging. **Dependency**: Must complete after T012 AND T013 to ensure the CLI only runs on validated data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Smooth Number Density Across Parameter Grid (Priority: P2)

**Goal**: Enumerate integers in short intervals $[x, x+h]$ across BOTH the Spec-defined and Plan-defined grids to calculate $y$-smooth densities.

**⚠️ METHODODOLOGICAL AMENDMENT**: The Spec's FR-002/US-2 is hereby amended to include the Plan's fixed-$h$ grid for variance analysis (SC-004) alongside the Spec's power-law grid. This dual-grid approach is now the official requirement.

**Independent Test**: Run on a small fixed subset ($x=10^6, y=100$); verify count matches brute-force calculation [UNRESOLVED-CLAIM: c_91d01997 — status=not_enough_info].

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for smoothness classification logic in `tests/test_smoothness.py`: Implement `test_factor_all_smaller_y` (returns True), `test_factor_larger_y` (returns False), and `test_empty_interval_count` (returns 0).
- [X] T019 [P] [US2] Integration test for density calculation in `tests/test_smoothness.py`: Implement `test_density_small_interval` with parameters $x=10^6, y=100, h=1000 [UNRESOLVED-CLAIM: c_06b4c905 — status=not_enough_info]$. Verify count matches brute-force ground truth.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/smoothness.py`: Factorization logic using trial division against primes $\le y$ from `data/primes_1e9.csv`. **Dependency**: Must wait for T012 AND T013 (validated prime list).
- [X] T021 [US2] Implement `code/smoothness.py`: Interval enumeration loop that handles edge cases (empty intervals, $x+h > 10^9$) without crashing. **Dependency**: Must wait for T012 AND T013.
- [X] T022 [US2] Implement `code/smoothness.py`: Aggregation logic to compute density $\rho = \text{count}/h$ and deviation ratio $R = \rho_{obs} / \rho_{Dickman}(u)$ for **50** random starting positions per configuration. **Dependency**: Must wait for T012, T013, AND T004 (Dickman function).
- [X] T023a [US2] **Spec-Defined Grid (Baseline)** generation.
 1. Parameters: $y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$, with $h \in \{x^{0.1}, x^{0.3}, x^{0.5}, x^{0.7}, x^{0.9}\}$.
 2. **Non-Integer Handling**: For $h$ values that are not integers (e.g., $x^{0.1}$), **round** to the nearest integer.
 3. Save results to `data/density_measurements_spec.csv` with a `source` column set to 'spec'.
 4. Run **50** random starting positions per configuration.
 **Dependency**: Must wait for T012 AND T013.
- [X] T023b [US2] **Plan-Defined Grid (Variance Analysis)** generation.
 1. Parameters: $y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$, with **fixed interval lengths** $h \in \{10^3, 10^4, 10^5, 10^6\}$.
 2. Save results to `data/density_measurements_plan.csv` with a `source` column set to 'plan'.
 3. Run **50** random starting positions per configuration.
 **Dependency**: Must wait for T012 AND T013.
- [X] T023c [US2] **Conditional Sensitivity Analysis**: Implement logic to trigger a sensitivity sweep of the exponent $\alpha$ (sweeping $\pm 0.05$) if initial results from T026b are inconclusive (defined as $p > 0.05$ AND $|\beta - 1| < 0.1$).
 1. If triggered, re-run the grid generation for $h \in \{x^{0.1 \pm 0.05}, \dots, x^{0.9 \pm 0.05}\}$.
 2. Save results to `data/density_measurements_sensitivity.csv`.
 3. Log a warning if the sweep is not triggered.
 **Dependency**: Must wait for T026b (to check for inconclusive results).
- [X] T023d [US2] **Verify Grid Generation**: Validate the output of T023a and T023b. **Requirements**:
 1. Confirm `data/density_measurements_spec.csv` and `data/density_measurements_plan.csv` exist.
 2. Verify non-zero row counts for both files.
 3. Verify the `source` column contains exactly 'spec' and 'plan' values respectively.
 4. Verify the schema matches the expected columns (x, y, h, start_offset, count, density, ratio).
 5. Output `grid_verification.json` with status `{"spec_valid": bool, "plan_valid": bool}`.
 **Dependency**: Must wait for T023a AND T023b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization of Density Trends (Priority: P3)

**Goal**: Fit power-law models to the observed density data (both grids), perform BOTH Chi-Square (Spec) and KS (Plan) tests, and generate visualizations.

**Independent Test**: Run analysis on synthetic data with known $\beta$; verify regression recovers $\beta$ within margin.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for WLS regression implementation in `tests/test_analysis.py`: Implement `test_wls_recovery` using synthetic data: 10 points, slope=2.0, noise=0.1 [UNRESOLVED-CLAIM: c_8edf4a34 — status=not_enough_info]. Assert `abs(beta_estimated - 2.0) < 0.05 `.
- [X] T025 [P] [US3] Unit test for Chi-Square test logic in `tests/test_analysis.py`: Implement `test_chi_square_logic` with synthetic observed/expected counts. Assert p-value is calculated and within expected range.

### Implementation for User Story 3

- [ ] T026a [P] [US3] Implement `code/analysis.py`: **Plan-Primary (Exploratory)** Power-law regression to fit $R \propto h^\beta$ (deviation ratio) for each $y$-group using the Plan-defined grid (`density_measurements_plan.csv`). **Note**: This metric is exploratory and has no Spec-defined success threshold (SC-001 applies to raw density). (Satisfies Plan Summary). **Output**: Write results to `data/model_fits_plan.json`. **Dependency**: Must wait for T023b AND T004.
- [ ] T026b [P] [US3] Implement `code/analysis.py`: **Spec-Mandatory (Baseline)** Power-law regression to fit $\rho = c \cdot h^\beta$ (raw density) for each $y$-group using the Spec-defined grid (`density_measurements_spec.csv`). This satisfies FR-004 and SC-001. **Output**: Write results to `data/model_fits_spec.json`. **Dependency**: Must wait for T023a.
- [ ] T027a [P] [US3] Implement `code/analysis.py`: **Plan-Primary (Exploratory)** Kolmogorov-Smirnov (KS) test comparing observed vs. Dickman distributions for the Plan-defined grid. **Note**: This is an **exploratory** task not required by the Spec; it is included to satisfy the Plan's methodological revision but does not replace the Spec-mandated Chi-Square test. (Satisfies Plan Principle VII). **Output**: Append to `data/model_fits_plan.json`. **Dependency**: Must wait for T023b AND T004.
- [ ] T027b [P] [US3] Implement `code/analysis.py`: **Spec-Mandatory (Baseline)** Chi-Square Goodness-of-Fit test comparing observed counts vs. Dickman expectations for the Spec-defined grid. **Method**:
 1. Input: `data/density_measurements_spec.csv`.
 2. **Binning**: Bin on **observed density values**. Use Sturges' rule to determine number of bins $k = \lceil 1 + \log_2(N) \rceil$.
 3. **Merge Strategy**: If any bin has expected count < 5, merge adjacent bins, prioritizing the bins with the **lowest expected counts**. If multiple bins have the same lowest expected count, **merge the leftmost bin**.
 4. Calculate expected counts for each bin: $E_i = \sum (\rho_{Dickman}(u) \cdot h \cdot \text{bin\_width})$.
 5. Compute $\chi^2$ statistic and p-value.
 6. Output: Append to `data/model_fits_spec.json`.
 **Note**: This test satisfies FR-005 and is mandatory. **Dependency**: Must wait for T023a.
- [X] T028 [US3] Implement `code/viz.py`: Generate density vs. interval length plots with confidence intervals and theoretical curves for BOTH grids; save to `data/` as PNG. **Requirement**: Generate captions directly from the data (e.g., "Observed: {rho}, Expected: {exp}, p={p}") and save as text next to the image. **Dependency**: Must wait for T026/T027.
- [X] T029 [US3] Implement `code/main.py` to orchestrate analysis. **Requirements**:
 1. Aggregate results from T026a, T026b, T027a, T027b by reading `data/model_fits_plan.json` and `data/model_fits_spec.json`.
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
 **Handling Non-Convergence**: If a regression fails to converge (e.g., `scipy.optimize` raises a `RuntimeError` OR if $R^2 < 0.0$ OR if $R^2$ is `NaN`), set the corresponding beta, se, and r_squared values to `null` and log a warning with the specific error message: `WARNING: Regression failed for {group}: {error_message}`.
 **Note**: `plan_beta` is an exploratory metric with no Spec-defined success threshold. `spec_beta` is the only metric with a defined threshold (SC-001).
 **Dependency**: Must wait for T023a, T023b, T026a, T026b, T027a, T027b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior research-stage reviews

- [ ] T030 [P] **Visualization Annotation**: Update `code/viz.py` to add specific text annotations at coordinates (x,y) for each plot indicating "Associational Trend Only" (per Spec Assumptions). Update `code/analysis.py` docstrings to explicitly state "Correlation does not imply causation".
- [X] T031 [P] Documentation updates: Create `docs/methodology.md` containing sections: "Sieve Implementation", "Smoothness Logic", "Statistical Tests (KS & Chi-Square)", "Dual-Grid Rationale". Ensure reproducibility steps are detailed.
- [X] T033a [P] **Reproducibility Execution**: If `docs/quickstart.md` does not exist, generate it. Then execute the `quickstart.md` script end-to-end in a clean environment using Docker image `python:slim` on an `ubuntu-latest` runner. **Command**: `docker run --rm -v $(pwd):/app python:slim bash /app/docs/quickstart.md`. **Output**: Capture stdout/stderr to `data/ci_logs/repro_run.log`. **Dependency**: None.
- [X] T033b [P] **Reproducibility Verification**: Verify the output of T033a. **Requirements**:
 1. Check exit code is 0.
 2. Verify `data/primes_1e9.csv` exists and matches the checksum in `state/`.
 3. Verify `data/density_measurements_plan.csv` exists and has non-zero rows.
 4. Output `repro_verified: true` to `data/repro_status.json`.
 **Dependency**: Must wait for T033a.
- [X] T036 [US3] **Draft Narrative**: Write the initial `research.md` artifact. **Requirements**:
 1. Create `research.md` with sections: "Introduction", "Methodology", "Results", "Narrative Interpretation".
 2. **Constraint**: Parse `data/model_fits.json` for `plan_beta`, `spec_chi2_p`, and `density_measurements_*.csv` for variance. Narrative must emerge strictly from these empirical results.
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
- **Critical**: Task T012 must enforce the 7200-second (120-minute) runtime constraint via checkpoint/resume logic, not just warning log.
- **Critical**: Task T030 must strictly adhere to "associational" framing as per Spec Assumptions.
- **Critical**: Task T013 MUST use `sympy.isprime` for verification (not self-referential trial division) to satisfy Constitution Principle VI and runtime constraints.
- **Critical**: Task T036 must ensure narrative captions are strictly data-derived, moving metaphors to `research.md` to preserve the Single Source of Truth.
- **Critical**: Task T023a and T023b must execute BOTH the Spec's $x^\alpha$ grid and the Plan's fixed $h$ grid to satisfy both methodological requirements and SC-004.
- **Critical**: Task T029 must explicitly state that `plan_beta` is exploratory and lacks a Spec-defined success threshold, AND must verify that the analysis prioritizes the 'plan' grid for the deviation ratio and KS tests.
- **Critical**: Task T023d must only verify data generation (T023a/T023b) and NOT reference future analysis tasks (T026/T027).
- **Critical**: Task T023c must implement the conditional sensitivity analysis as per Spec Assumption-6.
- **Critical**: Task T026a/T027a must write to `model_fits_plan.json` and T026b/T027b to `model_fits_spec.json` to avoid race conditions.
