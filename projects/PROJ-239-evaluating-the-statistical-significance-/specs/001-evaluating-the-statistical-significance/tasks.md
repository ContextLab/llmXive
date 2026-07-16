# Tasks: Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

**Input**: Design documents from `/specs/001-evaluating-the-statistical-significance/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-239-evaluating-the-statistical-significance-`). **Deliverable**: Run `mkdir -p code tests data/raw data/derived` and create empty `code/__init__.py` and `tests/__init__.py`. Verify with `ls code tests data/raw data/derived`.
- [X] T002 Initialize Python 3.11 project with dependencies. **Deliverable**: Create `requirements.txt` with exact pins: `numpy==1.26.0`, `scipy==1.12.0`, `statsmodels==0.14.1`, `pandas==2.2.0`, `pytest==7.4.0`.
- [X] T003 [P] Configure linting (flake8/black). **Deliverable**: Add `.flake8` and `pyproject.toml` with Black config, and verify with `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Create `code/config.py` to define simulation parameters and validation. **Deliverable**: Define constants `ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]`, `ICC_STEP = 0.1`, `ALPHA_LEVELS = [0.01, 0.05, 0.10]`, `DEFAULT_N_CLUSTERS = 100`, `DEFAULT_SEED = 42`. Implement `validate_config(cfg)` that raises `ValueError` if `cfg['n_clusters'] < 50` **unless** `cfg['icc'] == 0.0`. Provide `load_config()` returning a dict and `set_seed(seed)` using `np.random.seed(seed)`.
- [X] T006 [P] Initialize test scaffolding. **Deliverable**: Create the following files with exact content:
 1. `tests/unit/__init__.py`: Empty file or docstring.
 2. `tests/unit/test_data_generator.py`: File containing only a `pass` statement inside a `def test_placeholder():` function.
 3. `tests/unit/test_estimators.py`: File containing only a `pass` statement inside a `def test_placeholder():` function.
- [ ] T007 [P] Add basic CI configuration. **Deliverable**: Create `.github/workflows/ci.yml` that installs `requirements.txt`, runs `pytest`, and caches pip.
- [X] T023 [P] [US3] Implement CLI support for alpha levels in `code/config.py`. **Deliverable**: Extend `load_config()` to accept command-line arguments `--alpha-list` (comma-separated) that override the default `ALPHA_LEVELS` constant. If not provided, defaults to `[0.01, 0.05, 0.10]`. This task **implements** the dynamic override logic required by FR-005. **Note**: This task replaces the previous T034 and is the sole implementation task for CLI alpha levels. It must ensure the runtime configuration uses the CLI value if present, overriding the hardcoded constant from T004.
- [X] T033 [P] Add CLI / config loader support for user‑specified ICC range and step size. **Deliverable**: Extend `code/config.py` with `parse_cli_args()` that populates `cfg['icc_range']` and `cfg['icc_step']` from command-line flags `--icc-range` and `--icc-step`. This satisfies FR-001 user configurability.
- [ ] T035 [US1] Generate synthetic cluster-structure parameters. **Deliverable**: Script `code/synthetic_cluster_params.py` that reads public summary statistics for UCI Online Retail from a **hardcoded dictionary**: `{"avg_cluster_size": 15, "total_clusters": 100, "std_cluster_size": 5}`. Generates a synthetic cluster structure (list of sizes) matching these stats using a log-normal distribution. **Validation**: Must verify that the generated cluster size distribution supports the full `ICC_RANGE` [0.0, 0.5] by ensuring `n_clusters * avg_cluster_size` is sufficient for the random intercept model variance constraints. Saves to `data/derived/synthetic_cluster_structure.csv`. **Constraint**: Do NOT download or ingest the real UCI dataset. Use only summary stats to inform the synthetic generation. If summary stats are missing, fall back to a deterministic default set defined in `config.py`. **Dependency**: [Depends on T004] to access `ICC_RANGE` and `DEFAULT_N_CLUSTERS` for validation.

---

## Phase 3: User Story 1 - Core Simulation (Implementation & Testing)

**Purpose**: Implement the baseline simulation engine and unit tests

- [X] T010 [US1] Implement `code/data_generator.py`. **Deliverable**: Function `generate_data(n_clusters, n_obs_per_cluster, icc, seed) -> pd.DataFrame` using a random intercept model `Y_ij = mu + u_i + e_ij`.
 - **Critical Logic**: If `icc == 0.0`, the random intercept `u_i` MUST be zero (independent data).
 - Treatment labels are assigned **randomly at the cluster level**.
 - **Constitution Note**: This baseline method intentionally violates Principle VI (Cluster-Aware Inference) to measure Type I error inflation. It must be clearly documented as a "violation baseline" for comparison only.
 - Edge‑case handling for `icc=0.0` and unbalanced cluster sizes is added (see T028).
- [X] T036 [P] Wrap naive baseline t‑test with a warning. **Deliverable**: Function `run_naive_ttest_with_warning` in `code/estimators.py` that logs a clear warning that the method assumes independence and is intended only for baseline comparison, thereby respecting Constitution Principle VI.
- [X] T011 [US1] Implement naive baseline t‑test in `code/estimators.py`. **Deliverable**: Function `run_naive_ttest(data, treatment_col, outcome_col) -> float` wrapping `scipy.stats.ttest_ind`. This function **must be called via the wrapper** `run_naive_ttest_with_warning` (see T036) to flag the intentional violation of cluster‑aware inference.
- [X] T012 [US1] Implement `code/simulation_runner.py` baseline loop. **Deliverable**: Function `run_baseline_simulation(icc, n_iterations, seed) -> List[Dict]` that generates data, runs the naive t‑test (through the warning wrapper), stores p‑values, and returns a list of result dicts. **Logic**: Must handle `n_obs_per_cluster` reduction if memory constraints are triggered (see T027).
- [X] T013 [US1] Implement aggregation in `code/analysis.py`. **Deliverable**: Function `aggregate_errors(results_list, alpha_levels) -> pd.DataFrame` that computes empirical Type I error rates and **95 % confidence intervals** using the **Clopper-Pearson (Exact) method** (see T038) to ensure statistical rigor for binary simulation outcomes.
- [ ] T014 [US1] Create script `run_simulation_baseline.py`. **Deliverable**: CLI accepting `--icc`, `--iterations`, `--seed`, and optional `--icc-step`. Uses the config loader (T004) and writes `data/derived/baseline_results.csv`. **Schema**: `iteration, icc, p_value, rejected (bool)`. **Error Handling**: If an iteration fails to generate data or compute p-value, log a warning and skip that iteration (do not crash). **Verification**: Script must verify that `data/derived/baseline_results.csv` exists and contains exactly `len(ICC_RANGE) * iterations` rows before exiting. Exit code 0 on success. **Dependency**: [Depends on T012] and T013.
- [X] T008 [P] [US1] Add unit test for `code/data_generator.py`. **Deliverable**: Implement `tests/unit/test_data_generator.py` with function `test_generate_data_h0_true()` asserting that generated treatment groups have equal means (within tolerance) and that cluster IDs are preserved. **Dependency**: [Depends on T010].
- [X] T009 [P] [US1] Add unit test for `code/estimators.py` standard t‑test. **Deliverable**: Implement `tests/unit/test_estimators.py` with function `test_naive_ttest_independent_data()` that creates independent data with known means and asserts the returned p‑value matches `scipy.stats.ttest_ind` output. **Dependency**: [Depends on T011].

---

## Phase 4: User Story 2 - Robust Methods (Implementation & Testing)

**Purpose**: Implement cluster-robust and permutation tests

- [X] T017 [US2] Implement cluster‑robust variance estimator in `code/estimators.py`. **Deliverable**: Function `run_cluster_robust_ttest(data, treatment_col, outcome_col, cluster_id_col) -> float` using statsmodels `cov_type='cluster'` with CR2 adjustment. This is the constitutionally compliant method.
- [X] T018 [US2] Implement block permutation test in `code/estimators.py`. **Deliverable**: Function `run_block_permutation(data, treatment_col, outcome_col, cluster_id_col, n_permutations=1000) -> float` that permutes treatment labels at the cluster level and returns a p‑value.
- [X] T015 [US2] Add unit test for cluster‑robust variance. **Deliverable**: `tests/unit/test_estimators.py` function `test_cluster_robust_variance_fixed_data()` that runs `run_cluster_robust_ttest` on a small fixed dataset and asserts the p‑value is within an expected range.
- [X] T016 [US2] Add unit test for block permutation logic. **Deliverable**: `tests/unit/test_estimators.py` function `test_block_permutation_respects_clusters()` that verifies no observation‑level swaps occur during permutation.
- [ ] T019 [US2] Extend `code/simulation_runner.py` to include robust methods. **Deliverable**: Update the loop to also run `run_cluster_robust_ttest` and `run_block_permutation` for each iteration, storing their p‑values alongside the naive result. **Depends on** T012 (baseline runner) and T017/T018.
- [X] T020 [US2] Extend aggregation in `code/analysis.py` to compute empirical error rates for all three methods across ICC levels. **Deliverable**: Updated `aggregate_errors` returns a DataFrame with columns `method`, `icc`, `alpha`, `error_rate`, `ci_lower`, `ci_upper`. Uses Clopper-Pearson intervals.
- [ ] T021 [US2] Create script `run_simulation_robust.py`. **Deliverable**: CLI similar to baseline script, writes `data/derived/robustResults.csv`. **Schema**: `iteration, icc, method, p_value, rejected (bool)`. **Error Handling**: If an iteration fails, log warning and skip. **Verification**: Script must verify that `data/derived/robustResults.csv` exists and contains exactly `len(ICC_RANGE) * iterations * 3` rows before exiting. Exit code 0 on success. **Dependency**: [Depends on T019] and T020.

---

## Phase 5: User Story 3 - Analysis & Reporting

**Purpose**: Aggregate results, verify constraints, and generate reports

- [X] T024 [US3] Refactor `code/analysis.py` to compute 95 % CIs using the Clopper-Pearson method from T038 (already part of T013/T020).
- [ ] T025 [US3] Generate `data/derived/final_report.csv`. **Deliverable**: Script `code/scripts/merge_results.py` that reads `data/derived/baseline_results.csv` and `data/derived/robustResults.csv`, aggregates them by ICC and Alpha, computes error rates and CIs, and writes `data/derived/final_report.csv`. **Schema**: `ICC, Alpha, Method, Empirical_Error_Rate, CI_Lower, CI_Upper`. **Verification**: Script must verify that input files exist, contain data, and that `len(df) > 0` and `set(df.columns) == {'ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper'}`. **Dependency**: [Depends on T014] and T021.
- [X] T038 [P] Confidence‑interval method selector. **Deliverable**: Function `select_ci_method(error_rate, n)` in `code/analysis.py` that **always returns 'clopper_pearson'** for this project to ensure statistical rigor and consistency with the Single Source of Truth principle.
- [ ] T027 [US3] [Memory & Time] Implement performance monitoring and enforcement in `code/simulation_runner.py`. **Deliverable**:
 1. Import `tracemalloc` and `time` at the start of the script.
 2. Start tracing before the simulation loop: `tracemalloc.start()`.
 3. **Memory Pre-Check**: Before each iteration, estimate memory footprint. If projected usage > 6 GB, reduce `n_obs_per_cluster` by **halving** it (max 3 retries). If still > 6 GB after 3 retries, raise `RuntimeError`.
 4. **Memory Post-Check**: In each iteration, check `current, peak = tracemalloc.get_traced_memory()`. If `peak > 6.5 * 1024 * 1024 * 1024` (6.5GB), raise `RuntimeError("Memory limit exceeded: 6.5GB. Down-sampling failed.")`.
 5. **Time Enforcement**: Wrap the entire simulation loop in a timer. If total elapsed time > 6 hours (21600 seconds), raise `RuntimeError("Time limit exceeded: 6 hours.")`.
 6. Log wall‑clock time to console and append to `data/timing.csv`; also record peak memory usage to `data/memory.csv`.
 7. **Rationale**: 6.5GB is a safety margin below the 7GB spec limit (FR-006) to prevent OOM crashes on the runner. 6-hour limit enforces SC-003.
- [X] T028 [US3] Edge‑case handling in `code/data_generator.py`. **Deliverable**: Ensure the generator gracefully handles `icc=0.0` (produces independent data by setting random intercept to 0) and accepts a list of heterogeneous cluster sizes; raise informative warnings if clusters are highly unbalanced. If `icc=0.0`, skip the minimum cluster count validation for robust methods.
- [X] T029 [US3] Validate all dependencies are CPU‑only. **Deliverable**: Add a check in CI (`grep -i cuda requirements.txt && echo 'No CUDA deps'`) and confirm the command returns no matches.
- [X] T039 [P] Ensure all scripts run on CPU‑only hardware. **Deliverable**: Add a CI step that parses `requirements.txt` for any CUDA‑related packages and fails the job if found (reinforces T029).
- [ ] T031 [US3] Document `code/simulation_runner.py` **AND** `code/data_generator.py` with Google‑style docstrings covering ICC ranges, iteration counts, and seed usage (Principle VII). **Note**: The plan's reference to `code/simulation.py` is a typo; the correct files are `simulation_runner.py` and `data_generator.py`. **Requirement**: Docstrings must explicitly state the range of ICCs simulated (from non-negative values up to 0.5), the **configurable nature** of the iteration count (default value and CLI override), and the exact random seed used (default 42). This documentation is a hard prerequisite for T026 (Report Generation) to satisfy Constitution Principle VII (Simulation Transparency).
- [X] T032 [Polish] Run quickstart validation. **Deliverable**: Execute `pytest tests/` and capture stdout to `data/test_output.log`. Verify exit code 0. If exit code != 0, the task fails and `data/test_output.log` is marked as an error log. Update `quickstart.md` with the exact command used and the success message from `data/test_output.log` (only if exit code 0).
- [ ] T022 [US3] Integration test for report generation. **Deliverable**: `tests/integration/test_report_generation.py` with function `test_report_contains_all_alpha_levels()` that runs the full simulation (using reduced iterations) and asserts that the generated `final_report.csv` contains rows for α = 0.01, α = 0.05, α = 0.10.
- [X] T045 [US3] [Time Limit] Implement and verify 6-hour time limit enforcement. **Deliverable**:
 1. Ensure `code/simulation_runner.py` (T027) includes the wall-clock timer check.
 2. Create `tests/integration/test_time_limit.py` with a function `test_simulation_respects_time_limit()` that mocks a slow iteration to verify the `RuntimeError` is raised when the 6-hour threshold is exceeded.
 3. Verify that the final report generation (T026) only proceeds if the simulation completes within the time limit.
 4. **Dependency**: Depends on T027.
- [X] T050 [US3] Aggregate Performance Metrics. **Deliverable**: Script `code/scripts/aggregate_metrics.py` that reads `data/timing.csv` and `data/memory.csv`, calculates total simulation time, peak memory, and success/failure counts. Writes `data/derived/performance_summary.csv` with columns `total_time_sec, peak_memory_gb, iterations_completed, status`. **Verification**: Must assert `total_time_sec < 21600` if status is 'success'. **Dependency**: [Depends on T027].
- [ ] T026 [US3] Create `scripts/generate_report.py`. **Deliverable**: Script that reads `final_report.csv` (T025) and `performance_summary.csv` (T050) and produces `specs/001-evaluating-the-statistical-significance/research.md`. **Deliverable Requirement**: The generated report MUST include:
 1. A table with columns: `ICC`, `Alpha`, `Method`, `Empirical_Error_Rate`, `CI_Lower`, `CI_Upper`.
 2. A line plot (saved as `data/derived/error_rate_vs_icc.png`) showing Error Rate vs ICC for all methods.
 3. A section "Performance Summary" explicitly stating total compute time and verifying it is < 6 hours (SC-003).
 **Dependency**: Depends on T025 and T050.

---

## Phase 6: Cross‑Cutting Enhancements & Constitution Alignment

- [X] T030 [US3] Add pytest integration test for end‑to‑end simulation with reduced iterations. **Deliverable**: `tests/integration/test_end_to_end.py` function `test_end_to_end_reduced_iterations()` that runs `run_simulation_robust.py` with **100 iterations** and asserts output files exist and contain plausible values.

---

### Dependencies & Execution Order Summary

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3-5)** → **Cross‑Cutting (Phase 6)**
- All tasks marked `[P]` may run in parallel as long as they do not modify the same file.
- Validation tasks (e.g., T029, T039) run after the corresponding implementation tasks to verify compliance.
- **Critical Dependencies**:
 - T031 must complete before T026.
 - T035 must complete before T026.
 - T004 (Implementation) must complete before T023 (Implementation).
 - T023 (Implementation) must complete before T014, T021, T026.
 - T012, T013 must complete before T014.
 - T019, T020 must complete before T021.
 - T014 and T021 must complete before T025.
 - T025 must complete before T026.
 - T031 covers both runner and generator.
 - T027 (Monitoring) must be implemented before T026 to ensure FR-006 compliance.
 - T045 depends on T027.
 - T008 and T009 depend on T010 and T011 (moved to Phase 3).
 - T050 depends on T027.
 - T026 depends on T050.
 - T035 depends on T004.

---

### Notes

- All tasks now include concrete deliverables, file paths, and verification steps.
- The baseline naive t‑test is explicitly flagged as a methodological violation but retained for comparison, satisfying both the research need and Constitution Principle VI via T036.
- Dynamic configuration via CLI arguments ensures FR‑001 and FR‑005 are fully user‑configurable.
- Real‑world UCI data handling is now strictly synthetic (T035), complying with data‑hygiene and single‑source‑of‑truth principles.
- Memory and runtime constraints are actively enforced through profiling and sub‑sampling logic (T027, T045).
- Confidence‑interval selection is standardized to Clopper-Pearson for rigor.
- Edge cases for ICC=0.0 are explicitly handled to prevent invalid robust variance estimates.
- **Fixed**: Task T031 is now active and mandatory, ensuring Constitution Principle VII compliance and enabling T026.
- **Fixed**: Task T023 is now in Phase 2, ensuring CLI support is available before T014/T021.
- **Fixed**: Task T035 is now in Phase 2, ensuring synthetic parameters are available before T026, with explicit dependency on T004.
- **Fixed**: Task T027 is marked complete with explicit algorithm (halve count, max 3 retries).
- **Fixed**: Task T037 has been merged into T027 to eliminate redundancy.
- **Fixed**: Task T008 and T009 moved to Phase 3 to ensure tests are written against existing code, with explicit dependency tags.
- **Removed**: Phase 7 (Human Decision Simulation) and tasks T046, T047 have been removed as they were unauthorized scope creep not present in spec.md.
- **Removed**: T037 (separate memory optimization task) has been merged into T027.
- **NEW**: Added T050 to aggregate performance metrics for SC-003 verification.
