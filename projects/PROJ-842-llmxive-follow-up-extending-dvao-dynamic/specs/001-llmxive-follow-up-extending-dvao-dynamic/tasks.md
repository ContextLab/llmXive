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

- [X] T001 [P] Initialize project directory structure: Create `src/`, `tests/`, `data/`, `scripts/`, `docs/` directories and their subdirectories (`src/derivation`, `src/environment`, `src/heuristic`, `src/analysis`, `tests/unit`, `tests/contract`, `tests/integration`, `data/raw`, `data/processed`) along with `__init__.py` files for all Python packages and `.gitkeep` files for data directories. **Verification**: Run `find. -type d -name "src" -o -name "tests" -o -name "data" | wc -l` and verify count is 7, then verify `__init__.py` exists in `src/`, `src/derivation/`, etc. **Note**: Implements Constitution Principle I (Reproducibility).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical memory optimizations to ensure a constrained memory environment is met from the start.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (a range of values including 5, 10, 20, 50), `k` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {0, 0.2, 0.5}), and `distributions` (Linear, Sparse, Non-Convex). **Exact Content**: The file must contain:
 ```yaml
n_objectives: [5, 10, 20, 50]
k_sweep: [0.01, 0.05, 0.1]
seeds: [42, 123, 456]
noise_correlation: [0, 0.2, 0.5]
rollout_size: 1000
distributions: ["linear", "sparse", "non-convex"]
 ```
 **Verification**: Run `python -c "import yaml; d=yaml.safe_load(open('src/config/defaults.yaml')); assert d['n_objectives'] == [5, 10, 20, 50]; assert d['noise_correlation'] == [0, 0.2, 0.5]; assert d['k_sweep'] == [0.01, 0.05, 0.1]; assert d['distributions'] == ['linear', 'sparse', 'non-convex']"`. **Note**: This task configures the parameters for the full sweep required by US-2, but the execution is handled by T033b.

- [X] T015 [P] Implement `src/environment/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ across a range of values including the absence of correlation as required by FR-009, (3) deterministic seeded random state management. **Depends on**: T014 (config).

- [X] T015b [P] Implement and verify N=5 case in `src/environment/synthetic_mdp.py`. **Deliverable**: Function call `generate_mdp(n_objectives=5, seed=42)` returning a valid MDP instance. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(5, seed=42); assert mdp.n_objectives == 5; assert len(mdp.state_space) >= 10; assert len(mdp.action_space) > 0"` and verify no errors. **Note**: Explicitly implements FR-003 N=5 requirement with deterministic seed and minimum size check.

- [X] T015d [P] Implement function `get_theoretical_noise_variance(n_objectives, noise_std)` in `src/environment/synthetic_mdp.py` that calculates the theoretical noise variance $\sigma^2$ based on the configured noise standard deviation and number of objectives, returning a float. **Deliverable**: Function `get_theoretical_noise_variance` returning the scalar $\sigma^2$. **Verification**: Run `python -c "from src.environment.synthetic_mdp import get_theoretical_noise_variance; v = get_theoretical_noise_variance(5, 0.1); assert isinstance(v, float) and v > 0 and abs(v - 0.01) < 1e-9"` and verify the value matches the theoretical calculation (e.g., `noise_std**2`). **Note**: Explicitly implements FR-013 and FR-014 ground truth requirement.

