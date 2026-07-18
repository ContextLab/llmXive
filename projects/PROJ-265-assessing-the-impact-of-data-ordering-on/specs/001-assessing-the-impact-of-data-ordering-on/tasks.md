# Tasks: Assessing the Impact of Data Ordering on Bootstrapping Results

**Input**: Design documents from `/specs/001-assess-data-ordering-bootstrapping/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit and integration tests are included to verify the bootstrap logic, data generation, and coverage metrics.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. US-3 is now active and implements the real-world data analysis using the UCI dataset.

**Format**: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on prior task completion)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Create `code/`, `tests/`, `data/raw/`, `data/processed/`, and `results/` directories.
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing: `numpy>=1.24`, `pandas>=2.0`, `scikit-learn>=1.2`, `statsmodels>=0.14`, `scipy>=1.10`, `pyyaml>=6.0`, `pytest>=7.4`. Use major.minor version pinning.
- [X] T003 [P] Configure linting and formatting: Create `.flake8` (max-line-length=88, ignore=E203,W503) and `pyproject.toml` (black config: line-length=88)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for configuration, random seeds, and path management
- [X] T005 [P] Implement `code/utils.py` for logging helpers, checksum verification, and plotting scaffolding
- [X] T005b [S] [Dependency: T005] Implement `code/utils.py` extension for Synthetic Data Checksumming: Add function `def hash_synthetic_params(seed: int, phi: float, n: int) -> str` to generate a deterministic hash for synthetic data integrity tracking per Constitution Principle III.
- [X] T006 [P] Create `code/data_generation.py` stub with function signature `def generate_ar1(phi: float, n: int, seed: int) -> np.ndarray`. **Requirement**: The stub must raise `NotImplementedError` if called before implementation.
- [X] T007 [P] Create `code/bootstrap_engine.py` stub with function signature `def standard_bootstrap(data: np.ndarray, n_resamples: int, seed: int) -> list`. **Requirement**: The stub must raise `NotImplementedError` if called before implementation.
- [X] T008 [P] Create `code/metrics.py` stub with function signatures: `def calculate_coverage(cis: list, true_mean: float) -> float`. **Requirement**: The stub must raise `NotImplementedError` if called before implementation.
- [X] T009 [P] Create `code/runner.py` stub with entry point `def run_simulation(phi: float, n: int, seed: int) -> dict`. **Requirement**: The stub must raise `NotImplementedError` if called before implementation.

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
 - Assertion: `assert ci_lower < 0 < ci_upper` and `assert ci_width > 0`. (Note: Specific width value is `[deferred]` to avoid empirical hardcoding).
- [X] T012 [P] [US1] Integration test for coverage calculation in `tests/test_metrics.py`:
 - Function: `test_coverage_degradation_at_high_phi`.
 - Input: `phi=0.8`, `n=100`, `trials=1000`, `seed=42`.
 - Logic: Run simulation, calculate coverage.
 - Assertion: `assert coverage < 0.95`. (Note: Specific magnitude of drop is `[deferred]` until empirical results are available).

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_generation.py`: Generate AR(1) series using algorithm `y_t = phi * y_{t-1} + epsilon` (epsilon ~ N(0,1)). Output: `numpy.ndarray`.
- [X] T014 [US1] Implement `code/bootstrap_engine.py`: Standard non-parametric bootstrap (a sufficient number of resamples). Use `np.random.choice(data, size=n, replace=True)`. Output: List of bootstrap means.
- [X] T015 [US1] Implement `code/metrics.py`: Calculate empirical coverage probability. Input: List of CIs. Logic: `sum(1 for ci in cis if ci[0] <= true_mean <= ci[1]) / len(cis)`.
- [X] T016 [US1] Implement `code/runner.py`: Orchestrate simulation batches. Logic: Nested loops for $\phi$ in [0.0, 0.9] (step 0.1) and $N \in \{50, 100, 200\}$. Output: JSON log to `results/simulation_logs.json`. **Schema**: Each entry must contain keys: `phi` (float), `n` (int), `seed` (int), `coverage` (float), `ci_bounds` (list of 2 floats), `ordered` (bool), `shuffled` (bool).

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
- [X] T019 [P] [US2] [FR-005-AMEND] Unit test for McNemar's test in `tests/test_metrics.py`:
 - Function: `test_mcnemar_test_logic`.
 - Mock contingency table representing a dominant count for the Ordered Covered condition relative to the Shuffled Covered condition.
 - Logic: Run `statsmodels.stats.contingency.mcnemar`.
 - Assertion: `assert p_value < 0.05` (indicating significant difference).
 - **Constraint Justification**: This task implements McNemar's test per the plan's 'Complexity Tracking' section (FR-005-AMEND) for paired data, deviating from the generic Z-test in FR-005 to ensure statistical validity.

