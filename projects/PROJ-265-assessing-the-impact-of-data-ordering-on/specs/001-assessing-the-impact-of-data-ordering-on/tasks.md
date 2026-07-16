# Tasks: Assessing the Impact of Data Ordering on Bootstrapping Results

**Input**: Design documents from `/specs/001-assess-data-ordering-bootstrapping/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit and integration tests are included to verify the bootstrap logic, data generation, and coverage metrics.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. US-3 logic is implemented as 'blocked-ready' code to satisfy spec requirements, with execution gated by data availability.

**Format**: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project directory structure: Create `code/`, `tests/`, `data/raw/`, `data/processed/`, and `results/` directories.
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing: `numpy>=1.24`, `pandas>=2.0`, `scikit-learn>=1.2`, `statsmodels>=0.14`, `scipy>=1.10`, `pyyaml>=6.0`, `pytest>=7.4`. Use major.minor version pinning.
- [X] T003 [P] Configure linting and formatting: Create `.flake8` (max-line-length=88, ignore=E203,W503) and `pyproject.toml` (black config: line-length=88)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for configuration, random seeds, and path management
- [X] T005 [P] Implement `code/utils.py` for logging helpers, checksum verification, and plotting scaffolding
- [X] T006 [P] Create `code/data_generation.py` stub with function signature `def generate_ar1(phi: float, n: int, seed: int) -> np.ndarray`
- [X] T007 [P] Create `code/bootstrap_engine.py` stub with function signature `def standard_bootstrap(data: np.ndarray, n_resamples: int, seed: int) -> list`
- [X] T008 [P] Create `code/metrics.py` stub with function signatures: `def calculate_coverage(cis: list, true_mean: float) -> float`, `def calculate_ci_width_stability(ordered_cis: list, shuffled_cis: list) -> float`, `def calculate_bias_block_bootstrap(ordered_cis: list, block_cis: list) -> float`
- [X] T009 [P] Create `code/runner.py` stub with entry point `def run_simulation(phi: float, n: int, seed: int) -> dict`
- [ ] T032 [BLOCKED] [P] Implement error handling and logging logic for real-world data:
 - Function in `code/data_loader.py`: `def load_and_segment(url: str) -> list`.
 - Logic: If URL missing/unreachable or checksum fails, raise explicit error and halt execution (per FR-006).
 - Logic: If segment N < 30, log JSON `{"status": "skipped", "reason": "insufficient_data"}` to `results/simulation_logs.json`.
 - Logic: Handle missing values in UCI dataset (drop or impute consistently).
 - Note: This task is placed here to ensure the utility is available if the block is lifted, but execution is blocked by plan.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulate Autocorrelated Data and Compute Coverage (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic autoregressive time series, apply standard bootstrapping, and calculate empirical coverage probability against the theoretical mean (0).

**Independent Test**: Run a simulation with $\phi=0.8$ and verify coverage is significantly lower than 0.95.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests FIRST to ensure they FAIL before implementation.

- [X] T010 [P] [US1] Unit test for AR(1) generation in `tests/test_data_generation.py`:
 - Function: `test_generate_ar1_returns_correct_mean_and_phi`.
 - Input: `phi=0.8`, `n=100`, `seed=42`.
 - Logic: Generate series, estimate phi using `statsmodels.tsa.ar_model.AutoReg`, calculate mean.
 - Assertion: `assert abs(estimated_phi - 0.8) < 0.05` and `abs(mean - 0.0) < 0.01`.
- [X] T011 [P] [US1] Unit test for bootstrap CI calculation in `tests/test_bootstrap_engine.py`:
 - Function: `test_standard_bootstrap_ci_bounds`.
 - Input: `data = np.random.normal(0, 1, 1000)`, `n_resamples=1000`, `seed=42`.
 - Logic: Run bootstrap, calculate 95% CI.
 - Assertion: `assert ci_lower < 0 < ci_upper` and `abs(ci_width - 0.12) < 0.02` (approx).
- [X] T012 [P] [US1] Integration test for coverage calculation in `tests/test_metrics.py`:
 - Function: `test_coverage_degradation_at_high_phi`.
 - Input: `phi=0.8`, `n=100`, `trials=1000`, `seed=42`.
 - Logic: Run simulation, calculate coverage.
 - Assertion: `assert coverage < 0.92`.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_generation.py`: Generate AR(1) series using algorithm `y_t = phi * y_{t-1} + epsilon` (epsilon ~ N(0,1)). Output: `numpy.ndarray`.
