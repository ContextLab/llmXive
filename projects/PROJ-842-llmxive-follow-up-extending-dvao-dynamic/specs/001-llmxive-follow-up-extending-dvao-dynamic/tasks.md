# Tasks: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Input**: Design documents from `/specs/001-llmxive-noise-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for upstream artifacts)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Create `src/`, `tests/`, `data/`, `scripts/`, `docs/` directories and their subdirectories (`src/derivation`, `src/environment`, `src/heuristic`, `src/analysis`, `tests/unit`, `tests/contract`, `tests/integration`, `data/raw`, `data/processed`, `data/derived`) along with `__init__.py` files for all Python packages and `.gitkeep` files for data directories. **Verification**: Run `find. -type d -name "src" -o -name "tests" -o -name "data" -o -name "data/derived" | wc -l` and verify count is at least 11, then verify `__init__.py` exists in `src/`, `src/derivation/`, etc. **Note**: Implements Constitution Principle I (Reproducibility).

---
## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical memory optimizations to ensure a constrained memory environment is met from the start.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (a range of values including 5, 10, 20, 50), `k` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {0, 0.2, 0.5}), and `distributions` (Linear, Sparse, Non-Convex). **Exact Content**: The file must contain:
 ```yaml
n_objectives: [5, 10, 20, 50]
k_sweep: [, 0.05, 0.1]
seeds: [multiple random initializations]
noise_correlation: [0, 0.2, 0.5]
distributions: ["linear", "sparse", "non-convex"]
 ```
 **Verification**: Run `python -c "import yaml; d=yaml.safe_load(open('src/config/defaults.yaml')); assert d['n_objectives'] == [5, 10, 20, 50]; assert d['noise_correlation'] == [0, 0.2, 0.5]; assert d['k_sweep'] == [0.01, 0.05, 0.1]; assert d['distributions'] == ['linear', 'sparse', 'non-convex']"`

- [X] T015 [P] Implement `src/environment/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ across a range of values including the absence of correlation as required by FR-009, (3) deterministic seeded random state management. **Deliverable**: Class `SyntheticMDP` with `generate_mdp(n_objectives, seed)` method. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(5, seed=42); assert mdp.n_objectives == 5; assert len(mdp.state_space) >= 10; assert len(mdp.action_space) > 0"`

- [X] T015d-wiring [S] Implement `src/environment/synthetic_mdp.py` function `get_theoretical_noise_variance(n_objectives, noise_std)` AND the wiring logic in `src/environment/runner.py` to pass `theoretical_sigma_sq` to `src/analysis/stats.py`. **Deliverable**: Function `get_theoretical_noise_variance` returning scalar $\sigma^2$ AND updated runner/wiring function ensuring `stats.py` receives `sigma_sq`. **Verification**: Run `python -c "from src.environment.synthetic_mdp import get_theoretical_noise_variance; v = get_theoretical_noise_variance(5, 0.1); assert isinstance(v, float) and v > 0"` AND run `pytest tests/unit/test_wiring.py` which mocks the runner loop and asserts `stats.run_noise_sanity_check` is called with the correct `sigma_sq` argument.