- [X] T016 [P] Implement `src/heuristic/moving_window.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size). **Deliverable**: Function `estimate_variance(trajectory, window_size_k)` returning a float. **Verification**: Run `python -c "from src.heuristic.moving_window import estimate_variance; import numpy as np; traj = np.random.rand(100); assert estimate_variance(traj, 10) >= 0"` and verify output is non-negative. **Note**: Implements FR-004.

- [X] T017c [P] Implement explicit 2-core enforcement logic in `src/environment/runner.py` using `os.sched_setaffinity` to pin the process to a minimal set of CPU cores and setting `OMP_NUM_THREADS=2`. **Deliverable**: Function `enforce_cpu_cores(cores=2)` raising an error if the system cannot support it or if the limit is exceeded. **Verification**: Run `python -c "import os; from src.environment.runner import enforce_cpu_cores; enforce_cpu_cores(); assert len(os.sched_getaffinity(0)) == 2"` and verify the process is pinned to 2 cores. **Note**: Implements FR-005 and Constitution Principle VII.

- [X] T061a [P] **Implement Data-Flow Check Function**: Implement the check function in `src/environment/runner.py` that verifies the existence of required input files (e.g., `data/processed/empirical_results.json`) before starting analysis. **Deliverable**: Function `check_data_flow_dependencies()` raising an error if files are missing. **Verification**: Unit test (T061b) confirms the function raises the correct error. **Note**: Implementation of the check logic only; verification is handled by T061b.

- [X] T053 [P] **Refactor Runner for Memory**: Refactor `src/environment/runner.py` to use generators instead of lists for trajectory storage to ensure memory efficiency (<7GB) under large N. **Deliverable**: Generator-based trajectory iterator. **Verification**: Run with N=50 and confirm memory < 7GB using `tracemalloc` to measure actual process memory growth, not object size. Use `tracemalloc` for verification. **Note**: Implements FR-016 and memory constraints. **Moved to Phase 2** to allow verification on complete runner.

- [X] T055 [P] Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint. **Deliverable**: Batched variance calculation function. Use `psutil` for memory monitoring. **Verification**: Run `process_batch` with 1M rows and verify peak memory < 7GB. **Note**: Moved to Phase 2 to allow concrete verification.

- [X] T017 [P] Implement `src/environment/runner.py` with main() function accepting --n-objectives, --seed, --noise-correlation arguments, executing CPU-constrained training loops with memory checks (<7GB) using `tracemalloc`, and enforcing a specific number of CPU cores via `os.sched_setaffinity` and `OMP_NUM_THREADS=2` environment variables. **Depends on**: T053, T055, T017c, T061a completion. **Exit**: Exit with code 0 on success. **Note**: This task now includes the integration of the data-flow check from T061a and the sample size check from T062.

- [X] T018 [P] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i. **Deliverable**: Function `derive_variance_expression(N, epsilon)` returning a sympy Expr. **Verification**: Run `python -c "from src.derivation.variance_scaling import derive_variance_expression; import sympy; expr = derive_variance_expression(10, 0.1); assert isinstance(expr, sympy.Expr)"`.

- [X] T019a [P] Implement inversion logic in `src/derivation/sample_complexity.py` to calculate sample complexity bounds from variance equations. **Deliverable**: Function `calculate_bound(variance_expr, N, epsilon)` returning a sympy expression. **Verification**: Verify that `calculate_bound` returns the symbolic inverse of the variance equation for N=10, epsilon=0.1.

- [X] T019b [P] Implement string formatting for sample complexity bound in `src/derivation/sample_complexity.py`. **Deliverable**: Function `format_bound_expression(bound_expr)` returning a human-readable string.

- [X] T019c [P] Create `tests/unit/test_sample_complexity.py` to verify the inversion logic and string formatting. **Deliverable**: Unit tests for `calculate_bound` and `format_bound_expression`.

- [X] T017b [P] Implement `src/environment/pareto_oracle.py` with a defined approximation method for calculating distance to the theoretical Pareto frontier. **Deliverable**: Function `calculate_pareto_distance(policy, objectives)` returning a float. **Verification**: Verify against a known analytical solution for N=2. **Note**: Implements FR-017.

- [X] T021d [P] Implement sanity check function `run_noise_sanity_check(empirical_variance, theoretical_sigma_sq)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and deviation metric; verifies empirical noise matches theoretical sigma^2 within tolerance. **Verification**: Run `python -c "from src.analysis.stats import run_noise_sanity_check; import numpy as np; result = run_noise_sanity_check(0.0105, 0.01); assert result['passed'] == True and abs(result['deviation']) < 0.1"` and verify the function correctly identifies a match within tolerance. **Note**: Explicitly implements FR-013 and FR-014. **Depends on**: T015d.

- [X] T021a [P] Implement **ONE-SAMPLE T-TEST** function `run_one_sample_ttest(heuristic_vals, theoretical_bound)` in `src/analysis/stats.py` comparing mean deviation from theoretical bound against zero. **Deliverable**: Function returning p-value and statistic. **Verification**: Verify p-value < 0.05 for synthetic data with known mean deviation. **Note**: Explicitly implements Spec FR-006. **Depends on**: T015d.

