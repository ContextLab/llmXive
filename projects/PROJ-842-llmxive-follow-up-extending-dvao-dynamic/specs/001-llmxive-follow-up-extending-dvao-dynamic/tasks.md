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

- [X] T001 [P] Initialize project directory structure: Create `src/`, `tests/`, `data/`, `scripts/`, `docs/` directories and their subdirectories (`src/derivation`, `src/environment`, `src/heuristic`, `src/analysis`, `tests/unit`, `tests/contract`, `tests/integration`, `data/raw`, `data/processed`) along with `__init__.py` files for all Python packages and `.gitkeep` files for data directories. **Verification**: Run `find. -type d -name "src" -o -name "tests" -o -name "data" | wc -l` and verify count is at least 10, then verify `__init__.py` exists in `src/`, `src/derivation/`, etc. **Note**: Implements Constitution Principle I (Reproducibility).

---
## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical memory optimizations to ensure a constrained memory environment is met from the start.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (a range of values including 5, 10, 20, 50), `k` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {0, 0.2, 0.5}), and `distributions` (Linear, Sparse, Non-Convex). **Exact Content**: The file must contain:
 ```yaml
n_objectives: [5, 10, 20, 50]
k_sweep: [0.01, 0.05, 0.1]
seeds: [42, 123, 456, 789, 101112]
noise_correlation: [0, 0.2, 0.5]
rollout_size: 2048
distributions: ["linear", "sparse", "non-convex"]
construct_validity_threshold: 0.10
 ```
 **Verification**: Run `python -c "import yaml; d=yaml.safe_load(open('src/config/defaults.yaml')); assert d['n_objectives'] == [5, 10, 20, 50]; assert d['noise_correlation'] == [0, 0.2, 0.5]; assert d['k_sweep'] == [0.01, 0.05, 0.1]; assert d['distributions'] == ['linear', 'sparse', 'non-convex']"`

- [X] T015 [P] Implement `src/environment/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ across a range of values including the absence of correlation as required by FR-009, (3) deterministic seeded random state management. **Deliverable**: Class `SyntheticMDP` with `generate_mdp(n_objectives, seed)` method. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(5, seed=42); assert mdp.n_objectives == 5; assert len(mdp.state_space) >= 10; assert len(mdp.action_space) > 0"`

- [X] T015d [P] Implement function `get_theoretical_noise_variance(n_objectives, noise_std)` in `src/environment/synthetic_mdp.py` that calculates the theoretical noise variance $\sigma^2$ based on the configured noise standard deviation and number of objectives, returning a float. **Deliverable**: Function `get_theoretical_noise_variance` returning the scalar $\sigma^2$. **Verification**: Run `python -c "from src.environment.synthetic_mdp import get_theoretical_noise_variance; v = get_theoretical_noise_variance(5, 0.1); assert isinstance(v, float) and v > 0 and abs(v - 0.01) < 1e-9"`