- [X] T016 [P] Implement `src/heuristic/moving_window.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size). **Deliverable**: Function `estimate_variance(trajectory, window_size_k)` returning a float. **Verification**: Run `python -c "from src.heuristic.moving_window import estimate_variance; import numpy as np; traj = np.random.rand(100); assert estimate_variance(traj, 10) >= 0 "`

- [X] T017-core [P] Implement `src/environment/runner.py` with basic structure and main() function accepting --n-objectives, --seed, --noise-correlation arguments. **Deliverable**: Basic runner script skeleton. **Verification**: Run `python src/environment/runner.py --help`

- [X] T017c [P] Implement explicit 2-core enforcement logic in `src/environment/runner.py` using `os.sched_setaffinity` to pin the process to a minimal set of CPU cores and setting `OMP_NUM_THREADS=2`. **Deliverable**: Function `enforce_cpu_cores(cores=2)` raising an error if the system cannot support it or if the limit is exceeded. **Verification**: Run `python -c "import os; from src.environment.runner import enforce_cpu_cores; enforce_cpu_cores(); assert len(os.sched_getaffinity(0)) == 2 "`

- [X] T017a [S] Implement `src/environment/pareto_oracle.py` with a function `calculate_pareto_distance(policy_rewards, pareto_frontier)` using a weighted-sum sweep approximation for N > 10, and exact enumeration for N <= 5. **Deliverable**: Function returning float distance. **Verification**: Run `python -c "from src.environment.pareto_oracle import calculate_pareto_distance; import numpy as np; d = calculate_pareto_distance(np.array([1.0, 1.0]), np.array([[1.0, 1.0]])); assert d == 0.0"`

- [X] T086 [S] Refactor `src/environment/synthetic_mdp.py` to stream state space generation for N > 50: Instead of pre-allocating the entire state space matrix in memory, implement a generator `state_iterator()` that yields states one-by-one or in small batches to strictly adhere to the <7GB RAM constraint during the generation phase. **Deliverable**: Generator method `state_iterator()` and updated `generate_mdp` to use it. **Verification**: Run `python -c "import tracemalloc; tracemalloc.start(); from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(50, seed=42); list(mdp.state_iterator()); current, peak = tracemalloc.get_traced_memory(); assert peak < 7 * 1024 * 1024 * 1024 "`

- [X] T053 [P] Refactor `src/environment/runner.py` to use generators instead of lists for trajectory storage to ensure memory efficiency (<7GB) under large N. **Deliverable**: Generator-based trajectory iterator. **Verification**: Run with N=50 and confirm memory < 7GB using `tracemalloc`.

- [X] T055 [P] Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint. **Deliverable**: Batched variance calculation function. **Verification**: Run with 1M rows and verify peak memory < 7GB.

- [X] T061 [P] Create `src/environment/runner.py` with data-flow check function `check_data_flow_dependencies()` verifying existence of required input files before analysis. **Deliverable**: Function raising an error if files are missing. **Verification**: Unit test confirms the function raises the correct error.

- [X] T017-final [P] Integrate T053, T055, T017c, T061, T086 into `src/environment/runner.py` main() function. **Deliverable**: Final runner script with all constraints. **Verification**: Run `python src/environment/runner.py --n=50` and verify memory < 7GB and CPU cores = 2.

- [X] T018 [S] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i. **Deliverable**: Function `derive_variance_expression(N, epsilon)`

- [X] T018b [S] Export variance expression to JSON in `src/derivation/variance_scaling.py` & load in `src/derivation/sample_complexity.py`. **Exact Deliverable**: File `data/derived/variance_expr.json` with keys: `expression_str` (sympy string), `variables` (list of symbols), `timestamp`. **Constraint**: Must include a `--force-regenerate` flag or a pre-run check that deletes `variance_expr.json` if `src/derivation/sample_complexity.py` content hash has changed, ensuring 'Code as Truth'. **Verification**: Run `python -c "import json; d=json.load(open('data/derived/variance_expr.json')); assert 'expression_str' in d and d['variables']"`

- [X] T019a [S] Implement inversion logic in `src/derivation/sample_complexity.py` to calculate sample complexity bounds from variance equations (imported via T018b). **Deliverable**: Function `calculate_bound(variance_expr, N, epsilon, target_error)` returning a float. **Verification**: Run `python -c "from src.derivation.sample_complexity import calculate_bound; import json; d=json.load(open('data/derived/variance_expr.json')); b = calculate_bound(d['expression_str'], N=10, epsilon=0.1, target_error=0.05); assert isinstance(b, float) and b > 0"`

- [X] T019b [S] Implement string formatting for sample complexity bound in `src/derivation/sample_complexity.py`. **Deliverable**: Function `format_bound_report(bound, N, epsilon)` returning a Markdown string. **Verification**: Run `python -c "from src.derivation.sample_complexity import format_bound_report; s = format_bound_report(100.0, 5, 0.1); assert 'Sample Complexity' in s"`

- [X] T019c [S] Create `tests/unit/test_derivation.py` to verify the inversion logic and string formatting. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_derivation.py -v`.