- [X] T021b [P] Implement stability check function `run_stability_check(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and ratio stats; verifies ratio remains within [0.9, 1.1] for ≥ 95% of steps. **Note**: Explicitly implements SC-003.

- [X] T021c [P] Implement sensitivity analysis sweep logic in `src/analysis/stats.py` for window size k. **Deliverable**: Function `run_sensitivity_sweep(...)` returning aggregated results.

- [X] T021e [P] Implement **ONE-SAMPLE T-TEST** function `run_one_sample_ttest(heuristic_vals, theoretical_bound)` in `src/analysis/stats.py` comparing mean deviation from theoretical bound against zero. **Deliverable**: Function returning p-value and statistic. **Note**: Explicitly implements Spec FR-006. **Verification**: Verify p-value < 0.05 for synthetic data with known mean deviation. (Duplicate of T021a, kept for clarity in US3 context).

- [X] T022 [P] Create `tests/unit/test_derivation.py` to verify symbolic equations simplify correctly

- [X] T023 [P] Create `tests/unit/test_mdp.py` to verify MDP generation determinism and objective counts

- [X] T024 [P] Create `tests/unit/test_heuristic.py` to verify windowed variance calculation logic

- [X] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/` (Constitution Principle V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [X] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i

- [X] T026b [US1] Execute symbolic math engine verification: Run a script that parses the output of T026 (the sympy expression) and uses `sympy` to algebraically verify the consistency of the derived equation against the known variance accumulation rules (e.g., `Var(aX + bY) = a^2 Var(X) + b^2 Var(Y)` for independent X, Y). **Deliverable**: Log file `logs/symbolic_verification.log` containing "VERIFIED" or "FAILED". **Verification**: Run `python scripts/verify_symbolic_derivation.py` and check `logs/symbolic_verification.log` for "VERIFIED". **Note**: Explicitly implements SC-001 symbolic engine requirement.

- [X] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound. **Depends on**: T019a, T019b, T019c, T026b. **Note**: This task consumes the derivation output via import and serialization.

- [X] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output. **Format**: Add JSON field `assumptions: ["i.i.d. noise"]` to `docs/theoretical_derivation.md` as a YAML frontmatter block or a JSON object at the top of the file. **Implementation**: Implement CLI flag `--verify-assumptions` in `src/derivation/sample_complexity.py`. **Verification**: Run `python src/derivation/sample_complexity.py --verify-assumptions` and verify stdout contains the assumptions JSON. **Schema**: `{"assumptions": ["i.i.d. noise"], "timestamp": "ISO8601"}`.

- [X] T029 [US1] Create `docs/theoretical_derivation.md` with required sections: (1) closed-form equation for Var(A) as function of N and ε_i, (2) sample complexity bound derivation, (3) explicit assumptions list, (4) verification results from sympy. **Depends on**: T027 completion.

- [X] T030 [US1] Create `docs/peer_review_checklist.md` with verification criteria for SC-001 alternative path, including algebraic consistency checklist and peer review sign-off template.

- [X] T031b [US1] **Generate Draft Peer Review Report**: Run the peer review checklist defined in T030 against the derivation in T029. **Deliverable**: Update `docs/peer_review_checklist.md` with timestamp and `status: DRAFT`. **Verification**: File must contain `status: DRAFT`. **Depends on**: T029, T030.

- [X] T031c [US1] **Automated Peer Review Gate (Symbolic Path)**: Automatically generate the content for `docs/peer_review_checklist.md` based on the output of T029 and T030, and mark it as `status: PASSED` if all automated checks (T026b) pass. **Deliverable**: Update `docs/peer_review_checklist.md` with `status: PASSED` and automated verification timestamp. **Verification**: File must contain `status: PASSED` and `verified_by: system`. **Note**: This task covers the "Symbolic Math Engine" path of SC-001. **Depends on**: T031b, T026b.

- [X] T031d [US1] **Manual Peer Review Gate (Alternative Path)**: Implement a script or process to perform a manual or semi-automated peer review of the derivation steps as an alternative to the symbolic engine. **Deliverable**: Update `docs/peer_review_checklist.md` with `status: PASSED` and `verified_by: peer_review` if the manual review criteria are met. **Verification**: File must contain `status: PASSED` and `verified_by: peer_review`. **Note**: This task covers the "Peer Review Checklist" path of SC-001, ensuring the 'OR' condition is met. **Depends on**: T030.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {small, 20, 50}) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2