### Implementation for User Story 2

- [X] T020 [P] [US2] [Dependency: T014] Implement `code/bootstrap_engine.py` extension: Add function `def shuffled_bootstrap(data: np.ndarray, n_resamples: int, seed: int) -> list`. Logic: Shuffle input data before resampling.
 - Note: Can run in parallel with T015/T016 once T014 is implemented.
- [X] T021 [US2] Implement `code/metrics.py` to calculate magnitude of coverage drop. Logic: `abs(empirical_coverage - 0.95)`.
- [X] T022 [US2] [FR-005-AMEND] Implement `code/metrics.py` McNemar's test for paired outcomes. Input: Contingency table of (Ordered Covered, Shuffled Covered) counts. Logic: Use `statsmodels.stats.contingency.mcnemar`.
 - **Constraint Justification**: This task implements McNemar's test per the plan's 'Complexity Tracking' section (FR-005-AMEND) for paired data, deviating from the generic Z-test in FR-005 to ensure statistical validity.
- [X] T023 [US2] Update `code/runner.py`: Execute paired simulations (Ordered + Shuffled) for each trial. Logic: Loop must run both bootstrap types for the same seed.
- [X] T024 [S] [US2] Create `results/coverage_metrics.csv` with headers [phi, n, ordered_cov, shuffled_cov, diff, p_value] and implement logic to append rows. Logic: Calculate `diff` as `ordered_cov - shuffled_cov`. **Formatting**: `p_value` must be formatted as a float with 6 decimal places. Note: Removed `ci_width_ratio` and `bias_block` as these belong to blocked FR-010 (now active in T033).

**Checkpoint**: US-2 complete; mechanism of bias (temporal dependence) is isolated and quantified.

---

## Phase 5: User Story 3 - Analyze Real-World Data Segments (Priority: P3)

**Status**: **ACTIVE**. Implements analysis on the UCI Individual Household Electric Power Consumption dataset as mandated by Constitution Principles VI and VII.

