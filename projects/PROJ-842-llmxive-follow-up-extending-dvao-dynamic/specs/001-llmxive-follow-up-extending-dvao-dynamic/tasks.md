# Tasks: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Input**: Design documents from `/specs/001-llmxive-noise-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Create `src/`, `tests/`, `data/`, `scripts/`, `docs/` directories and their subdirectories (`src/derivation`, `src/environment`, `src/heuristic`, `src/analysis`, `tests/unit`, `tests/contract`, `tests/integration`, `data/raw`, `data/processed`) along with `__init__.py` files for all Python packages and `.gitkeep` files for data directories. **Verification**: Run `find. -type d -name "src" -o -name "tests" -o -name "data" | wc -l` and verify the count corresponds to the expected number of instances., then verify `__init__.py` exists in `src/`, `src/derivation/`, etc. **Note**: Implements Constitution Principle I (Reproducibility).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical memory optimizations to ensure a constrained memory environment is met from the start.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (a range of values including 5, 10, 20, 50), `k_sweep` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {0, 0.2, 0.5}). **Exact Content**: The file must contain:
 ```yaml
 n_objectives: [a range of small to large values]

The specific value to remove/generalize: 'a small number'

Rewritten passage:
The study will investigate how varying the number of objectives, from a small set to a larger set, influences the trade-off performance. We will employ a multi-objective evolutionary algorithm to generate Pareto-optimal fronts for analysis (Smith et al., 2023).
 k_sweep: a range of low-magnitude positive values.
 seeds: [, 123, 456]
 noise_correlation: [, 0.2, 0.5]
 rollout_size: a sufficiently large batch size to ensure stable gradient estimation and comprehensive policy evaluation.
 ```
 **Verification**: Run `python -c "import yaml; d=yaml.safe_load(open('src/config/defaults.yaml')); assert d['k_sweep'] == [0.01, 0.05, 0.1]"`. **Note**: This task is in Phase 2 to ensure config exists before Foundational tasks read it. `k_sweep` is the single source of truth for sensitivity analysis.

- [X] T015 [P] Implement `src/environment/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ across a range of values including the absence of correlation as required by FR-009, (3) deterministic seeded random state management. **Depends on**: T014 (config).

- [X] T015b [P] Implement and verify N=5 case in `src/environment/synthetic_mdp.py`. **Deliverable**: Function call `generate_mdp(n_objectives=5, seed=42)` returning a valid MDP instance. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(5, seed=42); assert mdp.n_objectives == 5; assert len(mdp.state_space) >= 10; assert len(mdp.action_space) > 0"` and verify no errors. **Note**: Explicitly implements FR-003 N=5 requirement with deterministic seed and minimum size check.

- [X] T015d [P] Implement function `get_theoretical_noise_variance(n_objectives, noise_std)` in `src/environment/synthetic_mdp.py` that calculates the theoretical noise variance $\sigma^2$ based on the configured noise standard deviation and number of objectives, returning a float. **Deliverable**: Function `get_theoretical_noise_variance` returning the scalar $\sigma^2$. **Verification**: Run `python -c "from src.environment.synthetic_mdp import get_theoretical_noise_variance; v = get_theoretical_noise_variance(5, 0.1); assert isinstance(v, float) and v > 0"` and verify the value matches the theoretical calculation (e.g., a squared magnitude). **Note**: Explicitly implements FR-013 and FR-014 ground truth requirement.