- [X] T031 [US2] Verify `src/environment/synthetic_mdp.py` generates correct tabular MDPs with N objectives (including N=5, 10, 20, 50) and noise correlation parameter ρ. **Note**: Explicitly includes N=5 as per FR-003.

- [X] T031a [US2] Verify N=5 generation explicitly: Run `generate_mdp(n_objectives=5, seed=42)` and assert the resulting MDP has exactly 5 reward functions and valid state/action spaces. **Deliverable**: Unit test `tests/unit/test_mdp_n5.py`. **Note**: Explicitly implements FR-003 N=5 requirement.

- [X] T032 [US2] Verify `src/heuristic/moving_window.py` correctly calculates variance using only last k steps

- [X] T034 [US2] Add logic to handle edge case where N > 50. **Behavior**: If N > 50, reduce state space size |S| by a factor of two [UNRESOLVED-CLAIM: c_c277ea9c — status=not_enough_info] (formula: `new_S = original_S // 2`), log warning "State space reduced to |S|/2 for memory constraints (N={N})", and proceed. **Implementation**: Modify `src/environment/synthetic_mdp.py` to accept `force_reduce_state_space` flag. **Verification**: Run with N=100 and verify `logs/runner.log` contains "State space reduced to |S|/2 for memory constraints (N=100)" and the effective |S| is logged. **Output Requirement**: The function MUST write the `effective_n` and `reduced_state_space_size` to `data/processed/empirical_results.json` and `data/processed/statistical_report.json` as required by FR-016. **Note**: Implements FR-016 and US-6 Edge Case.

- [X] T034a [US2] Implement logging logic for state space reduction in `src/environment/runner.py`. **Deliverable**: Log entries for `effective_n` and `reduced_state_space_size`. **Verification**: Verify `logs/runner.log` contains the required fields. **Note**: Implements FR-016 logging requirement. **Depends on**: T034.

- [X] T034b [US2] Update `data/processed/empirical_results.json` and `data/processed/statistical_report.json` schemas to include `effective_n` and `reduced_state_space_size` fields. **Deliverable**: Updated JSON schemas and writer logic. **Verification**: Run with N=51 and verify output files contain the new fields. **Note**: Implements FR-016 output requirement. **Depends on**: T034, T034a.