- [X] T016 [P] Implement `src/heuristic/moving_window.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size). **Deliverable**: Function `estimate_variance(trajectory, window_size_k)` returning a float. **Verification**: Run `python -c "from src.heuristic.moving_window import estimate_variance; import numpy as np; traj = np.random.rand(100); assert estimate_variance(traj, 10) >= 0 "`

- [X] T017-core [P] Implement `src/environment/runner.py` with basic structure and main() function accepting --n-objectives, --seed, --noise-correlation arguments. **Deliverable**: Basic runner script skeleton. **Verification**: Run `python src/environment/runner.py --help`

- [X] T017c [P] Implement explicit 2-core enforcement logic in `src/environment/runner.py` using `os.sched_setaffinity` to pin the process to a minimal set of CPU cores and setting `OMP_NUM_THREADS=2`. **Deliverable**: Function `enforce_cpu_cores(cores=2)` raising an error if the system cannot support it or if the limit is exceeded. **Verification**: Run `python -c "import os; from src.environment.runner import enforce_cpu_cores; enforce_cpu_cores(); assert len(os.sched_getaffinity(0)) == 2"`

- [X] T053 [P] Refactor `src/environment/runner.py` to use generators instead of lists for trajectory storage to ensure memory efficiency (<7GB) under large N. **Deliverable**: Generator-based trajectory iterator. **Verification**: Run with N=50 and confirm memory < 7GB using `tracemalloc`.

- [X] T055 [P] Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint. **Deliverable**: Batched variance calculation function. **Verification**: Run with 1M rows and verify peak memory < 7GB.

- [X] T061 [P] Implement data-flow check function `check_data_flow_dependencies()` in `src/environment/runner.py` verifying existence of required input files before analysis. **Deliverable**: Function raising an error if files are missing. **Verification**: Unit test confirms the function raises the correct error.

- [X] T017-final [P] Integrate T053, T055, T017c, T061 into `src/environment/runner.py` main() function. **Deliverable**: Final runner script with all constraints. **Verification**: Run `python src/environment/runner.py --n=50` and verify memory < 7GB and CPU cores = 2.

- [X] T018 [P] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i. **Deliverable**: Function `derive_variance_expression(N, epsilon)`

- [S] T018b [S] Export variance expression to JSON in `src/derivation/variance_scaling.py` & load in `src/derivation/sample_complexity.py`. **Exact Deliverable**: File `data/derived/variance_expr.json` with keys: `expression_str` (sympy string), `variables` (list of symbols), `timestamp`. **Verification**: Run `python -c "import json; d=json.load(open('data/derived/variance_expr.json')); assert 'expression_str' in d and d['variables']"`

- [S] T019a [S] Implement inversion logic in `src/derivation/sample_complexity.py` to calculate sample complexity bounds from variance equations (imported via T018b). **Exact Deliverable**: Function `calculate_bound(variance_expr, N, epsilon, target_error)` returning a float. **Verification**: Run `python -c "from src.derivation.sample_complexity import calculate_bound; b = calculate_bound(..., N=10, epsilon=0.1, target_error=0.05); assert isinstance(b, float) and b > 0"`

- [S] T019b [S] Implement string formatting for sample complexity bound in `src/derivation/sample_complexity.py`. **Deliverable**: Function `format_bound_report(bound, N, epsilon)` returning a Markdown string. **Verification**: Run `python -c "from src.derivation.sample_complexity import format_bound_report; s = format_bound_report(100.0, 5, 0.1); assert 'Sample Complexity' in s"`

- [X] T019c [P] Create `tests/unit/test_sample_complexity.py` to verify the inversion logic and string formatting. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_sample_complexity.py -v`.

- [X] T021d [P] Implement sanity check function `run_noise_sanity_check(empirical_variance, theoretical_sigma_sq)` in `src/analysis/stats.py`. **Deliverable**: Function returning a dict with `passed` (bool) and `ratio`. **Verification**: Run `python -c "from src.analysis.stats import run_noise_sanity_check; r = run_noise_sanity_check(0.01, 0.01); assert r['passed']"`

- [X] T021a [P] Implement one-sample t-test in `src/analysis/stats.py` comparing mean deviation from theoretical bound against zero. **Deliverable**: Function `run_ttest(deviations, alpha=0.05)` returning p-value. **Verification**: Run `python -c "from src.analysis.stats import run_ttest; import numpy as np; p = run_ttest(np.zeros(10)); assert p == 1.0"`

- [X] T021b [P] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps. **Deliverable**: Function `check_stability(ratios)` returning bool. **Verification**: Run `python -c "from src.analysis.stats import check_stability; assert check_stability([1.0]*100)"`

- [X] T021c [P] Implement sensitivity analysis sweep logic in `src/analysis/stats.py` for window size k. **Deliverable**: Function `sweep_k(results, k_values)` returning a table of results. **Verification**: Run `python -c "from src.analysis.stats import sweep_k; assert isinstance(sweep_k({}, [0.01]), dict)"`

- [X] T022 [P] Create `tests/unit/test_derivation.py`. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_derivation.py -v`.

- [X] T023 [P] Create `tests/unit/test_mdp.py`. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_mdp.py -v`.

- [X] T024 [P] Create `tests/unit/test_heuristic.py`. **Deliverable**: Pytest file. **Verification**: Run `pytest tests/unit/test_heuristic.py -v`.