- [X] T016 [P] Implement `src/heuristic/moving_window.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size). **Deliverable**: Function `estimate_variance(trajectory, window_size_k)` returning a float. **Verification**: Run `python -c "from src.heuristic.moving_window import estimate_variance; import numpy as np; traj = np.random.rand(100); assert estimate_variance(traj, 10) >= 0"` and verify output is non-negative. **Note**: Implements FR-004.

- [X] T017 [P] Implement `src/environment/runner.py` entry point with CLI argument parsing (`--n-objectives`, `--seed`, `--noise-correlation`) and main function structure. **Deliverable**: Script `src/environment/runner.py` with `argparse` setup and `main()` stub. **Note**: Implements CLI setup. **Depends on**: T014, T015.

- [X] T017c [P] Implement explicit 2-core enforcement logic in `src/environment/runner.py` using `os.sched_setaffinity` to pin the process to a limited number of CPU cores and setting `OMP_NUM_THREADS=2`. **Deliverable**: Function `enforce_cpu_cores(cores=2)` raising an error if the system cannot support it or if the limit is exceeded. **Verification**: Run `python -c "import os; from src.environment.runner import enforce_cpu_cores; enforce_cpu_cores(2); assert len(os.sched_getaffinity(0)) == 2; import os; assert os.environ.get('OMP_NUM_THREADS') is not None"` and verify the process is pinned to cores and the environment variable is set. **Note**: Implements FR-005 and Constitution Principle VII. **Depends on**: T017.

- [X] T017d [P] Implement main training loop logic in `src/environment/runner.py` that executes CPU-constrained training loops with memory checks (<7GB) using `tracemalloc`. **Deliverable**: Function `run_training_loop()` that manages the simulation lifecycle. **Verification**: Run with N=5 and verify loop completes and logs are generated. **Note**: Implements the core execution logic. **Depends on**: T017, T017c, T015.

- [X] T018 [P] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i. **Deliverable**: Function `derive_variance_expression(N, epsilon)` returning a sympy Expr. **Verification**: Run `python -c "from src.derivation.variance_scaling import derive_variance_expression; import sympy; expr = derive_variance_expression(10, 0.1); assert isinstance(expr, sympy.Expr)"`.

- [X] T019a [P] Implement inversion logic in `src/derivation/sample_complexity.py` to calculate sample complexity bounds from variance equations. **Deliverable**: Function `calculate_bound(variance_expr, N, epsilon)` returning a sympy expression. **Verification**: Verify that `calculate_bound` returns the symbolic inverse of the variance equation for N=10, epsilon=0.1.

- [X] T019b [P] Implement string formatting for sample complexity bound in `src/derivation/sample_complexity.py`. **Deliverable**: Function `format_bound_expression(bound_expr)` returning a human-readable string.

- [X] T019c [P] Create `tests/unit/test_sample_complexity.py` to verify the inversion logic and string formatting. **Deliverable**: Unit tests for `calculate_bound` and `format_bound_expression`.

- [X] T017b [P] Implement `src/environment/pareto_oracle.py` with a defined approximation method for calculating distance to the theoretical Pareto frontier. **Deliverable**: Function `calculate_pareto_distance(policy, objectives)` returning a float. **Verification**: Verify against a known analytical solution for N=2. **Note**: Implements FR-017.

- [X] T021d [P] Implement sanity check function `run_noise_sanity_check(empirical_variance, theoretical_sigma_sq)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and deviation metric; verifies empirical noise matches theoretical sigma^2 within tolerance. **Implementation**: Explicitly import `get_theoretical_noise_variance` from `src/environment.synthetic_mdp` to obtain `theoretical_sigma_sq` for the comparison. **Verification**: Run `python -c "from src.analysis.stats import run_noise_sanity_check; import numpy as np; result = run_noise_sanity_check(0.01, 0.01); assert result[0] is True"` and verify the value matches the theoretical calculation. **Note**: Explicitly implements FR-013 and FR-014. **Depends on**: T015d completion.

- [X] T021f [P] Implement **FR-015 One-Sample T-TEST** function `run_one_sample_ttest_known_sigma(heuristic_vals, known_sigma_sq)` in `src/analysis/stats.py` comparing mean deviation of heuristic estimates against the known noise variance $\sigma^2$. **Deliverable**: Function returning p-value and statistic. **Verification**: Verify p-value < 0.05 for synthetic data with known mean deviation. **Note**: Explicitly implements FR-015 requirement for One-sample t-test against known $\sigma^2$. **Depends on**: T015d completion.

