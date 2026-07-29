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

- [ ] T001 [P] Initialize project directory structure: Create `src/`, `tests/`, `data/`, `scripts/`, `docs/` directories and their subdirectories (`src/derivation`, `src/environment`, `src/heuristic`, `src/analysis`, `tests/unit`, `tests/contract`, `tests/integration`, `data/raw`, `data/processed`) along with `__init__.py` files for all Python packages and `.gitkeep` files for data directories.
- [X] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (a range of values including 5, 10, 20, 50), `k` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {0, 0.2, 0.5}). **Note**: This task is in Phase 1 to ensure config exists before Foundational tasks read it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical memory optimizations to ensure a constrained memory environment is met from the start.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T015 [P] Implement `src/environment/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ across a range of values including the absence of correlation as required by FR-009, (3) deterministic seeded random state management. **Depends on**: T014 (config).
- [X] T015b [P] Implement and verify N=5 case in `src/environment/synthetic_mdp.py`. **Deliverable**: Function call `generate_mdp(n_objectives=5)` returning a valid MDP instance. **Verification**: Run `python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(5); assert mdp.n_objectives == 5"`. **Note**: Explicitly implements FR-003 N=5 requirement.
- [ ] T016 [P] Implement `src/heuristic/moving_window.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size). **Depends on**: T014 (config). <!-- FAILED: unspecified -->
- [X] T053 [P] Refactor `src/environment/runner.py` to use generators instead of lists for trajectory storage to ensure memory efficiency (<7GB) under large N. **Deliverable**: Generator-based trajectory iterator. **Verification**: Run with N=50 and confirm memory < 7GB or verify `sys.getsizeof(iterator)` remains constant regardless of N. Use `tracemalloc` for verification.
- [X] T054 [P] Create `tests/unit/test_runner_memory.py` to verify memory usage remains <7GB with generators for N=50.
- [ ] T055 [P] Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint. **Deliverable**: Batched variance calculation function. Use `psutil` for memory monitoring.
- [X] T017 [P] Implement `src/environment/runner.py` with main() function accepting --n-objectives, --seed, --noise-correlation arguments, executing CPU-constrained training loops with memory checks (<7GB) using `tracemalloc`, and enforcing a specific number of CPU cores via `os.sched_setaffinity` and `OMP_NUM_THREADS=2` environment variables. **Depends on**: T053, T055, T017c completion. **Exit**: Exit with code 0 on success.
- [X] T017c [P] Implement explicit 2-core enforcement logic in `src/environment/runner.py` using `os.sched_setaffinity` to pin the process to exactly 2 CPU cores and setting `OMP_NUM_THREADS=2`. **Deliverable**: Function `enforce_cpu_cores(cores=2)` raising an error if the system cannot support it or if the limit is exceeded. **Verification**: Run `nproc` inside the runner script and verify it reports 2. **Note**: Implements FR-005 and Constitution Principle VII.
- [X] T018 [P] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i
- [X] T019a [P] Implement inversion logic in `src/derivation/sample_complexity.py` to calculate sample complexity bounds from variance equations. **Deliverable**: Function `calculate_bound(variance_expr, N, epsilon)` returning a sympy expression. **Verification**: Verify that `calculate_bound` returns the symbolic inverse of the variance equation for N=10, epsilon=0.1.
- [X] T019b [P] Implement string formatting for sample complexity bound in `src/derivation/sample_complexity.py`. **Deliverable**: Function `format_bound_expression(bound_expr)` returning a human-readable string.
- [X] T019c [P] Create `tests/unit/test_sample_complexity.py` to verify the inversion logic and string formatting. **Deliverable**: Unit tests for `calculate_bound` and `format_bound_expression`.
- [X] T017b [P] Implement `src/environment/pareto_oracle.py` with a defined approximation method for calculating distance to the theoretical Pareto frontier. **Deliverable**: Function `calculate_pareto_distance(policy, objectives)` returning a float. **Verification**: Verify against a known analytical solution for N=2. **Note**: Implements FR-017.
- [X] T021d [P] Implement sanity check function `run_noise_sanity_check(empirical_variance, theoretical_sigma_sq)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and deviation metric; verifies empirical noise matches theoretical sigma^2 within tolerance. **Note**: Explicitly implements FR-013 and FR-014.
- [X] T021a [P] Implement **PAIRED T-TEST** function `run_paired_ttest(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance. **Deliverable**: Function returning p-value and statistic. **Verification**: Verify p-value < 0.05 for synthetic data with known mean difference. **Note**: This implements the Plan's revision (Paired T-Test) as a secondary metric.
- [X] T021b [P] Implement stability check function `run_stability_check(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and ratio stats; verifies ratio remains within [0.9, 1.1] for ≥ 95% of steps. **Note**: Explicitly implements SC-003.
- [X] T021c [P] Implement sensitivity analysis sweep logic in `src/analysis/stats.py` for window size k. **Deliverable**: Function `run_sensitivity_sweep(...)` returning aggregated results.
- [X] T021e [P] Implement **ONE-SAMPLE T-TEST** function `run_one_sample_ttest(heuristic_vals, theoretical_bound)` in `src/analysis/stats.py` comparing mean deviation from theoretical bound against zero. **Deliverable**: Function returning p-value and statistic. **Note**: Explicitly implements Spec FR-006. **Verification**: Verify p-value < 0.05 for synthetic data with known mean deviation.
- [X] T022 [P] Create `tests/unit/test_derivation.py` to verify symbolic equations simplify correctly
- [X] T023 [P] Create `tests/unit/test_mdp.py` to verify MDP generation determinism and objective counts
- [X] T024 [P] Create `tests/unit/test_heuristic.py` to verify windowed variance calculation logic
- [X] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/` (Constitution Principle V)
- [X] T056 [P] Implement runtime memory verification step in `src/environment/runner.py` that explicitly fails the build (exits with code 1) if memory usage exceeds 7GB during N=50 runs. **Deliverable**: Function `check_memory_limit()` raising `MemoryError` if limit exceeded. **Verification**: Force memory spike in test and verify exit code 1. **Note**: Implements Constitution Principle VII verified constraint.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [X] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i
- [ ] T026b [US1] Execute symbolic math engine verification: Run a script that parses the output of T026 and uses `sympy` to algebraically verify the consistency of the derived equation against the known variance accumulation rules. **Deliverable**: Log file `logs/symbolic_verification.log` containing "VERIFIED" or "FAILED". **Note**: Explicitly implements SC-001 symbolic engine requirement.
- [X] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound. **Depends on**: T019a, T019b, T019c.
- [X] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output. **Format**: Add JSON field `assumptions: ["i.i.d. noise"]` in `docs/theoretical_derivation.md` and log to stdout. **Implementation**: Implement CLI flag `--verify-assumptions` in `src/derivation/sample_complexity.py`. **Verification**: Run `python src/derivation/sample_complexity.py --verify-assumptions` and verify stdout contains the assumptions JSON.
- [X] T029 [US1] Create `docs/theoretical_derivation.md` with required sections: (1) closed-form equation for Var(A) as function of N and ε_i, (2) sample complexity bound derivation, (3) explicit assumptions list, (4) verification results from sympy. **Depends on**: T027 completion.
- [X] T030 [US1] Create `docs/peer_review_checklist.md` with verification criteria for SC-001 alternative path, including algebraic consistency checklist and peer review sign-off template.
- [X] T031b [US1] **Generate Draft Peer Review Report**: Run the peer review checklist defined in T030 against the derivation in T029. **Deliverable**: Update `docs/peer_review_checklist.md` with timestamp and `status: DRAFT`. **Verification**: File must contain `status: DRAFT`.
- [X] T031c [US1] **Manual Peer Review Gate**: A human reviewer must manually sign off on `docs/peer_review_checklist.md`. **Deliverable**: Update `docs/peer_review_checklist.md` with `status: PASSED` and reviewer initials. **Verification**: File must contain `status: PASSED`. **Note**: This is a manual step.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {, 10, 20, 50}) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2

- [X] T031 [US2] Verify `src/environment/synthetic_mdp.py` generates correct tabular MDPs with N objectives (including N=5, 10, 20, 50) and noise correlation parameter ρ. **Note**: Explicitly includes N=5 as per FR-003.
- [X] T031a [US2] Verify N=5 generation explicitly: Run `generate_mdp(n_objectives=5)` and assert the resulting MDP has exactly 5 reward functions and valid state/action spaces. **Deliverable**: Unit test `tests/unit/test_mdp_n5.py`. **Note**: Explicitly implements FR-003 N=5 requirement.
- [X] T032 [US2] Verify `src/heuristic/moving_window.py` correctly calculates variance using only last k steps
- [X] T034 [US2] Add logic to handle edge case where N > 50. **Behavior**: If N > 50, reduce state space size |S| by a factor of (not N), log warning "State space reduced to |S|/2 for memory constraints (N={N})", and proceed. **Implementation**: Modify `src/environment/synthetic_mdp.py` to accept `force_reduce_state_space` flag. **Verification**: Run with N=100 and verify `logs/runner.log` contains "State space reduced" and the effective |S| is logged. **Note**: Implements FR-016 and US-6 Edge Case.
- [X] T034b [US2] Verify state space degradation logic in T034. **Deliverable**: Unit test `tests/unit/test_runner_degradation.py` that asserts |S| is halved for N>50. **Verification**: Run test and confirm pass. **Note**: Depends on completion of state space reduction logic in T034.
- [X] T034c [US2] Implement generation of held-out set with heavy-tailed noise distribution (Student's t, degrees of freedom=3) in `src/environment/synthetic_mdp.py`. **Deliverable**: Function `generate_heavy_tailed_mdp(..., seed=42)` returning an MDP instance. **Verification**: Verify noise distribution parameters match input (e.g., degrees of freedom) and seed strategy ensures reproducibility. **Note**: Implements FR-012 and US-4.
- [ ] T034d [US2] Implement calculation of distance to theoretical Pareto frontier for the heavy-tailed held-out set and comparison against the % deviation threshold in `src/analysis/stats.py`. **Deliverable**: Function `validate_heavy_tailed_pareto(...)` returning deviation metric and boolean `threshold_passed`. **Verification**: Run with heavy-tailed MDP and verify output file `data/processed/heavy_tailed_results.json` contains `threshold_passed: true` or `false`. **Note**: Implements FR-012, US-4 Independent Test, and SC-006.
- [ ] T034h [US2] Implement comparison of heavy-tailed held-out set results against the theoretical bound and the 10% deviation threshold in `src/analysis/stats.py`. **Deliverable**: Function `validate_heavy_tailed(...)` returning deviation metric and boolean `threshold_passed`. **Verification**: Run with heavy-tailed MDP and verify output file `data/processed/heavy_tailed_results.json` contains `threshold_passed: true` or `false`. **Note**: Implements FR-012 and US-4 Independent Test.
- [X] T034e [US2] Implement generation of reward functions with "Sparse" (sparsity ratio > 0.9) and "Non-Convex" (curvature metric > 0.5) distributions in `src/environment/synthetic_mdp.py`. **Deliverable**: Functions `generate_sparse_mdp(...)` and `generate_nonconvex_mdp(...)`. **Verification**: Verify generated rewards match distribution characteristics (e.g., sparsity ratio, non-convexity). **Note**: Implements FR-010 and US-4.
- [ ] T034g [US2] Implement generation of reward functions with "Linear" distribution baseline in `src/environment/synthetic_mdp.py`. **Deliverable**: Function `generate_linear_mdp(...)`. **Verification**: Verify generated rewards match linear combination characteristics. **Note**: Implements FR-010 (completes the set of three distributions).
- [ ] T034f [US2] Implement sensitivity analysis for Sparse, Non-Convex, and Linear distributions in `src/analysis/stats.py`. **Deliverable**: Function `validate_distributions(...)` returning deviation metrics for each distribution type. **Verification**: Run full sweep and verify `data/processed/distribution_sweep_results.json` contains results for Linear, Sparse, and Non-Convex. **Note**: Implements FR-010 and US-4.
- [X] T035 [US2] Add logging calls to output empirical variance and distance to Pareto frontier in `data/processed/empirical_results.json`. **Trigger**: After every N sweep completion. **Schema**: `{n_objectives, empirical_variance, pareto_distance, timestamp}`. **Verification**: Run `python src/environment/runner.py --n=50` and verify file exists with schema.
- [ ] T036 [US2] Extend `src/environment/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}) as required by FR-009. **Depends on**: T052c.
- [ ] T037 [US2] Verify MDP generation is deterministic with seeded random states
- [ ] T052b [US2] **Run Noise Correlation Sweep**: Execute simulation with noise correlation parameter ρ ∈ {, 0.5} (representing non-zero correlation levels) and log results to verify if the scaling law holds. **Deliverable**: `data/processed/correlation_sweep_results.json`. **Verification**: File exists with results for all three ρ values.
- [ ] T052c [US2] Implement Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N at ρ=0 in `src/analysis/stats.py`. **Deliverable**: Function `run_ks_test_slope(...)` returning p-value. **Verification**: Verify p-value > 0.05 for synthetic data with known slope matching theoretical bound. **Note**: Explicitly implements FR-009 KS-test requirement.
- [ ] T033 [US2] Integrate `src/environment/runner.py` with memory footprint checks (<7GB) and CPU constraints (exactly 2 cores via `os.sched_setaffinity`), ensuring it uses foundational MDP and heuristic modules. **Depends on**: T034, T036, T017c completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation (One-sample t-test vs bound, Paired t-test, Correlation) and sensitivity analysis on window size k. **Note**: The Plan's Paired T-Test is retained as a secondary metric, but the Spec's One-sample t-test (FR-006) is the primary validation requirement.