- [X] T014 [US1] Implement `code/bootstrap_engine.py`: Standard non-parametric bootstrap (a sufficient number of resamples). Use `np.random.choice(data, size=n, replace=True)`. Output: List of bootstrap means.
- [X] T015 [US1] Implement `code/metrics.py`: Calculate empirical coverage probability. Input: List of CIs. Logic: `sum(1 for ci in cis if ci[0] <= true_mean <= ci[1]) / len(cis)`.
- [X] T016 [US1] Implement `code/runner.py`: Orchestrate simulation batches. Logic: Nested loops for $\phi$ in [, 0.9] (step 0.1) and $N \in \{50, 100, 200\}$. Output: JSON log to `results/simulation_logs.json` including trial results, coverage, and CI bounds.

**Checkpoint**: US-1 is fully functional; coverage degradation is measurable.

---

## Phase 4: User Story 2 - Compare Ordered vs. Shuffled Baselines (Priority: P2)

**Goal**: Apply bootstrapping to shuffled data to break temporal dependence, compare coverage, and perform statistical significance testing.

**Independent Test**: Run simulation on $\phi=0.5$, compare ordered vs. shuffled coverage, and verify p-value < 0.05.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Unit test for data shuffling in `tests/test_bootstrap_engine.py`:
 - Function: `test_shuffle_preserves_marginal_distribution`.
 - Input: `data = np.random.normal(0, 1, 1000)`.
 - Logic: Shuffle data, perform Kolmogorov-Smirnov test against original.
 - Assertion: `assert p_value > 0.05`.