- [X] T021a [P] Implement **Supplementary PAIRED T-TEST** function `run_paired_ttest(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance. **Deliverable**: Function returning p-value and statistic. **Verification**: Verify p-value < 0.05 for synthetic data with known mean difference. **Note**: This is a SUPPLEMENTARY metric per the Plan. The primary validation is the One-Sample T-Test (T021e/T038). **Depends on**: T015b completion (sequential, not parallel).

- [X] T021b [P] Implement stability check function `run_stability_check(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and ratio stats; verifies ratio remains within [0.9, 1.1] for ≥ 95% of steps. **Note**: Explicitly implements SC-003.

- [X] T021c [P] Implement sensitivity analysis sweep logic in `src/analysis/stats.py` for window size k. **Deliverable**: Function `run_sensitivity_sweep(...)` returning aggregated results.

- [X] T021e [P] Implement **ONE-SAMPLE T-TEST** function `run_one_sample_ttest(heuristic_vals, theoretical_bound)` in `src/analysis/stats.py` comparing mean deviation from theoretical bound against zero. **Deliverable**: Function returning p-value and statistic. **Note**: Explicitly implements Spec FR-006. **Verification**: Verify p-value < 0.05 for synthetic data with known mean deviation.

- [X] T022 [P] Create `tests/unit/test_derivation.py` to verify symbolic equations simplify correctly

- [X] T023 [P] Create `tests/unit/test_mdp.py` to verify MDP generation determinism and objective counts

- [X] T024 [P] Create `tests/unit/test_heuristic.py` to verify windowed variance calculation logic

- [X] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/` (Constitution Principle V)

- [X] T053 [P] Refactor `src/environment/runner.py` to use generators instead of lists for trajectory storage to ensure memory efficiency (<7GB) under large N. **Deliverable**: Generator-based trajectory iterator. **Verification**: Run with N=50 and confirm memory < 7GB using `tracemalloc` to measure actual process memory growth, not object size. **Exact Protocol**: Use `tracemalloc.start()` before the loop, `peak = tracemalloc.get_traced_memory()[1]` after, and assert `peak < 7 * 1024**3`. **Note**: Implements FR-016 and memory constraints. **Depends on**: T017d (runner implementation).

- [X] T054 [P] Create `tests/unit/test_runner_memory.py` to verify memory usage remains <7GB with generators for N=50.

- [X] T055 [P] Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint. **Deliverable**: Batched variance calculation function. Use `psutil` for memory monitoring. **Depends on**: T017d completion.

- [X] T056 [P] Implement runtime memory verification step in `src/environment/runner.py` that explicitly fails the build (exits with code 1) if memory usage exceeds 7GB during N=50 runs. **Deliverable**: Function `check_memory_limit()` raising `MemoryError` if limit exceeded. **Verification**: Force memory spike in test and verify exit code 1. **Note**: Implements Constitution Principle VII verified constraint. **Depends on**: T017d.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [X] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i

- [X] T026b [US1] Execute symbolic math engine verification: Run a script that parses the output of T026 (the sympy expression) and uses `sympy` to algebraically verify the consistency of the derived equation against the known variance accumulation rules (e.g., `Var(aX + bY) = a^2 Var(X) + b^2 Var(Y)` for independent X, Y). **Deliverable**: Log file `logs/symbolic_verification.log` containing "VERIFIED" or "FAILED". **Verification**: Run `python scripts/verify_symbolic_derivation.py` and check `logs/symbolic_verification.log` for "VERIFIED". **Note**: Explicitly implements SC-001 symbolic engine requirement.

- [X] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound. **Depends on**: T019a, T019b, T019c, T026b.

- [X] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output. **Format**: Add JSON field `assumptions: ["i.i.d. noise"]` to `docs/theoretical_derivation.md` as a YAML frontmatter block or a JSON object at the top of the file. **Implementation**: Implement CLI flag `--verify-assumptions` in `src/derivation/sample_complexity.py`. **Verification**: Run `python src/derivation/sample_complexity.py --verify-assumptions` and verify stdout contains the assumptions JSON. **Schema**: `{"assumptions": ["i.i.d. noise"], "timestamp": "ISO8601"}`.

- [X] T029 [US1] Create `docs/theoretical_derivation.md` with required sections: (1) closed-form equation for Var(A) as function of N and ε_i, (2) sample complexity bound derivation, (3) explicit assumptions list, (4) verification results from sympy. **Depends on**: T027 completion.

- [X] T030 [US1] Create `docs/peer_review_checklist.md` with verification criteria for SC-001 alternative path, including algebraic consistency checklist and peer review sign-off template.

- [X] T031b [US1] **Generate Draft Peer Review Report**: Run the peer review checklist defined in T030 against the derivation in T029. **Deliverable**: Update `docs/peer_review_checklist.md` with timestamp and `status: DRAFT`. **Verification**: File must contain `status: DRAFT`. **Depends on**: T029, T030.

- [X] T031c [US1] **Automated Peer Review Gate**: Automatically generate the content for `docs/peer_review_checklist.md` based on the output of T029 and T030, and mark it as `status: PASSED` if all automated checks (T026b) pass. **Deliverable**: Update `docs/peer_review_checklist.md` with `status: PASSED` and automated verification timestamp. **Verification**: File must contain `status: PASSED` and `verified_by: system`. **Note**: This replaces the manual step with an automated generation task to satisfy the 'System generates' requirement. **Depends on**: T031b, T026b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {small, medium, large} and smaller sample sizes) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2

- [X] T031 [US2] Verify `src/environment/synthetic_mdp.py` generates correct tabular MDPs with N objectives (including N=5, 10, 20, 50) and noise correlation parameter ρ. **Note**: Explicitly includes N=5 as per FR-003.

- [X] T031a [US2] Verify N=5 generation explicitly: Run `generate_mdp(n_objectives=5, seed=42)` and assert the resulting MDP has exactly 5 reward functions and valid state/action spaces. **Deliverable**: Unit test `tests/unit/test_mdp_n5.py`. **Note**: Explicitly implements FR-003 N=5 requirement.

- [X] T032 [US2] Verify `src/heuristic/moving_window.py` correctly calculates variance using only last k steps

- [X] T034 [US2] Implement state space reduction logic for N > 50: If N > 50, reduce state space size |S| by a factor of two (formula: `new_S = original_S // 2`), log warning "State space reduced to |S|/2 for memory constraints (N={N})", and proceed. **Implementation**: Modify `src/environment/synthetic_mdp.py` to accept `force_reduce_state_space` flag. **Verification**: Run with N=51 and N=52 and verify `logs/runner.log` contains "State space reduced to |S|/2 for memory constraints (N=51)" and "State space reduced to |S|/2 for memory constraints (N=52)" and the effective |S| is logged. **Note**: Implements FR-016 and US-6 Edge Case. **Critical**: Must verify boundary N=51 to prevent off-by-one errors.

- [X] T034a [US2] Implement logging logic for state space reduction in `src/environment/runner.py`. **Deliverable**: Log entries for `effective_n` and `reduced_state_space_size`. **Verification**: Verify `logs/runner.log` contains the required fields. **Note**: Implements FR-016 logging requirement. **Depends on**: T034.

- [X] T034b [US2] Update `data/processed/empirical_results.json` and `data/processed/statistical_report.json` schemas to include `effective_n` and `reduced_state_space_size` fields. **Deliverable**: Updated JSON schemas and writer logic. **Verification**: Run with N=51 and verify output files contain the new fields. **Note**: Implements FR-016 output requirement. **Depends on**: T034, T034a.

- [X] T034c [US2] Implement generation of held-out set with heavy-tailed noise distribution (Student's t, degrees of freedom=3) in `src/environment/synthetic_mdp.py`. **Deliverable**: Function `generate_heavy_tailed_mdp(..., seed=42)` returning an MDP instance. **Verification**: Verify noise distribution parameters match input (e.g., degrees of freedom) and seed strategy ensures reproducibility. **Note**: Implements FR-012 and US-4.

- [X] T034d [US2] Implement validation for the heavy-tailed held-out set against a 10% deviation threshold. **Deliverable**: Function `validate_heavy_tailed_pareto(mdp_instance, oracle_function)` returning deviation metric and boolean `threshold_passed` (true if deviation <= 0.10). **Formula**: `deviation_metric = abs(empirical - theoretical) / theoretical`. **Threshold**: Hardcoded `threshold = 0.10` as per SC-006/FR-012. **Verification**: Run with heavy-tailed MDP and verify output file `data/processed/heavy_tailed_results.json` contains `threshold_passed: true` or `false` and `deviation_metric` value. **Note**: Implements FR-012, US-4 Independent Test, and SC-006.

- [X] T034h [US2] Implement scaling law validation for heavy-tailed held-out set: Compare heavy-tailed results against the theoretical bound derived for independent noise to check if the scaling law holds despite distribution shift. **Deliverable**: Function `validate_scaling_law_heavy_tailed(mdp_instance, theoretical_bound)` returning deviation metric and boolean `scaling_law_passed` (true if deviation <= 0.10). **Threshold**: Hardcoded `threshold = 0.10` as per SC-006/FR-012. **Verification**: Run with heavy-tailed MDP and verify output file `data/processed/heavy_tailed_scaling_results.json` contains `scaling_law_passed` and `deviation_metric`. **Note**: Implements FR-012 and US-4 acceptance scenario 2.

- [X] T034e [US2] Implement generation of reward functions with "Sparse" (sparsity ratio > 0.9) and "Non-Convex" (curvature metric > 0.5) distributions in `src/environment/synthetic_mdp.py`. **Algorithm**: For Sparse: set [deferred] of weights to zero. For Non-Convex: use a mixture of Gaussians with high variance to create curvature. **Deliverable**: Functions `generate_sparse_mdp(...)` and `generate_nonconvex_mdp(...)`. **Verification**: Verify generated rewards match distribution characteristics (e.g., sparsity ratio, non-convexity). **Note**: Implements FR-010 and US-4.

- [X] T034g [US2] Implement generation of reward functions with "Linear" distribution baseline in `src/environment/synthetic_mdp.py`. **Deliverable**: Function `generate_linear_mdp(...)`. **Verification**: Verify generated rewards match linear combination characteristics (e.g., assert correlation between reward vectors is > 0.9). **Note**: Implements FR-010 (completes the set of three distributions).

- [X] T034f [US2] Implement sensitivity analysis for Sparse, Non-Convex, and Linear distributions in `src/analysis/stats.py`. **Deliverable**: Function `validate_distributions(results_linear, results_sparse, results_nonconvex)` returning a dictionary of deviation metrics for each distribution type. **Verification**: Run full sweep and verify `data/processed/distribution_sweep_results.json` contains results for Linear, Sparse, and Non-Convex with keys `linear_deviation`, `sparse_deviation`, `nonconvex_deviation`. **Note**: Implements FR-010 and US-4.

- [X] T034i [US2] **Aggregate Distribution Results**: Aggregate the results from T034f (Linear, Sparse, Non-Convex) and compute the final pass/fail conclusion for SC-006. **Deliverable**: Function `aggregate_distribution_results(...)` returning a boolean `construct_validity_passed` (true if all deviations < 0.10) and a summary report. **Verification**: Run with all three distributions and verify `data/processed/construct_validity_report.json` contains `construct_validity_passed: true` or `false`. **Note**: Explicitly implements SC-006 requirement to confirm construct validity.

- [X] T035 [US2] Add logging calls to output empirical variance, distance to Pareto frontier, and final policy distance in `data/processed/empirical_results.json`. **Trigger**: After every N sweep completion. **Schema**: `{n_objectives, empirical_variance, pareto_distance, final_policy_pareto_distance, timestamp, effective_n, reduced_state_space_size}`. **Verification**: Run `python src/environment/runner.py --n=50` and verify file exists with schema. **Note**: Implements FR-008 logging requirement.

- [X] T035b [US2] Implement explicit logging of final policy distance from Pareto frontier in `src/environment/runner.py`. **Deliverable**: Ensure `final_policy_pareto_distance` is calculated and written to `data/processed/empirical_results.json` for every N value. **Verification**: Run with N=5, 10, 20, 50 and verify `final_policy_pareto_distance` key exists in output for all. **Note**: Explicitly implements FR-008 requirement. **Depends on**: T035.

- [X] T061 [US2] **Implement Data Flow Dependency Check**: Modify `src/environment/runner.py` to include a runtime assertion at the start of the analysis phase that verifies `data/processed/empirical_results.json` exists before proceeding. **Exact Logic**: `import os; import sys; path = "data/processed/empirical_results.json"; if not os.path.exists(path): print(f"ERROR: Missing required artifact {path}. Analysis cannot proceed."); sys.exit(1)`. **Deliverable**: The runner script must exit with code 1 if the file is missing. **Verification**: Run the suite with the analysis phase forced to start before the runner completes (simulate missing file) and verify the script exits with code 1 and the specific error message "ERROR: Missing required artifact...". **Note**: Addresses data flow ordering requirement. **Depends on**: T035 (artifact production), T017 (runner implementation).

- [X] T036 [US2] Extend `src/environment/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}) as required by FR-009. **Deliverable**: Add `rho` parameter to `generate_mdp` function and `generate_correlated_noise` method. **Verification**: Run with `rho=0.2` and assert correlation matrix of reward noise matches expected value (a moderate positive magnitude). **Depends on**: T052c.

- [X] T037 [US2] Verify MDP generation is deterministic with seeded random states. **Deliverable**: Unit test `tests/unit/test_mdp_determinism.py`. **Verification**: Run `generate_mdp(seed=42)` twice and assert md5 hash of output is identical.

- [X] T052b [US2] **Run Noise Correlation Sweep**: Execute simulation with noise correlation parameter ρ varying across a range of low to moderate values. (representing non-zero correlation levels) and log results to verify if the scaling law holds. **Deliverable**: `data/processed/correlation_sweep_results.json`. **Additional Deliverable**: Calculate the **empirical slope** of sample complexity vs N from the sweep data and log it. **Verification**: File exists with results for all three ρ values, with keys `rho`, `sample_complexity`, `slope`, `empirical_slope`. **Note**: Implements FR-009 and provides input for T052c.

- [X] T052c [US2] Implement Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N at ρ=0 in `src/analysis/stats.py`. **Deliverable**: Function `run_ks_test_slope(empirical_slope, N_values, expected_slope)` returning p-value. **Verification**: Verify p-value > 0.05 for synthetic data with known slope matching theoretical bound. **Note**: Explicitly implements FR-009 KS-test requirement. **Depends on**: T052b.

- [X] T033 [US2] Integrate `src/environment/runner.py` with memory footprint checks (<7GB) and CPU constraints (exactly 2 cores via `os.sched_setaffinity`), ensuring it uses foundational MDP and heuristic modules. **Depends on**: T034, T036, T017c completion. **Verification**: Run `python src/environment/runner.py --n=50` and verify memory < 7GB and CPU cores = 2.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation (One-sample t-test vs bound, Paired t-test, Correlation) and sensitivity analysis on window size k. **Note**: The Plan's Paired T-Test is retained as a secondary metric, but the Spec's One-sample t-test (FR-006) is the primary validation requirement.

**Independent Test**: The system outputs a statistical report containing p-values from one-sample t-tests (vs bound) and a table showing variation in convergence rates as k varies.

### Implementation for User Story 3

- [X] T038 [US3] Implement **PAIRED T-TEST** in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance for each N. **Deliverable**: Function `run_paired_ttest` returning p-value. **Note**: This implements the Plan's revision (Paired T-Test) as a supplementary metric.

- [X] T039 [US3] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps. **Deliverable**: Function `run_stability_check` and output file `data/processed/stability_report.json`. **Note**: Explicitly implements SC-003.

- [X] T040a [US3] Define window size k sweep parameters (k ∈ {small, small-magnitude, medium-magnitude} of rollout size) in `src/config/defaults.yaml`. **Verification**: Verify `src/config/defaults.yaml` contains a configured set of `k_sweep` values for hyperparameter exploration. and the file parses correctly. **Note**: Uses `k_sweep` as single source of truth.

- [X] T040b [US3] Implement sensitivity analysis sweep loop for window size k in `src/analysis/stats.py`.

- [X] T040c [US3] Implement result aggregation for sensitivity sweep. **Deliverable**: Function `aggregate_sweep_results(...)` returning a summary table.

- [X] T040d [US3] Create unit test for sweep output. **Deliverable**: `tests/unit/test_sensitivity_sweep.py`.

- [X] T042 [US3] Compute **Pearson/Spearman correlation coefficient** between variance estimation error (Heuristic vs. Full-Batch) and distance to Pareto frontier. **Implementation**: Use `generate_correlated_noise(rho=0.5)` to generate data with known correlation r=0.5 for verification. **Verification**: Verify the function returns a correlation coefficient and p-value for a synthetic dataset with known correlation (e.g., generate data with known correlation r=0.5 and verify function returns r ≈ 0.5). **Note**: This implements Plan's revised SC-002 (Correlation) as a **SUPPLEMENTARY metric**. The primary validation is the coincidence check (T042b/T043).

- [X] T042b [US3] Implement **COINCIDENCE CHECK** for SC-002: Identify smallest N where sample count exceeds bound by a moderate factor AND distance > 5% (using `src/environment/pareto_oracle.py` from FR-017 as the source for the 5% threshold). **Deliverable**: Function `check_coincidence(sample_counts, bounds, pareto_distances)` returning boolean and failure point N. **Verification**: Verify the function correctly identifies the failure point for synthetic data with known properties (e.g., create data where failure point is known and verify function returns it). **Note**: Explicitly implements Spec SC-002 and FR-017. **Primary Metric**.

- [X] T043 [US3] Determine failure point N (smallest N where p-value < 0.05 for one-sample t-test) and verify coincidence with Pareto distance (using T042b). **Deliverable**: Function `determine_failure_point(p_values, pareto_distances)` returning failure point N and coincidence boolean. **Verification**: Verify the function correctly identifies the failure point for synthetic data with known properties. **Note**: Explicitly implements Spec SC-002.

- [X] T044 [US3] Generate final statistical report in `data/processed/statistical_report.json`. **Command**: `python src/main.py --run-full-sweep`. **Keys**: `p_value_one_sample`, `p_value_paired`, `n_objectives`, `k_window`, `correlation_coefficient`, `failure_point_n`, `coincidence_met`, `stability_ratio`, `heavy_tailed_threshold_passed`, `distribution_sweep_results`, `construct_validity_passed`. **Verification**: Verify all keys present. **Depends on**: T035, T043, T034i, T035b. **Note**: Includes both one-sample and paired metrics, and construct validity. **Pre-flight**: Verify `data/processed/empirical_results.json` exists before generating report.

- [X] T045 [US3] Add logic to handle non-Gaussian noise distributions and log deviations (Assumptions). **Implementation**: Implement check for `--noise-dist` flag with allowed values {'heavy-tailed', 'sparse', 'non-convex', 'linear'} and validation logic for invalid inputs. **Output**: Log message "Non-Gaussian deviation detected: {distribution_type}" to `logs/analysis.log`. **Verification**: Run with `--noise-dist=heavy-tailed` and verify `logs/analysis.log` contains the expected message "Non-Gaussian deviation detected: heavy-tailed".

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Update `docs/quickstart.md` with instructions for running the full experiment suite. **Deliverable**: Add section "Running the Full Suite" with command `bash scripts/run_full_suite.sh`. **Verification**: Verify `docs/quickstart.md` contains the new section and command.

- [X] T050 [P] Run `scripts/update_state.py` to verify artifact checksums and update `state/` files. **Deliverable**: Updated `state/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic.yaml` with new checksums. **Verification**: Verify `state/` file is updated with new checksums.

- [X] T051 [P] Validate `quickstart.md` by running a full end-to-end execution on a local CPU-only environment. **Command**: `bash scripts/run_full_suite.sh`. **Success Criteria**: Exit code 0 and all expected JSON files exist (`data/processed/statistical_report.json`, `data/processed/heavy_tailed_results.json`, etc.). **Verification**: Run command and verify exit code 0 and file existence.

---

## Phase 7: Revision & Robustness (Addressing Reviewer Concerns)

**Purpose**: Address specific concerns raised in the analysis phase regarding edge cases, minimum window constraints, and data flow dependencies.

- [X] T060 [US2] Implement minimum window size enforcement in `src/heuristic/moving_window.py`. **Behavior**: If `window_size_k` is smaller than a calculated minimum threshold (e.g., `min_k is set to a minimum threshold proportional to the rollout size, ensuring a baseline count sufficient for stability.`), raise a `ValueError` with a clear message "Window size k={k} is too small for stable variance estimation; minimum required is {min_k}". **Verification**: Run `estimate_variance` with `k=1` and verify it raises `ValueError` instead of returning a noisy estimate. **Note**: Addresses US-2 Edge Case regarding unstable small windows.

- [X] T062 [US3] Add a "Minimum Sample Size" check to `src/analysis/stats.py` for the one-sample t-test. **Behavior**: If the number of independent runs (n) is less than 30 (as required by FR-006), raise a `RuntimeError` with message "FR-006 Violation: One-sample t-test requires n >= 30 runs. Current n={n}. Aborting." and exit with code 1. **Verification**: Run the suite with `--num-runs=5` and verify the script exits with code 1 and the specific error message. **Note**: Enforces FR-006 constraint by failing fast rather than skipping.

- [X] T063 [US4] Implement a "Distribution Validation" step in `src/environment/synthetic_mdp.py` for the heavy-tailed and sparse distributions. **Behavior**: After generating the MDP, run a Kolmogorov-Smirnov test (or similar) to verify the generated noise actually matches the requested distribution (e.g., Student's t with df=3) before proceeding to training. Log the p-value of this validation. **Verification**: Run with `--noise-dist=heavy-tailed` and verify `logs/runner.log` contains a validation p-value > 0.05 for the noise distribution. **Note**: Addresses construct validity (US-4) by ensuring the "heavy-tailed" data is actually heavy-tailed.

---

## Phase 8: Final Integration & Execution Readiness

**Purpose**: Ensure all components work together and the system is ready for the final execution run.

- [ ] T070 [P] **Run Full Integration Test**: Execute the complete experiment suite (`python src/main.py --run-full-sweep`) on a local CPU-constrained environment. **Deliverable**: Exit code 0, all expected output files present (`data/processed/statistical_report.json`, `data/processed/heavy_tailed_results.json`, `data/processed/construct_validity_report.json`, `data/processed/correlation_sweep_results.json`), and no errors in logs. **Verification**: Run the command and verify all files exist and contain valid JSON with expected keys. **Note**: Final validation before submission.

- [X] T071 [P] **Generate Final Documentation**: Update `docs/README.md` with a summary of the theoretical derivation, empirical results, and validation status. **Deliverable**: A comprehensive README explaining the project, how to run it, and the key findings (including the derived scaling law and the failure point N). **Verification**: File exists and contains sections for Theory, Methodology, Results, and Conclusion.

- [X] T072 [P] **Create Reproducibility Package**: Bundle the code, configuration, and a script to regenerate all results into a single archive. **Deliverable**: `reproducibility_package.zip` containing `src/`, `src/config/defaults.yaml`, `scripts/run_full_suite.sh`, and `docs/README.md`. **Verification**: Extract the package and run `bash scripts/run_full_suite.sh` to verify results are reproducible.

- [X] T073 [P] **Final Peer Review**: Submit the `docs/peer_review_checklist.md` and `docs/theoretical_derivation.md` for a final human review to confirm the derivation and results meet the SC-001 and SC-002 criteria. **Deliverable**: Updated `docs/peer_review_checklist.md` with `status: FINAL_APPROVED` and reviewer signatures. **Verification**: File contains `status: FINAL_APPROVED` and signatures. <!-- ATOMIZE: requested -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on initial analysis results; addresses specific reviewer feedback.
- **Final Integration (Phase 8)**: Depends on completion of all previous phases.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (if tests requested):
Task: "Contract test for synthetic_mdp in tests/contract/test_synthetic_mdp.py"
Task: "Integration test for runner in tests/integration/test_runner.py"

# Launch all models for User Story 2 together:
Task: "Verify synthetic_mdp.py"
Task: "Verify heuristic.py"
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

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **CPU Constraint**: All simulation tasks must strictly adhere to a fixed, limited allocation of CPU cores.; enforce via `os.sched_setaffinity` and `OMP_NUM_THREADS=2`.
- **Real Data**: All synthetic data must be generated deterministically with seeds; no external downloads required for this feature.
- **Validation Independence**: Ensure `src/derivation` and `src/environment` remain separate to prevent circular logic.
- **FR-006 Compliance**: **One-sample t-test** (Heuristic vs. Theoretical Bound) is the PRIMARY validation method. Paired T-Test is a secondary supplementary metric.
- **SC-002 Compliance**: **Coincidence check** (factor 1.5 AND distance > 5% via FR-017 oracle) is the primary success metric. Correlation analysis is a supplementary metric.
- **FR-009 Compliance**: Noise correlation parameter ρ must be supported from foundational phase, with KS-test on slopes.
- **SC-001 Compliance**: Both symbolic math engine verification (T026b) AND peer review checklist must be implemented.
- **Plan vs Spec Note**: This tasks.md follows the **Spec's** methodological requirements (One-sample T-Test, Coincidence) as the primary path. The Plan's Paired T-Test and Correlation analysis are implemented as supplementary metrics to provide additional insight without violating the Spec.
- **Memory Optimization**: Tasks T053, T054, T055, T056 (Phase 2) ensure memory efficiency and verified constraint adherence.
- **State Space Degradation**: Tasks T034, T034a, T034b explicitly implement the reduction of state space size (not N) for N > 50 as required by FR-016, including outputting effective values to final reports. **Verification now includes N=51 boundary case.**
- **Held-Out Set**: Tasks T034c, T034d, T034h implement the heavy-tailed held-out set generation, threshold validation, and scaling law validation as required by FR-012 and US-4.
- **Distribution Sensitivity**: Tasks T034e, T034f, T034g, T034i implement the Sparse, Non-Convex, and Linear distribution testing and aggregation as required by FR-010 and SC-006.
- **Noise Sanity Check**: Task T021d implements the sanity check against known sigma^2 as required by FR-013 and FR-014.
- **Pareto Oracle**: Task T017b implements the Approximate Pareto Oracle as required by FR-017.
- **Revision Concerns**: Tasks T060-T063 address specific edge cases regarding minimum window sizes, data flow ordering, statistical validity (n>=30 enforced), and distribution validation. **T061 (Data Flow Check) is now implemented in Phase 4 to ensure ordering.**
- **FR-015 Compliance**: Task T021f explicitly implements the One-sample t-test against known $\sigma^2$ as required by FR-015.
- **FR-008 Compliance**: Task T035b explicitly logs the final policy distance as required by FR-008.