- [X] T021a [S] Implement one-sample t-test in `src/analysis/stats.py` comparing mean deviation from theoretical bound against zero. **Deliverable**: Function `run_ttest(deviations, alpha=0.05)` returning p-value. **Verification**: Run `python -c "from src.analysis.stats import run_ttest; import numpy as np; p = run_ttest(np.zeros(10)); assert p == 1.0"`

- [X] T021b [S] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps. **Deliverable**: Function `check_stability(ratios)` returning bool. **Verification**: Run `python -c "from src.analysis.stats import check_stability; assert check_stability([1.0]*100)"`

- [X] T021c [S] Implement sensitivity analysis sweep for window size k in `src/analysis/stats.py`. **Deliverable**: Function `run_k_sweep(results, k_values)` that iterates over `k_values` and aggregates results. **Verification**: Run `python -c "from src.analysis.stats import run_k_sweep; import numpy as np; res = run_k_sweep([{'k': 0.01}], [0.01, 0.05]); assert len(res) == 2"`

- [X] T022 [P] Create `tests/unit/test_derivation.py`. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_derivation.py -v`.

- [X] T023 [P] Create `tests/unit/test_mdp.py`. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_mdp.py -v`.

- [X] T024 [P] Create `tests/unit/test_heuristic.py`. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_heuristic.py -v`.

- [X] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/`. **Deliverable**: Script. **Verification**: Run `python scripts/update_state.py`.

---
## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [S] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i. **Exact Content**: The output must match `N * epsilon**2` (or equivalent derived form). **Deliverable**: `tests/unit/test_derivation.py` contains a test `test_variance_expression` that asserts the output matches the expected form. **Verification**: Run `pytest tests/unit/test_derivation.py::test_variance_expression -v`.

- [S] T026b [US1] Execute symbolic math engine verification: **Create** `src/derivation/verify_symbolic.py` that parses the output of T026 (the sympy expression) and uses `sympy` to algebraically verify the consistency of the derived equation against the known variance accumulation rules. **Deliverable**: `data/derived/verification_log.json` containing `status: "PASS"` and `method: "sympy_algebra"`. **Verification**: Run `python src/derivation/verify_symbolic.py` and check `data/derived/verification_log.json` for `status: "PASS"`.

- [S] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound. **Test Case**: Run `calculate_bound(N=10, epsilon=0.1, target_error=0.05)`. **Expected Output**: A float value (e.g., 1000). **Deliverable**: `tests/unit/test_sample_complexity.py` contains a test `test_inversion` that asserts the result is within 5% of the expected analytical value. **Verification**: Run `pytest tests/unit/test_sample_complexity.py::test_inversion -v`.

- [S] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output. **Format**: Add JSON field `assumptions: ["i.i.d. noise"]` and generate `docs/theoretical_derivation.md` via `--generate-docs` flag. **Verification**: Run `python src/derivation/sample_complexity.py --generate-docs` and verify `docs/theoretical_derivation.md` contains a section generated from the code's assumptions list.

- [S] T029 [US1] Generate Theoretical Derivation Report: Execute `python src/derivation/sample_complexity.py --generate-docs` to create `docs/theoretical_derivation.md`. This task must integrate the symbolic verification (T026b) and the empirical validation logic. **Deliverable**: `docs/theoretical_derivation.md` containing the closed-form derivation, assumptions, and sample complexity bound. **Verification**: Run `python src/derivation/sample_complexity.py --generate-docs` and verify the file exists and contains the required sections.