**Independent Test**: The system outputs a statistical report containing p-values from one-sample t-tests (vs bound) and a table showing variation in convergence rates as k varies.

### Implementation for User Story 3

- [X] T038 [US3] Implement **PAIRED T-TEST** in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance for each N. **Deliverable**: Function `run_paired_ttest` returning p-value. **Note**: This implements the Plan's revision (Paired T-Test) as a supplementary metric.
- [X] T039 [US3] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps. **Deliverable**: Function `run_stability_check` and output file `data/processed/stability_report.json`. **Note**: Explicitly implements SC-003.
- [X] T040a [US3] Define window size k sweep parameters (k ∈ {small values} of rollout size) in `src/config/defaults.yaml`. **Verification**: Verify `src/config/defaults.yaml` contains `k_sweep: [0.01, 0.05, 0.1]` and the file parses correctly.
- [X] T040b [US3] Implement sensitivity analysis sweep loop for window size k in `src/analysis/stats.py`.
- [X] T040c [US3] Implement result aggregation for sensitivity sweep. **Deliverable**: Function `aggregate_sweep_results(...)` returning a summary table.
- [X] T040d [US3] Create unit test for sweep output. **Deliverable**: `tests/unit/test_sensitivity_sweep.py`.
- [X] T042 [US3] Compute **Pearson/Spearman correlation coefficient** between variance estimation error (Heuristic vs. Full-Batch) and distance to Pareto frontier. **Verification**: Verify the function returns a correlation coefficient and p-value for a synthetic dataset with known correlation. **Note**: This implements Plan's revised SC-002 (Correlation) as a supplementary metric.
- [X] T042b [US3] Implement **COINCIDENCE CHECK** for SC-002: Identify smallest N where sample count exceeds bound by a moderate factor AND distance > 5% (using `src/environment/pareto_oracle.py` from FR-017 as the source for the 5% threshold). **Deliverable**: Function `check_coincidence(...)` returning boolean and failure point N. **Verification**: Verify the function correctly identifies the failure point for synthetic data with known properties. **Note**: Explicitly implements Spec SC-002 and FR-017.
- [X] T043 [US3] Determine failure point N (smallest N where p-value < 0.05 for one-sample t-test) and verify coincidence with Pareto distance (using T042b). **Note**: Verify coincidence, not just correlation. **Note**: Explicitly implements Spec SC-002.
- [ ] T044 [US3] Generate final statistical report in `data/processed/statistical_report.json`. **Command**: `python src/main.py --run-full-sweep`. **Keys**: `p_value_one_sample`, `p_value_paired`, `n_objectives`, `k_window`, `correlation_coefficient`, `failure_point_n`, `coincidence_met`, `stability_ratio`. **Verification**: Verify all keys present. **Depends on**: T035. **Note**: Includes both one-sample and paired metrics.
- [ ] T045 [US3] Add logic to handle non-Gaussian noise distributions and log deviations (Assumptions). **Implementation**: Implement check for `--noise-dist` flag with allowed values {'heavy-tailed', 'sparse', 'non-convex', 'linear'} and validation logic for invalid inputs. **Output**: Log message "Non-Gaussian deviation detected: {distribution_type}" to `logs/analysis.log`. **Verification**: Run with `--noise-dist=heavy-tailed` and verify `logs/analysis.log` contains the expected message.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Update `docs/quickstart.md` with instructions for running the full experiment suite
- [ ] T050 [P] Run `scripts/update_state.py` to verify artifact checksums and update `state/` files
- [ ] T051 Validate `quickstart.md` by running a full end-to-end execution on a local CPU-only environment

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
- **State Space Degradation**: Task T034 explicitly implements the reduction of state space size (not N) for N > 50 as required by FR-016.
- **Held-Out Set**: Task T034c and T034d/T034h implement the heavy-tailed held-out set generation and validation with 10% threshold check as required by FR-012.
- **Distribution Sensitivity**: Tasks T034e, T034f, T034g implement the Sparse, Non-Convex, and Linear distribution testing as required by FR-010.
- **Noise Sanity Check**: Task T021d implements the sanity check against known sigma^2 as required by FR-013 and FR-014.
- **Pareto Oracle**: Task T017b implements the Approximate Pareto Oracle as required by FR-017.