- [X] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/`. **Deliverable**: Script. **Verification**: Run `python scripts/update_state.py`.

---
## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [S] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i. **Expected Form**: The output must match `N * epsilon**2` (or equivalent derived form). **Deliverable**: `tests/unit/test_derivation.py` contains a test `test_variance_expression` that asserts the output matches the expected form. **Verification**: Run `pytest tests/unit/test_derivation.py::test_variance_expression -v`.

- [X] T026b [US1] Execute symbolic math engine verification: Run a script that parses the output of T026 (the sympy expression) and uses `sympy` to algebraically verify the consistency of the derived equation against the known variance accumulation rules.

- [S] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound. **Test Case**: Run `calculate_bound(N=10, epsilon=0.1, target_error=0.05)`. **Expected Output**: A float value (e.g., 1000). **Deliverable**: `tests/unit/test_sample_complexity.py` contains a test `test_inversion` that asserts the result is within 5% of the expected analytical value. **Verification**: Run `pytest tests/unit/test_sample_complexity.py::test_inversion -v`.

- [S] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output. **Format**: Add JSON field `assumptions: ["i.i.d. noise"]` and generate `docs/theoretical_derivation.md` via `--generate-docs` flag. **Verification**: Run `python src/derivation/sample_complexity.py --generate-docs` and verify `docs/theoretical_derivation.md` contains a section generated from the code's assumptions list. **Note**: The `--generate-docs` flag triggers the module to extract assumptions from its internal state and format them into the Markdown report, ensuring 'Code as Truth'.

- [S] T029 [US1] Generate Theoretical Derivation Report: Execute `python src/derivation/sample_complexity.py --generate-docs` to create `docs/theoretical_derivation.md`. This task must integrate the symbolic verification (T026b) and the inversion logic (T019a) to produce the final artifact required by SC-001. **Deliverable**: `docs/theoretical_derivation.md` containing the closed-form derivation, assumptions, and sample complexity bound. **Verification**: Run `python src/derivation/sample_complexity.py --generate-docs` and verify the file exists and contains the required sections.

---
## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {small, moderate, large}) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2
- [X] T031 [US2] Verify `src/environment/synthetic_mdp.py` generates correct tabular MDPs with N objectives (including N=5, 10, 20, 50) and noise correlation parameter ρ.

- [X] T031a [US2] Verify N=5 generation explicitly: Run `generate_mdp(n_objectives=5, seed=42)` and assert the resulting MDP has exactly 5 reward functions and valid state/action spaces.

- [X] T032 [US2] Verify `src/heuristic/moving_window.py` correctly calculates variance using only last k steps

- [X] T034 [US2] Add logic to handle edge case where N > 50. **Formula**: `new_S = max(minimum_threshold, original_S // 2)` where `original_S = len(mdp.state_space)` before reduction. The theoretical bound used for comparison is `calculate_bound(N=original_N)` (from T019a) and is flagged as `degraded: true`. **Note**: This ensures the bound remains valid for the model's domain while acknowledging the reduced state space.

- [X] T034a [US2] Implement logging for state space reduction in `src/environment/runner.py`.

- [X] T034b [US2] Update schemas to include `effective_n`, `reduced_state_space_size`, and `degraded_flag`.

- [X] T034c [US2] Implement generation of reward functions with "Sparse" (sparsity ratio > 0.9) and "Non-Convex" distributions.

- [X] T034e [US2] Implement generation of reward functions with "Linear" distribution baseline.

- [X] T034f [US2] Implement sensitivity analysis sweep for Sparse, Non-Convex, and Linear distributions in `src/analysis/stats.py`.

- [S] T035 [US2] Add logging calls to output empirical variance, distance to Pareto frontier, and final policy distance in `data/processed/empirical_results.json`. **Exact Deliverable**: JSON file with keys: `empirical_variance`, `distance_to_pareto`, `final_policy_distance`, `theoretical_bound`, `n_objectives`, `degraded_flag`. **Verification**: Run the full N-sweep and verify the JSON file contains the expected keys and that `theoretical_bound` matches the value from T019a.

- [S] T082 [US2] Execute Construct Validity & Validation Independence Analysis: Run the full experiment suite on the heavy-tailed noise set (T068) and the Sparse/Non-Convex distributions (T034c) to compare results against the theoretical bound (T019a). **Deliverable**: `data/processed/construct_validity_results.json` containing deviation metrics for each distribution. **Verification**: Run `python src/environment/runner.py --distribution=heavy_tailed` and verify the report shows deviation < 10% for all distributions (SC-006).

- [S] T035d [US2] Implement data flow wiring for sigma-squared: Ensure `runner.py` passes the `theoretical_sigma_sq` from `synthetic_mdp.py` (T015d) to `stats.py` (T021d) for the sanity check. **Deliverable**: Updated `runner.py` main loop passing `sigma_sq` to analysis functions. **Verification**: Run `python -c "from src.environment.runner import run; run(n=5, seed=42); assert 'sigma_sq' in globals()"` (mock check).

- [X] T035b [US2] Implement explicit logging of final policy distance from Pareto frontier in `src/environment/runner.py`.
- [X] T061 [US2] Implement Data Flow Dependency Check: Modify `src/environment/runner.py` to include a runtime assertion that verifies the existence of required input files before proceeding with analysis.
- [X] T036 [US2] Extend `src/environment/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}).
- [X] T037 [US2] Verify MDP generation is deterministic with seeded random states.
- [X] T052b [US2] Run Noise Correlation Sweep.
- [X] T052c [US2] Implement Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N across correlation levels.
- [X] T033 [US2] Verify `src/environment/runner.py` with memory footprint checks and CPU constraints, ensuring it uses foundational MDP and heuristic modules.
- [X] T033b [US2] Run full N-sweep: Execute a script that runs the full experiment suite for all `n_objectives` values configured in `src/config/defaults.yaml`.

- [S] T083 [US2] Verify Data Flow for Theoretical Inputs: Execute a script that verifies `runner.py` correctly fetches `theoretical_sigma_sq` (T015d) and `theoretical_bound` (T019a) and passes them to the analysis module for the t-test comparison (FR-015). **Verification**: Run `python -c "from src.environment.runner import run; run(n=5, seed=42); assert 'sigma_sq' in globals() and 'theoretical_bound' in globals()"` (mock check).

---
## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation and sensitivity analysis on the Moving-Window Heuristic and noise scaling law.

**Independent Test**: The system outputs a statistical report containing p-values from the one-sample t-tests and a table showing how convergence rates change as k varies.

### Implementation for User Story 3
- [S] T060 [US3] Implement minimum window size enforcement in `src/heuristic/moving_window.py`. **Formula**: `The minimum number of selected rollouts, $k$, is determined by a threshold function that ensures a non-zero lower bound scaled by the rollout size, preventing degenerate cases while maintaining a proportional sampling strategy. This approach aligns with adaptive selection mechanisms described in prior work (arXiv:2305.14233).`. Raise `ValueError` if `k < min_k`. **Note**: Ensures the full sweep range {low, medium, high} is valid.

- [X] T062 [US3] Implement sensitivity analysis sweep for window size k in `src/analysis/stats.py`.

- [S] T063 [US3] Implement final report generation with statistical results. **Exact Deliverable**: `data/processed/statistical_report.json` with keys: `p_value_t_test`, `sensitivity_table`, `coincidence_flag`, `failure_point_N`. **Verification**: Run the full suite and verify the report contains all required fields.

- [X] T064 [US3] Verify the one-sample t-test implementation in `src/analysis/stats.py`.
- [X] T065 [US3] Verify the stability check implementation in `src/analysis/stats.py`.
- [X] T066 [US3] Verify the false positive rate calculation in `src/analysis/stats.py`.
- [X] T067 [US3] Verify the final report generation and aggregation logic.

- [S] T084 [US3] Verify Sweep Range Coverage: Execute a script that verifies the sweep logic (T062) covers the full range {0.01, 0.05, 0.1} for all configured rollout sizes, ensuring no hardcoded `min_k` blocks the lower bound. **Verification**: Run `python src/analysis/stats.py --verify-sweep` and confirm the output shows all k values were tested.

---
## Phase 6: User Story 4 - Validation Independence & Construct Validity (Priority: P4)

**Goal**: Generate a held-out set of reward functions with a different noise distribution and verify the scaling law holds across diverse reward landscapes.

**Independent Test**: The system successfully generates a held-out dataset with non-Gaussian noise and reports that the scaling law deviation remains within 10% of the theoretical bound.

### Implementation for User Story 4
- [X] T068 [US4] Implement generation of held-out set with heavy-tailed noise in `src/environment/synthetic_mdp.py`.
- [X] T069 [US4] Verify the held-out set generation and noise distribution parameters.
- [X] T071 [US4] Verify the construct validity across Linear, Sparse, and Non-Convex distributions.

---
## Phase 7: User Story 5 - Sensitivity Analysis on Noise Correlation (Priority: P5)

**Goal**: Perform a sensitivity analysis on the noise correlation structure by introducing controlled correlations (ρ ∈ {0, 0.2, 0.5}) and verifying if the scaling law holds.

**Independent Test**: The system outputs a report showing the results of a Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N for each ρ value, with a pass criterion of p > 0.05 for ρ=0.

### Implementation for User Story 5
- [S] T073 [US5] Implement the updated coincidence check with tolerance in `src/analysis/stats.py`.

- [S] T074 [US5] Document 'Degraded' State Space Logic in `docs/theoretical_derivation.md`: Run `python src/derivation/sample_complexity.py --generate-docs` to generate the section explaining the handling of the theoretical bound when state space is reduced (N > 50). **Content Requirement**: The section must state: "For N > 50, the empirical state space is degraded to fit memory constraints, but the theoretical bound is calculated for the original N to preserve the scaling law's validity. The comparison flags this as 'degraded: true'." **Verification**: Run `python src/derivation/sample_complexity.py --generate-docs` and verify the generated Markdown contains the required section.

- [S] T075 [US5] Run Final Coincidence Check with Tolerance: Execute the full suite with the updated coincidence check (T073) and verify the final report, ensuring the coincidence check logic with tolerance works correctly for all N values.

---
## Phase 8: Final Validation & Reporting (Priority: P6)

**Goal**: Final validation and reporting of the entire experiment suite.

**Independent Test**: The system outputs a comprehensive report containing all statistical results, sensitivity analysis, and validation independence checks.

### Implementation for User Story 6
- [X] T076 [US6] Verify the full experiment suite completes within the specified resource limits.
- [X] T077 [US6] Generate the final comprehensive report.
- [X] T078 [US6] Verify the final report against all success criteria.

---
## Phase 9: Revision & Analysis Resolution

**Purpose**: Address specific concerns raised by the analysis phase regarding data flow, robustness, and edge cases.

- [ ] T085 [S] [US3] Implement explicit "Fail Loudly" logic in `src/environment/synthetic_mdp.py`: Remove any `try/except` blocks that might fallback to synthetic data if the primary random generation fails. Ensure that any failure in seed initialization or state space creation raises a `RuntimeError` with a clear message, preventing silent data fabrication. **Verification**: Run a test that forces a seed error and confirms the process exits with a non-zero code and error message.
- [ ] T086 [S] [US2] Refactor `src/environment/synthetic_mdp.py` to stream state space generation for N > 50: Instead of pre-allocating the entire state space matrix in memory, implement a generator that yields states one-by-one or in small batches to strictly adhere to the <7GB RAM constraint during the generation phase. **Verification**: Run `python -c "import tracemalloc; tracemalloc.start(); from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(50, seed=42); list(mdp.state_iterator()); current, peak = tracemalloc.get_traced_memory(); assert peak < 7 * 1024 * 1024 * 1024"`
- [ ] T087 [S] [US5] Add explicit logging of correlation matrix properties in `src/environment/synthetic_mdp.py`: When generating correlated noise (ρ > 0), log the actual achieved correlation matrix (or a summary statistic like mean off-diagonal) to the console and `data/processed/noise_properties.json` to verify the intended correlation structure was achieved. **Verification**: Run `python src/environment/runner.py --noise-correlation=0.5` and check the log output for the correlation verification line.
- [ ] T088 [S] [US3] Implement a "Minimum Window Size" sanity check in `src/heuristic/moving_window.py`: Before calculating variance, assert that `window_size_k` is greater than a configurable minimum (e.g., `min_k = 5` or `0.01 * rollout_size`). If `k` is too small, raise a `ValueError` with a message explaining the statistical instability, preventing degenerate variance estimates. **Verification**: Run `python -c "from src.heuristic.moving_window import estimate_variance; import numpy as np; estimate_variance(np.zeros(100), 1)"` and confirm it raises a `ValueError`.
- [ ] T089 [S] [US4] Create a dedicated validation script `scripts/validate_construct_validity.py`: This script must load the results from `data/processed/construct_validity_results.json` and `data/processed/empirical_results.json`, compare the deviations against the 10% threshold for all distributions (Linear, Sparse, Non-Convex, Heavy-Tailed), and output a clear PASS/FAIL summary. **Verification**: Run `python scripts/validate_construct_validity.py` and verify it outputs "PASS: All distributions within 10% deviation" or a detailed failure report.