---
## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {small, moderate, large}) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2
- [S] T031 [US2] Verify `src/environment/synthetic_mdp.py` generates correct tabular MDPs with N objectives (including N=5, 10, 20, 50) and noise correlation parameter ρ.

- [S] T031a [US2] Verify N=5 generation explicitly: Run `generate_mdp(n_objectives=5, seed=42)` and assert the resulting MDP has exactly 5 reward functions and valid state/action spaces.

- [S] T032 [US2] Verify `src/heuristic/moving_window.py` correctly calculates variance using only last k steps

- [S] T033 [US2] Verify `src/environment/runner.py` with memory footprint checks and CPU constraints, ensuring it uses foundational MDP and heuristic modules.

- [S] T034 [US2] Add logic to handle edge case where N > 50. **Formula**: `new_S = max(minimum_threshold, The specific value to remove/generalize: 'a small number'

Rewritten passage:
The specific value to remove/generalize: 'a small number')` where `original_S = len(mdp.state_space)` before reduction. The theoretical bound used for comparison is `calculate_bound(N=original_N)` (from T019a) and is flagged as `degraded: true`. **Exact Implementation**: Modify `SyntheticMDP.generate_mdp` to return a dict with `degraded_flag` (bool), `effective_n` (int, original N), and `reduced_state_space_size` (int) when N > 50. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(60, seed=42); assert mdp.degraded_flag == True and mdp.effective_n == 60 and mdp.reduced_state_space_size < len(mdp.state_space) // 2"`

- [S] T034b [US2] Implement logging for state space reduction in `src/environment/runner.py`.

- [S] T034-cmds [US2] Implement reward generation functions for Linear, Sparse, and Non-Convex distributions in `src/environment/synthetic_mdp.py`. **Deliverable**: Functions `generate_linear_rewards`, `generate_sparse_rewards` (sparsity > 0.9), and `generate_non_convex_rewards`. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_non_convex_rewards; r = generate_non_convex_rewards(10); assert len(r) > 0"` AND run `pytest tests/unit/test_mdp.py::test_non_convex_generation -v`.

- [S] T035 [US2] Add logging calls to output empirical variance, distance to Pareto frontier, and final policy distance in `data/processed/empirical_results.json`. **Exact Deliverable**: JSON file with keys: `empirical_variance`, `distance_to_pareto`, `final_policy_distance`, `theoretical_bound`, `n_objectives`, `degraded_flag`. **Dependency**: Requires T035d-wiring, T034 (N>50 logic), and T017a (Pareto Oracle). **Verification**: Run the full N-sweep and verify the JSON file contains the expected keys and that `theoretical_bound` matches the value from T019a.

- [S] T035a [US2] Verify `pareto_oracle.py` invocation: Run a script that traces the execution of `runner.py` and confirms `calculate_pareto_distance` from T017a is called to compute `distance_to_pareto`. **Verification**: Run `python -c "import src.environment.runner as r; r.main(n=5, verify=True)"` and check logs for oracle call.

- [S] T035b [US2] Implement explicit logging of final policy distance from Pareto frontier in `src/environment/runner.py`.