- [X] T034c [US2] Implement generation of held-out set with heavy-tailed noise distribution (Student's t, degrees of freedom=3) in `src/environment/synthetic_mdp.py`. **Deliverable**: Function `generate_heavy_tailed_mdp(..., seed=42)` returning an MDP instance. **Verification**: Verify noise distribution parameters match input (e.g., degrees of freedom) and seed strategy ensures reproducibility. **Note**: Implements FR-012 and US-4.

- [X] T034h [US2] **Generate persistent heavy-tailed dataset**: Generate and save the heavy-tailed held-out set to a file (e.g., `data/processed/heavy_tailed_mdp.json`) that T034d can consume. **Deliverable**: File `data/processed/heavy_tailed_mdp.json` containing the MDP instance data. **Verification**: Verify file exists and contains valid MDP data. **Note**: Provides the input artifact for T034d. **Implementation Note**: Must use a distinct RNG instance and seed offset `base_seed + 1000` to ensure independence from training set. **Verification Note**: Verify that the RNG state hash of the generated MDP differs from the training set MDP. **Depends on**: T031, T031a.

- [X] T034d [US2] Implement calculation of distance to theoretical Pareto frontier for the heavy-tailed held-out set and compare it to the % threshold (0.10) in `src/analysis/stats.py`. **Deliverable**: Function `validate_heavy_tailed_pareto(mdp_instance, oracle_function)` returning deviation metric and boolean `threshold_passed` (true if deviation <= 0.10). **Formula**: `deviation_metric = abs(empirical - theoretical) / theoretical`. **Behavior**: If the bound fails (deviation > 0.10), explicitly flag a "construct validity failure" in the output. **Verification**: Run with heavy-tailed MDP and verify output file `data/processed/heavy_tailed_results.json` contains `threshold_passed: true` or `false`, `deviation_metric` value, and a `construct_validity_failure` flag if applicable. **Note**: Implements FR-012, US-4 Independent Test, and SC-006. Explicitly compares against the independent-noise theoretical bound.

- [X] T034e [US2] Implement generation of reward functions with "Sparse" (sparsity ratio > 0.9) and "Non-Convex" (curvature metric > 0.5) distributions in `src/environment/synthetic_mdp.py`. **Algorithm**: For Sparse: set [deferred] of weights to zero. For Non-Convex: use a mixture of Gaussians with high variance to create curvature. **Deliverable**: Functions `generate_sparse_mdp(...)` and `generate_nonconvex_mdp(...)`. **Verification**: Verify generated rewards match distribution characteristics (e.g., sparsity ratio, non-convexity). **Note**: Implements FR-010 and US-4.

- [X] T034g [US2] Implement generation of reward functions with "Linear" distribution baseline in `src/environment/synthetic_mdp.py`. **Deliverable**: Function `generate_linear_mdp(...)`. **Verification**: Verify generated rewards match linear combination characteristics (e.g., assert correlation between reward vectors is > 0.9). **Note**: Implements FR-010 (completes the set of three distributions).

- [X] T034f [US2] Implement sensitivity analysis for Sparse, Non-Convex, and Linear distributions in `src/analysis/stats.py`. **Deliverable**: Function `validate_distributions(results_linear, results_sparse, results_nonconvex)` returning a dictionary of deviation metrics for each distribution type. **Verification**: Run full sweep and verify `data/processed/distribution_sweep_results.json` contains results for Linear, Sparse, and Non-Convex with keys `linear_deviation`, `sparse_deviation`, `nonconvex_deviation`. **Note**: Implements FR-010 and US-4.

- [X] T034i [US2] **Aggregate Distribution Results**: Aggregate the results from T034f (Linear, Sparse, Non-Convex) and compute the final pass/fail conclusion for SC-006. **Deliverable**: Function `aggregate_distribution_results(...)` returning a boolean `construct_validity_passed` (true if all deviations < 0.10) and a summary report. **Verification**: Run with all three distributions and verify `data/processed/construct_validity_report.json` contains `construct_validity_passed: true` or `false`. **Note**: Explicitly implements SC-006 requirement to confirm construct validity.

- [X] T035 [US2] Add logging calls to output empirical variance, distance to Pareto frontier, and final policy distance in `data/processed/empirical_results.json`. **Trigger**: After every N sweep completion. **Schema**: `{n_objectives, empirical_variance, pareto_distance, final_policy_pareto_distance, timestamp, effective_n, reduced_state_space_size}`. **Verification**: Run `python src/environment/runner.py --n=50` and verify file exists with schema. **Note**: Implements FR-008 logging requirement.

- [X] T035b [US2] Implement explicit logging of final policy distance from Pareto frontier in `src/environment/runner.py`. **Deliverable**: Ensure `final_policy_pareto_distance` is calculated and written to `data/processed/empirical_results.json` for every N value. **Verification**: Run with N=5, 10, 20, 50 and verify `final_policy_pareto_distance` key exists in output for all. **Note**: Explicitly implements FR-008 requirement. **Depends on**: T035.

- [X] T061 [US2] **Implement Data Flow Dependency Check**: Modify `src/environment/runner.py` to include a runtime assertion at the start of the analysis phase that verifies `data/processed/empirical_results.json` exists before proceeding. **Exact Logic**: `import os; import sys; path = "data/processed/empirical_results.json"; if not os.path.exists(path): print(f"ERROR: Missing required artifact {path}. Analysis cannot proceed."); sys.exit(1)`. **Deliverable**: The runner script must exit with code 1 if the file is missing. **Verification**: Run the suite with the analysis phase forced to start before the runner completes (simulate missing file) and verify the script exits with code 1 and the specific error message "ERROR: Missing required artifact...". **Note**: Addresses data flow ordering requirement. **Depends on**: T035 (artifact production), T017 (runner implementation).

- [X] T036 [US2] Extend `src/environment/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}) as required by FR-009. **Deliverable**: Add `rho` parameter to `generate_mdp` function and `generate_correlated_noise` method. **Verification**: Run with `rho=0.2` and assert correlation matrix of reward noise matches expected value (a moderate positive magnitude). **Depends on**: T052c.

- [X] T037 [US2] Verify MDP generation is deterministic with seeded random states. **Deliverable**: Unit test `tests/unit/test_mdp_determinism.py`. **Verification**: Run `generate_mdp(seed=42)` twice and assert md5 hash of output is identical.

- [X] T052b [US2] **Run Noise Correlation Sweep**: Execute simulation with noise correlation parameter ρ ∈ {0, 0.2, 0.5} and log results to verify if the scaling law holds. **Deliverable**: `data/processed/correlation_sweep_results.json`. **Additional Deliverable**: Calculate the **empirical slope** of sample complexity vs N from the sweep data and log it. **Verification**: File exists with results for all three ρ values, with keys `rho`, `sample_complexity`, `slope`, `empirical_slope`. **Note**: Implements FR-009 and provides input for T052c.

- [X] T052c [US2] Implement Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N at ρ=0 in `src/analysis/stats.py`. **Deliverable**: Function `run_ks_test_slope(empirical_slope, N_values, expected_slope)` returning p-value. **Verification**: Verify p-value > 0.05 for synthetic data with known slope matching theoretical bound. **Note**: Explicitly implements FR-009 KS-test requirement. **Depends on**: T052b.

- [X] T033 [US2] Verify `src/environment/runner.py` with memory footprint checks (<7GB) and CPU constraints (exactly 2 cores via `os.sched_setaffinity`), ensuring it uses foundational MDP and heuristic modules. **Depends on**: T034, T036, T017c completion. **Verification**: Run `python src/environment/runner.py --n=50` and verify memory < 7GB and CPU cores = 2.

- [X] T033b [US2] **Run full N-sweep**: Execute a script that runs the full experiment suite for all `n_objectives` values configured in `src/config/defaults.yaml` (5, 10, 20, 50) in a single automated run. **Deliverable**: `data/processed/full_sweep_results.json` containing aggregated results for all N values. **Verification**: Run `python scripts/run_full_sweep.py` and verify file exists with results for all N values. **Note**: Explicitly implements the requirement to validate the scaling law across the specified range.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation (One-sample t-test vs bound, Paired t-test, Correlation) and sensitivity analysis on window size k. **Note**: The Plan's Paired T-Test is retained as a secondary metric, but the Spec's One-sample t-test (FR-006) is the primary validation requirement.

**Independent Test**: The system outputs a statistical report containing p-values from one-sample t-tests (vs bound) and a table showing variation in convergence rates as k varies.

### Implementation for User Story 3

- [X] T038 [US3] Implement **ONE-SAMPLE T-TEST** in `src/analysis/stats.py` comparing mean deviation of Heuristic variance from the **Theoretical Bound** against zero. **Deliverable**: Function `run_one_sample_ttest_vs_bound(mean_deviation, theoretical_bound)` returning p-value. **Note**: This implements the Spec's FR-006 requirement as the primary validation metric.

- [X] T038b [US3] Implement **PAIRED T-TEST** (Supplementary) in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance for each N. **Deliverable**: Function `run_paired_ttest` returning p-value. **Note**: This implements the Plan's revision (Paired T-Test) as a supplementary metric only.

- [X] T039 [US3] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps. **Deliverable**: Function `run_stability_check` and output file `data/processed/stability_report.json`. **Note**: Explicitly implements SC-003.

- [X] T040a [US3] Define window size k sweep parameters (k ∈ {0.01, 0.05, 0.1} of rollout size) in `src/config/defaults.yaml`. **Verification**: Verify `src/config/defaults.yaml` contains `k_sweep: [0.01, 0.05, 0.1]` and the file parses correctly.

- [X] T040b [US3] Implement sensitivity analysis sweep loop for window size k in `src/analysis/stats.py`.

- [X] T040c [US3] Implement result aggregation for sensitivity sweep. **Deliverable**: Function `aggregate_sweep_results(...)` returning a summary table.

- [X] T040d [US3] Create unit test for sweep output. **Deliverable**: `tests/unit/test_sensitivity_sweep.py`.

- [X] T042 [US3] Compute **Pearson/Spearman correlation coefficient** between variance estimation error (Heuristic vs. Full-Batch) and distance to Pareto frontier. **Implementation**: Use `generate_correlated_noise(rho=0.5)` to generate data with known correlation r=0.5 for verification. **Verification**: Verify the function returns a correlation coefficient and p-value for a synthetic dataset with known correlation (e.g., generate data with known correlation r=0.5 and verify function returns r ≈ 0.5). **Note**: This implements Plan's revised SC-002 (Correlation) as a **SUPPLEMENTARY metric**. The primary validation is the coincidence check (T042b/T043).

- [X] T042b [US3] Implement **COINCIDENCE CHECK** for SC-002: Identify smallest N where sample count exceeds bound by a moderate factor AND distance > 5% (using `src/environment/pareto_oracle.py` from FR-017 as the source for the 5% threshold). **Deliverable**: Function `check_coincidence(sample_counts, bounds, pareto_distances)` returning boolean and failure point N. **Verification**: Verify the function correctly identifies the failure point for synthetic data with known properties (e.g., create data where failure point is known and verify function returns it). **Note**: Explicitly implements Spec SC-002 and FR-017. **Primary Metric**.

- [X] T043 [US3] Determine failure point N (smallest N where p-value < 0.05 for one-sample t-test) and verify coincidence with Pareto distance (using T042b). **Deliverable**: Function `determine_failure_point(p_values, pareto_distances)` returning failure point N and coincidence boolean. **Verification**: Verify the function correctly identifies the failure point for synthetic data with known properties. **Note**: Explicitly implements Spec SC-002.

- [X] T044 [US3] Generate final statistical report in `data/processed/statistical_report.json`. **Command**: `python src/main.py --run-full-sweep`. **Keys**: `p_value_one_sample`, `p_value_paired`, `n_objectives`, `k_window`, `correlation_coefficient`, `failure_point_n`, `coincidence_met`, `stability_ratio`, `heavy_tailed_threshold_passed`, `distribution_sweep_results`, `construct_validity_passed`. **Verification**: Verify all keys present. **Depends on**: T035, T043, T034i, T035b. **Note**: Includes both one-sample and paired metrics, and construct validity. **Pre-flight**: Verify `data/processed/empirical_results.json` exists before generating report.

- [X] T045 [US3] Add logic to handle non-Gaussian noise distributions and log deviations (Assumptions). **Implementation**: Implement check for `--noise-dist` flag with allowed values {'heavy-tailed', 'sparse', 'non-convex', 'linear'} and validation logic for invalid inputs. **Output**: Log message "Non-Gaussian deviation detected: {distribution_type}" to `logs/analysis.log`. **Verification**: Run with `--noise-dist=heavy-tailed` and verify `logs/analysis.log` contains the expected message "Non-Gaussian deviation detected: heavy-tailed".

- [X] T062 [US3] Add a "Minimum Sample Size" check to `src/analysis/stats.py` for the one-sample t-test. **Behavior**: If the number of independent runs (n) is less than 30 (as required by FR-006), raise a `RuntimeError` with message "FR-006 Violation: One-sample t-test requires n >= 30 runs [UNRESOLVED-CLAIM: c_194155d7 — status=not_enough_info]. Current n={n}. Aborting." and exit with code 1. **Integration**: This check must be called by the main execution flow in T017. **Verification**: Run the suite with `--num-runs=10` and verify the script exits with code 1 and the specific error message. **Note**: Enforces FR-006 constraint by failing fast rather than skipping.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Update `docs/quickstart.md` with instructions for running the full experiment suite. **Deliverable**: Add section "Running the Full Suite" with command `bash scripts/run_full_suite.sh`. **Verification**: Verify `docs/quickstart.md` contains the new section and command.

- [X] T050 [P] Run `scripts/update_state.py` to verify artifact checksums and update `state/` files. **Deliverable**: Updated `state/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic.yaml` with new checksums. **Verification**: Verify `state/` file is updated with new checksums.

- [X] T051 [P] Validate `quickstart.md` by running a full end-to-end execution on a local CPU-only environment. **Command**: `bash scripts/run_full_suite.sh`. **Success Criteria**: Exit code 0 and all expected JSON files exist (`data/processed/statistical_report.json`, `data/processed/heavy_tailed_results.json`, etc.). **Verification**: Run command and verify exit code 0 and file existence.

---

## Phase 7: Revision & Robustness (Addressing Reviewer Concerns)

**Purpose**: Address specific concerns raised in the analysis phase regarding edge cases, minimum window constraints, and data flow dependencies. **Note**: Memory verification tasks moved here to break circular dependencies.

- [X] T060 [US2] Implement minimum window size enforcement in `src/heuristic/moving_window.py`. **Behavior**: If `window_size_k` is smaller than a calculated minimum threshold (e.g., `min_k = max(1, 0.01 * rollout_size)`), raise a `ValueError` with a clear message "Window size k={k} is too small for stable variance estimation; minimum required is {min_k}". **Verification**: Run `estimate_variance` with `k=1` and verify it raises `ValueError` instead of returning a noisy estimate. **Note**: Addresses US-2 Edge Case regarding unstable small windows.

- [X] T061b [US2] **Unit Test Data-Flow Check**: Create a unit test that mocks the missing input file to verify that the check function from T061a raises the expected error. **Deliverable**: Unit test `tests/unit/test_data_flow_check.py`. **Verification**: Run test and confirm it raises `RuntimeError` when the file is missing. **Note**: Verifies the check logic without requiring the full runner or actual file existence.

- [X] T053b [P] **Unit Test Generator Logic**: Create a unit test that mocks the trajectory data to verify the generator logic from T053 without requiring the full runner. **Deliverable**: Unit test `tests/unit/test_runner_generators.py`. **Verification**: Run test and confirm it passes. **Note**: Self-contained verification of generator logic.

- [X] T054 [P] Create `tests/unit/test_runner_memory.py` to verify memory usage remains <7GB with generators for N=50. **Verification**: Run test and confirm pass. **Note**: Moved to Phase 7 to run after T053 and T017 are complete.

- [X] T056 [P] Implement runtime memory verification step in `src/environment/runner.py` that explicitly fails the build (exits with code 1) if memory usage exceeds 7GB during N=50 runs. **Deliverable**: Function `check_memory_limit()` raising `MemoryError` if limit exceeded. **Verification**: Force memory spike in test and verify exit code 1. **Note**: Implements Constitution Principle VII verified constraint. Moved to Phase 7 to run on complete runner.

---

## Phase 8: Final Verification & Integration (Revision Round 2)

**Purpose**: Ensure all previous fixes are integrated, data flow is strictly enforced, and the system is ready for final validation.

- [ ] T063 [US2] **Enforce Strict Data-Flow Ordering (Verification Script)**: Modify `src/environment/runner.py` to explicitly check that `data/processed/full_sweep_results.json` (generated by T033b) exists and contains valid data for the current N *before* executing any analysis tasks (T038-T044). If the file is missing or empty, the runner must exit with code 1 and a clear error message: "Data Flow Error: Empirical results for N={N} not found. Ensure T033b (full sweep) has completed successfully." **Verification**: Run the analysis suite without running the sweep first and verify the script fails with the specific error message. **Note**: Addresses the critical data-flow failure mode where verification runs before data generation. This task is a **Verification Script** intended to run post-hoc to validate the pipeline, distinct from the production runner logic.

- [X] T064 [US3] **Verify Sample Size Enforcement**: Execute a controlled run of the full suite with `--num-runs=10` (below the FR-006 threshold of 30) to verify that the check in T062 triggers correctly and the run aborts immediately. **Deliverable**: Log output containing "FR-006 Violation" and exit code 1. **Verification**: Run `python src/environment/runner.py --num-runs=10` and confirm failure. **Note**: Validates the "Fail Loudly" principle for statistical constraints.

- [ ] T065 [US2] **Verify Heavy-Tailed Independence**: Run the heavy-tailed validation (T034d) independently of the linear sweep to ensure the held-out set logic (T034c) is not contaminated by training data. **Deliverable**: Confirm `data/processed/heavy_tailed_results.json` is generated without reading from `data/processed/full_sweep_results.json`. **Verification**: Delete `full_sweep_results.json` and run the heavy-tailed validation; it must succeed. **Note**: Validates Constitution Principle VI (Validation Independence).

- [X] T066 [US1] **Final Derivation Audit**: Re-run the symbolic verification (T026b) and peer review gate (T031c) to ensure no regressions occurred during the code refactoring in Phase 7. **Deliverable**: Updated `docs/peer_review_checklist.md` with `status: PASSED` and a new timestamp. **Verification**: Check that the checklist reflects the latest code state. **Note**: Ensures theoretical integrity is maintained through implementation changes.

- [ ] T067 [P] **End-to-End Regression Test**: Execute the full `scripts/run_full_suite.sh` from a clean state (after deleting `data/processed/`) to verify the entire pipeline (Setup -> Foundation -> US1 -> US2 -> US3 -> Polish) completes without errors and produces all expected artifacts. **Deliverable**: Exit code 0 and presence of all JSON reports. **Verification**: Run the script and validate the final `data/processed/statistical_report.json` contains valid data for all N values. **Note**: Final validation of the complete system. <!-- FAILED: unspecified -->