- [X] T019 [P] [US2] Unit test for McNemar's test in `tests/test_metrics.py`:
 - Function: `test_mcnemar_test_logic`.
 - Mock contingency table representing a dominant count for the Ordered Covered condition relative to the Shuffled Covered condition.
 - Logic: Run `statsmodels.stats.contingency.mcnemar`.
 - Assertion: `assert p_value < 0.05` (indicating significant difference).
 - Note: Deviates from FR-005 (z-test) per plan justification for paired data validity.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/bootstrap_engine.py` extension: Add function `def shuffled_bootstrap(data: np.ndarray, n_resamples: int, seed: int) -> list`. Logic: Shuffle input data before resampling.
 - Note: T020 depends on T014 completion.
- [X] T021 [US2] Implement `code/metrics.py` to calculate magnitude of coverage drop. Logic: `abs(empirical_coverage - 0.95)`.
- [X] T022 [US2] Implement `code/metrics.py` McNemar's test for paired outcomes. Input: Contingency table of (Ordered Covered, Shuffled Covered) counts. Logic: Use `statsmodels.stats.contingency.mcnemar`.
 - Note: Deviates from FR-005 (z-test) per plan justification for paired data validity.
- [X] T023 [US2] Update `code/runner.py`: Execute paired simulations (Ordered + Shuffled) for each trial. Logic: Loop must run both bootstrap types for the same seed.
- [X] T024 [US2] Update `results/coverage_metrics.csv`: Add columns `phi`, `n`, `ordered_cov`, `shuffled_cov`, `diff`, `p_value`, `ci_width_ratio`, `bias_block`.

**Checkpoint**: US-2 complete; mechanism of bias (temporal dependence) is isolated and quantified.

---

## Phase 5: User Story 3 - Analyze Real-World Data Segments (Priority: P3)

**Status**: **BLOCKED** per `plan.md` (No verified URL). Implementation tasks added to satisfy spec requirements (FR-006, FR-007, FR-010) as 'blocked-ready' code.

- [ ] T033 [BLOCKED] [P] Implement alternative metrics for real-world data:
 - Function in `code/metrics.py`: `calculate_ci_width_stability` and `calculate_bias_block_bootstrap`.
 - Logic: Calculate ratio of ordered/shuffled CI widths and bias relative to block-bootstrap estimate (since theoretical mean is unknown).
- [ ] T035 [BLOCKED] [P] Implement stratification logic and report for real-world results (FR-009):
 - Function in `code/metrics.py`: `stratify_by_phi(results: list, bins: list)`.
 - Logic: Bin results by estimated phi (e.g., 0.0-0.1, 0.1-0.2) and calculate aggregate metrics per bin.
 - Output: Generate `results/stratified_report.md` containing the stratified summary table.
 - Note: Merges logic for stratification and report generation to satisfy FR-009.

**Checkpoint**: US-3 logic implemented; execution blocked until verified URL is provided in plan.md.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T025 [P] Generate Sensitivity Analysis Report in `results/sensitivity_analysis.md` (per FR-011):
 - Structure: Markdown sections "Sensitivity by N", "Plots".
 - Logic: Aggregate results from `results/coverage_metrics.csv` comparing N=50, 100, 200 to confirm effect is not small-sample artifact.
- [X] T027 [P] Generate summary report in `results/summary_report.md`. Structure: Markdown sections "Summary", "Coverage Table", "Significance Table".
- [X] T029 [P] Create `quickstart.md` with instructions: Prerequisites, Install command, Run command (`python code/runner.py --full`), Expected output.
- [X] T030 [P] Run full simulation batch (Synthetic Only). Command: `python code/runner.py --full`. Verify: Execution time < 6 hours.
 - Note: Scope is synthetic-only due to blocked US-3; SC-004 "full simulation" metric is adjusted accordingly.
- [ ] T031 [P] Final code cleanup: Remove debug prints, fix linting errors, ensure all docstrings are complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core MVP
- **User Story 2 (Phase 4)**: Depends on Foundational and **T014 completion** (US-1 Implementation) - Requires US-1 results for comparison
- **User Story 3 (Phase 5)**: **BLOCKED** - Implementation tasks (T032, T033, T035) exist but execution depends on plan update
- **Polish (Phase N)**: Depends on US-1 and US-2 completion

### User Story Dependencies

- **User Story 1 (P1)**: Independent core logic.
- **User Story 2 (P2)**: Depends on US-1 implementation (needs the same bootstrap engine, just different input permutation).
- **User Story 3 (P3)**: Blocked (Logic implemented, data source missing).

### Parallel Opportunities

- **Phase 1 & 2**: T001, T003, T004, T005, T006, T007, T008, T009, T032 can be parallelized.
- **Testing**: T010, T011, T012 can run in parallel. T018, T019 can run in parallel with T020-T022 (same cycle).
- **Implementation**: T013 (Generation) can be parallel with T006-T009 stubs. T020 (Shuffling) depends on T014 completion, not just stub.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2 (Setup + Foundational).
2. Complete Phase 3 (US-1): Generate data, bootstrap, calculate coverage.
3. **STOP and VALIDATE**: Verify that $\phi=0.8$ yields coverage < 0.95.
4. This constitutes the Minimum Viable Research Unit.

### Incremental Delivery

1. Add Phase 4 (US-2): Implement shuffling and statistical comparison (McNemar's test).
2. Validate that shuffling restores coverage to ~0.95.
3. Add Phase 5 (US-3) logic: Implement error handling and alternative metrics (ready for data).
4. Generate final reports (Phase N).

---

## Notes

- **Real Data**: No real-world data tasks are included. All analysis uses synthetic AR(1) data. Logic for real data is implemented in T032/T033/T035 but blocked by plan.
- **Feasibility**: All tasks are CPU-only and designed to run within 6 hours on 2 cores.
- **Blocked**: US-3 and associated FRs (FR-006, FR-007, FR-009, FR-010) are blocked per `plan.md` due to missing verified URL, but implementation tasks (T032, T033, T035) are present to satisfy spec requirements.
- **Seeds**: All random operations must use seeds defined in `code/config.py` for reproducibility.
- **Statistical Test**: T022 implements McNemar's test per plan's methodological reasoning, overriding spec's generic "z-test" mention for paired data validity.