**Scope**: Load real data, segment into hourly windows, estimate autocorrelation, and compare ordered vs. shuffled bootstrap metrics using alternative ground-truth references (CI Width Stability, Block-Bootstrap Bias).

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/data_loader.py`:
 - Function: `def load_and_segment(url: str) -> list`.
 - Logic: Fetch UCI dataset from `[dataset-id]/LD2011_2014.txt.zip` (or verified equivalent).
 - Logic: Verify file integrity using MD5 checksum. If verification fails, raise `RuntimeError` explicitly and halt execution (per FR-006). **NO SYNTHETIC FALLBACK**.
 - Logic: Segment data into non-overlapping hourly windows.
 - Logic: Estimate AR(1) coefficient for each segment using `statsmodels`.
 - Logic: Skip segments with $N < 30$ by logging JSON `{"status": "skipped", "reason": "insufficient_data", "segment_id": "<id>"}` to `results/simulation_logs.json`.
 - Output: List of `DataSegment` objects.
- [X] T033 [P] [US3] Implement `code/metrics.py` extension for real-world data:
 - Function: `def calculate_ci_width_stability(ordered_ci_widths: list, shuffled_ci_widths: list) -> float`.
 - Function: `def calculate_bias_block_bootstrap(ordered_means: list, block_bootstrap_means: list) -> float`.
 - Logic: Calculate ratio of ordered/shuffled CI widths and bias relative to block-bootstrap estimate (since theoretical mean is unknown).
- [X] T035 [P] [US3] Implement `code/metrics.py` stratification logic:
 - Function: `def stratify_by_phi(results: list, bins: list) -> dict`.
 - Logic: Bin results by estimated phi (e.g., 0.0-0.1, 0.1-0.2) and calculate aggregate metrics per bin.
 - Output: Generate `results/stratified_report.md` containing the stratified summary table.

**Checkpoint**: US-3 complete; real-world validation of synthetic findings is performed.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Parallel Report Generation & Verification
**⚠️ CRITICAL**: These tasks depend on T030 (Simulation Completion) but can run in parallel with each other.

- [X] T025 [P] Generate Sensitivity Analysis Report in `results/sensitivity_analysis.md` (per FR-011):
 - Structure: Markdown sections "Sensitivity by N", "Plots".
 - Logic: Aggregate results from `results/coverage_metrics.csv` comparing N=50, 100, 200 to confirm effect is not small-sample artifact.
- [X] T027 [P] Generate summary report in `results/summary_report.md`. Structure: Markdown sections "Summary", "Coverage Table", "Significance Table".
- [X] T029 [P] Create `quickstart.md` with instructions: Prerequisites, Install command, Run command (`python code/runner.py --full`), Expected output.
- [X] T037 [P] [Dependency: T030] Create `tests/test_reproducibility.py`:
 - Function: `def verify_reproducibility() -> bool`.
 - Logic: Run `runner.py --seed=42` twice. Capture content hash of `results/coverage_metrics.csv` for both runs. Assert hashes match.
 - Note: Must complete after T030.
- [X] T039 [P] [Dependency: T030] Execute reproducibility verification:
 - Command: `pytest tests/test_reproducibility.py::verify_reproducibility`.
 - Logic: Assert `results/coverage_metrics.csv` content hash is identical across runs.
 - Note: Must complete after T030.

### Sequential Simulation Run
- [X] T030 [S] Run full simulation batch (**Synthetic + Real**). Command: `python code/runner.py --full`. Verify: Execution time < 6 hours.
 - Note: Scope now includes Synthetic and Real-World data. SC-004 feasibility is re-evaluated based on this expanded workload.

---

## Removed Tasks

**Purpose**: Documenting tasks removed due to scope completion or redundancy.

- **T036**: Removed. Task to add a "performance profiling harness" (cProfile, line_profiler) was deemed scope creep. SC-004 (6-hour limit) is satisfied by T030's runtime measurement.
- **T031**: Removed. Final code cleanup is implicit in the definition of a completed task and does not require a separate task ID in the active list.
- **T038**: Removed. Formal Scope Reduction Record is no longer needed as US-3 is now active and compliant with the Constitution.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core MVP
- **User Story 2 (Phase 4)**: Depends on Foundational and **T014 implementation** (US-1 Implementation) - Requires US-1 results for comparison
- **User Story 3 (Phase 5)**: **ACTIVE** - Implementation tasks (T032, T033, T035) are now active and depend on Foundational.
- **Polish (Phase N)**: Depends on US-1, US-2, and US-3 completion (specifically T030).

### User Story Dependencies

- **User Story 1 (P1)**: Independent core logic.
- **User Story 2 (P2)**: Depends on US-1 implementation (needs the same bootstrap engine, just different input permutation).
- **User Story 3 (P3)**: Depends on Foundational. Can run in parallel with US-1/US-2 implementation.

### Parallel Opportunities

- **Phase 1 & 2**: T001, T003, T004, T005, T005b (after T005), T006, T007, T008, T009 can be parallelized.
- **Testing**: T010, T011, T012 can run in parallel (Test-First approach). T018, T019 can run in parallel with T020-T022 (same cycle).
- **Implementation**: T013 (Generation) can be parallel with T006-T009 stubs. T020 (Shuffling) depends on T014 implementation, not the whole US-1 phase. T032, T033, T035 can run in parallel with US-1/US-2 implementation.
- **Report Generation & Verification**: T025, T027, T029, T037, T039 can all run in parallel once T030 is complete.

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
3. Add Phase 5 (US-3) logic: Implement data loader, alternative metrics, and stratification.
4. Generate final reports (Phase N).

---

## Notes

- **Real Data**: US-3 is now active. The system loads the UCI dataset, verifies MD5, and performs analysis. No synthetic fallback is permitted.
- **Feasibility**: All tasks are CPU-only and designed to run within 6 hours on 2 cores. Real-world data processing is optimized via chunking if necessary.
- **Seeds**: All random operations must use seeds defined in `code/config.py` for reproducibility.
- **Statistical Test**: T022 implements McNemar's test per plan's methodological reasoning, overriding spec's generic "z-test" mention for paired data validity. Tags `[FR-005-AMEND]` added to T019 and T022.
- **Reproducibility**: T037 and T039 added to explicitly validate deterministic reproducibility as required by the constitution. T037 is script creation; T039 is execution. T037 and T039 are now parallelized with report generation (T025/T027/T029) after T030.
- **Constraint Preservation**: The Plan's override of FR-005 (z-test) with McNemar's test is documented in T019/T022 with traceability tags. The Constitution's mandate for real-world analysis is satisfied by the activation of T032, T033, T035.
- **Dependency Correction**: T020 is marked [P] with a dependency on T014 implementation. T005b is marked [S] with dependency on T005.
- **Sequential Verification**: T037/T039 depend on T030 but are parallel with T025/T027/T029.
- **Review Resolution**: T037 and T039 address the "Reproducibility" review concern by explicitly verifying that `runner.py` produces identical hashes for identical seeds, ensuring the "Single Source of Truth" principle is met computationally.