- [S] T036 [US2] Extend `src/environment/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}).

- [S] T036a [US5] Add explicit logging of correlation matrix properties in `src/environment/synthetic_mdp.py`: When generating correlated noise (ρ > 0), log the actual achieved correlation matrix (or a summary statistic like mean off-diagonal) to the console and `data/processed/noise_properties.json` to verify the intended correlation structure was achieved. **Deliverable**: `data/processed/noise_properties.json` with keys `rho_target`, `rho_actual`, `correlation_matrix_summary`. **Verification**: Run `python src/environment/runner.py --noise-correlation=0.5` and check the log output and `noise_properties.json`.

- [S] T037 [US2] Verify MDP generation is deterministic with seeded random states.

- [S] T052b [US5] Run Noise Correlation Sweep: Execute a script that runs the full experiment suite for all `noise_correlation` values configured in `src/config/defaults.yaml`. **Deliverable**: Aggregated results in `data/processed/correlation_sweep_results.json`. **Verification**: Run `python src/environment/runner.py --run-sweep=correlation`.

- [S] T033b [US2] Run full N-sweep: Execute a script that runs the full experiment suite for all `n_objectives` values configured in `src/config/defaults.yaml`. **Deliverable**: `data/processed/n_sweep_results.json`.

---
## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation and sensitivity analysis on the Moving-Window Heuristic and noise scaling law.

**Independent Test**: The system outputs a statistical report containing p-values from the one-sample t-tests and a table showing how convergence rates change as k varies.

### Implementation for User Story 3
- [S] T060 [US3] Implement minimum window size enforcement in `src/heuristic/moving_window.py`. **Formula**: `min_k = 0.01 * rollout_size`. Raise `ValueError` if `k < min_k`. **Note**: Ensures the full sweep range {0.01, 0.05, 0.1} is valid and not blocked. **Verification**: Run `python -c "from src.heuristic.moving_window import estimate_variance; import numpy as np; estimate_variance(np.zeros(100), 1)"` and confirm it raises a `ValueError`.

- [S] T064 [US3] Verify the one-sample t-test implementation in `src/analysis/stats.py`.

- [S] T065 [US3] Verify the stability check implementation in `src/analysis/stats.py`.

- [S] T066a [US3] Implement `calculate_false_positive_rate` function in `src/analysis/stats.py` with signature `calculate_false_positive_rate(heuristic_stable_flags, deviation_flags)`. **Deliverable**: Function returning float. **Verification**: Run `python -c "from src.analysis.stats import calculate_false_positive_rate; r = calculate_false_positive_rate([True]*10, [False]*10); assert r == 0.0"`.

- [S] T066 [US3] Verify the false positive rate calculation in `src/analysis/stats.py`.

- [S] T067 [US3] Verify the final report generation and aggregation logic.

- [S] T073 [US3] Implement explicit coincidence check with tolerance in `src/analysis/stats.py`.

- [S] T073b [US3] Implement empirical convergence failure point calculation: Write a function `find_failure_point(results, bound_multiplier=1.5)` that finds the smallest N where `empirical_sample_count > theoretical_bound * bound_multiplier`. **Deliverable**: Function returning int N. **Verification**: Run `python -c "from src.analysis.stats import find_failure_point; r = find_failure_point({'5': 100, '10': 150, '20': 300}, 1.5); assert r == 10"` (assuming bounds scale linearly).

- [S] T074 [US3] Document 'Degraded' State Space Logic in `docs/theoretical_derivation.md`: Run `python src/derivation/sample_complexity.py --generate-docs` to generate the section explaining the handling of the theoretical bound when state space is reduced (N > 50). **Content Requirement**: The section must state: "For N > 50, the empirical state space is degraded to fit memory constraints, but the theoretical bound is calculated for the original N to preserve the scaling law's validity. The comparison flags this as 'degraded: true'. Runtime values are logged in `statistical_report.json`." **Verification**: Run `python src/derivation/sample_complexity.py --generate-docs` and verify the generated Markdown contains the required section and the string 'degraded: true' (e.g., `grep "degraded: true" docs/theoretical_derivation.md`).

- [S] T076 [US3] Verify the full experiment suite completes within the specified resource limits.

- [S] T077 [US3] Generate the final comprehensive report.

- [S] T078 [US3] Verify the final report against all success criteria.

- [S] T080-runtime [US3] Implement runtime logging of effective N and reduced state space size to `data/processed/statistical_report.json` and console. **Deliverable**: Updated `stats.py` or `runner.py` to write `effective_n`, `reduced_state_space_size`, and `degraded_flag` to the final report JSON. **Verification**: Run `python src/environment/runner.py --n=60` and check `data/processed/statistical_report.json` for the new keys, and verify the values match the runtime degradation logic.

---
## Phase 6: User Story 4 - Validation Independence & Construct Validity (Priority: P4)

**Goal**: Generate a held-out set of reward functions with a different noise distribution and verify the scaling law holds across diverse reward landscapes.

**Independent Test**: The system outputs a report showing the results of a Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N for each ρ value, with a pass criterion of p > 0.05 for ρ=0.

### Implementation for User Story 4
- [S] T068a [US4] Generate held-out set with heavy-tailed noise. **Deliverable**: `data/derived/heavy_tailed_set.json`. **Verification**: Run `python -c "import json; d = json.load(open('data/derived/heavy_tailed_set.json')); assert len(d) > 0"`
- [S] T068b [US4] Verify heavy-tailed noise distribution. **Deliverable**: `data/derived/heavy_tailed_verification.json` with `status: "PASS"`. **Verification**: Run `python src/environment/verify_distribution.py` and check `data/derived/heavy_tailed_verification.json`.
- [S] T068c [US4] Create a separate 'held-out' validation set from T068a's generated heavy-tailed noise, explicitly marking it as a 'validation set' and ensuring it's distinct from the training data used throughout the remainder of the experiments. **Deliverable**: `data/derived/heavy_tailed_validation_set.json`. **Verification**: Verify the file exists and is separate from the training data.
- [S] T069 [US4] Verify the held-out set generation and noise distribution parameters.
- [S] T071 [US4] Verify the construct validity across Linear, Sparse, and Non-Convex distributions.

---
## Phase 7: User Story 5 - Sensitivity Analysis on Noise Correlation (Priority: P5)

**Goal**: Perform a sensitivity analysis on the noise correlation structure by introducing controlled correlations (ρ ∈ {0, 0.2, 0.5}) and verifying if the scaling law holds.

**Independent Test**: The system outputs a report showing the results of a Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N for each ρ value, with a pass criterion of p > 0.05 for ρ=0.

### Implementation for User Story 5
- [S] T052b-agg [US5] Aggregate Correlation Sweep Results: Consolidate results from T036 and T052b into a single structured dataset for analysis. **Deliverable**: `data/derived/correlation_sweep_aggregated.json` containing per-ρ statistics. **Verification**: Run `python -c "import json; d=json.load(open('data/derived/correlation_sweep_aggregated.json')); assert 'rho_0' in d and 'rho_0.5' in d"`.
- [S] T052c [US5] Implement Kolmogorov-Smirnov (KS) goodness-of-fit test for the slope of sample complexity vs N using the aggregated data from T052b-agg. **Deliverable**: Function `run_ks_test(aggregated_data)` returning p-values per ρ. **Verification**: Run `python -c "from src.analysis.stats import run_ks_test; import json; d=json.load(open('data/derived/correlation_sweep_aggregated.json')); p = run_ks_test(d); assert 'rho_0' in p"`
- [S] T052d-merge [US5] Aggregate and Merge KS Test Results: Combine the KS test results from T052c into the `statistical_report.json` file, ensuring the final report includes the pass/fail status for the ρ=0 criterion. **Deliverable**: Updated `data/processed/statistical_report.json` with `ks_test_results`. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/statistical_report.json')); assert 'ks_test_results' in d"`

---
## Phase 8: Final Validation & Reporting (Priority: P6)

**Goal**: Final validation and reporting of the entire experiment suite.

**Independent Test**: The system outputs a comprehensive report containing all statistical results, sensitivity analysis, and validation independence checks.

### Implementation for User Story 6
- [S] T082 [US6] Execute Construct Validity & Validation Independence Analysis.

- [X] T076 [US6] Verify the full experiment suite completes within the specified resource limits.
- [X] T077 [US6] Generate the final comprehensive report.
- [X] T078 [US6] Verify the final report against all success criteria.