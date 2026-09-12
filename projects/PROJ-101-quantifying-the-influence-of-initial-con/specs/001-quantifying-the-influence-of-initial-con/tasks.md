---

description: "Task list template for feature implementation"
---

# Tasks: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Input**: Design documents from `/specs/001-quantify-initial-conditions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `state/`
- [X] T001b [P] Create `code/__init__.py`, `code/data/__init__.py`, `code/analysis/__init__.py`
- [X] T001c [P] Create `tests/unit/`, `tests/integration/` directories
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scipy, numpy, matplotlib, pandas, pytest, statsmodels)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting tools. **Deliverable**: Create `pyproject.toml` with `[tool.ruff]` section enabling rules `E, F, W` and `max-line-length=88`, and `[tool.black]` section with `line-length=88`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with hyperparameters (seeds, N values, noise levels, tolerances `rtol=1e-9`, `atol=1e-12`)
- [X] T005 [P] Implement `code/__init__.py` and package structure
- [X] T006 Setup `code/data/__init__.py` and `code/analysis/__init__.py`
- [X] T007 [P] Implement base utility for numerical stability checks in `code/utils/stability.py`. **Deliverables**: Implement `check_boundedness(state_vector, threshold=100)` returning bool; implement `check_convergence(values, tol=1e-6)` returning bool. These functions are the single source of truth for boundedness and convergence logic used by T016 and T026.
- [X] T008 Configure `pytest` with fixtures for random seeds and temporary data directories
- [X] T009 Implement `code/main.py` pipeline orchestrator skeleton with argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Noisy High-Dimensional Chaotic Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic time-series data from coupled Lorenz oscillators with controllable noise levels as ground truth.

**Independent Test**: Verify output dimensions match system definition and noise statistics match injected parameters within 1% tolerance; clean trajectory matches deterministic integration within numerical precision.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for noise injection statistics in `tests/unit/test_generator.py` (verify mean/variance match `sigma_noise`)
- [X] T011 [P] [US1] Unit test for clean trajectory numerical precision in `tests/unit/test_generator.py` (verify error < 1e-9 against reference)
- [X] T012 [US1] Unit test for "unphysical" flagging and "high-noise" warning in `tests/unit/test_generator.py` (verify `HighNoiseWarning` at `sigma > 0.1` and `UnphysicalTrajectoryError` at `sigma > 1.0` or divergence)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data/generator.py` with coupled Lorenz ODE system definition (N oscillators, coupling topology)
- [X] T014 [US1] Implement `code/data/generator.py` trajectory integration using `scipy.integrate.solve_ivp` with **method='DOP853'** and strict tolerances **rtol=1e-9**, **atol=1e-12** as mandated by FR-001.
- [X] T015 [US1] Implement `code/data/generator.py` additive Gaussian white noise injection logic (`np.random.normal`)
- [X] T016a [US1] Implement `code/data/generator.py` noise check logic: Raise `HighNoiseWarning` if `sigma_noise > 0.1`; Raise `UnphysicalTrajectoryError` if `sigma_noise > 1.0` OR if `max(|state_vector|) > 100` (attractor bound). **CRITICAL**: Use `check_boundedness` from T007 to perform the `max(|state_vector|) > 100` check for ALL noise levels. **Constraint**: If `UnphysicalTrajectoryError` is raised, the specific trial's analysis pipeline MUST halt immediately; do not proceed to save or further analysis for that trial.
- [X] T016b [US1] Implement `code/data/generator.py` flow control: Ensure the check logic in T016a is executed post-integration and pre-save. If `UnphysicalTrajectoryError` is raised, the trajectory must NOT be saved.
- [X] T017 [US1] Implement `code/data/loader.py` to save/load trajectories to `data/raw/` as **CSV** files with SHA-256 checksums (aligned with Constitution Data Hygiene principles for transparent formats).
- [X] T018 [US1] Implement `code/main.py` logic to trigger the full generation loop. **Deliverable**: Run loop for **N \in {3, 5}** (restricted to plan scope) and sigma $\in$ {a range of small to moderate values}. **Trial Logic**: For each noise level, determine `k` as: `k = max(30, int(100 * sigma))` . Run `k` trials per level. **Output**: Save each trajectory to `data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.csv` (where t=1..k). **CLI**: Support `--noise-levels` and `--N-values` arguments. **Constraint**: Must include `sigma > 1.0` (1.5, 2.0) to validate FR-007 unphysical regime. **Solver**: Must enforce `method='DOP853'`, `rtol=1e-9`, `atol=1e-12`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Finite-Time Lyapunov Exponents and Asymptotic Baselines (Priority: P2)

**Goal**: Calculate FTLE over sliding windows and establish a robust asymptotic baseline for the clean system to quantify deviation.

**Independent Test**: Verify FTLE converges to numerically computed asymptotic baseline for clean system as T increases; noisy trajectories show expected deviation.

### Tests for User Story 2 ⚠️

- [X] T019 [P] [US2] Unit test for FTLE convergence on clean trajectory in `tests/unit/test_ftle.py` (verify error < 5% at T=5000)
- [X] T020 [P] [US2] Unit test for Jacobian propagation stability in `tests/unit/test_ftle.py` (verify no NaN/Inf in tangent vectors)
- [X] T021 [US2/FR-006b] Unit test for "non-chaotic" detection (numerical lambda_max check) in `tests/unit/test_baseline.py` (verify `NonChaoticSystemError` is raised if computed lambda_max <= 0)

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/analysis/baseline.py` with Richardson extrapolation to compute numerically converged asymptotic baseline for specific (N, D) configuration. **Method**: Integrate trajectory with step sizes `h`, `h/2`, `h/4` using 4th order extrapolation. Stop when relative change `|lambda_{k} - lambda_{k-1}| / |lambda_{k-1}| < 1e-6`. **Output**: Save to `data/processed/baseline_{N}.json` with keys `lambda_max` (float), `error_estimate` (float), `convergence_check` (bool). **Verification**: Explicitly verify that the computed `lambda_max` is stable and converged via Richardson extrapolation. **Do NOT** compare against a theoretical single-oscillator value or an undefined "expected coupled limit".
- [X] T025 [US2] Implement `code/analysis/baseline.py` validation logic: confirm clean system max Lyapunov exponent is stable (converged to a positive value) before proceeding.
- [X] T026 [US2/FR-006] Implement `code/analysis/baseline.py` logic to detect non-chaotic regimes: Compute numerical `lambda_max` for the specific configuration; if `lambda_max <= 0`, raise `NonChaoticSystemError` with message "Non-chaotic regime detected: lambda_max={lambda_max} <= 0". (Do NOT use fixed rho threshold).
- [X] T028 [US2/FR-006] Implement `code/main.py` gating mechanism: Create `validate_and_gate(baseline_results: dict) -> None` function. **Logic**: If T024 (convergence value check) or T026 (non-chaotic check) fails, raise `GateFailedError` with specific message. **Return**: None on success. **Dependency**: Must be called before T045 execution.
- [X] T022 [US2] Implement `code/analysis/ftle.py` with tangent-linear propagation algorithm (Jacobian evaluation at noisy points). **DEPENDS ON**: T024 (Baseline Data), T026 (Error Classes), T007 (Stability Utils). **Data Flow**: Read `lambda_max` from `data/processed/baseline_{N}.json` key `lambda_max`.
- [X] T023 [US2] Implement `code/analysis/ftle.py` sliding window logic for `T \in {500, 1000, 5000}` ensuring **T < total_length - 10** (strict multi-step offset as per Edge Cases) to allow for tangent vector propagation. **DEPENDS ON**: T024, T026, T007. **Data Flow**: Read `lambda_max` from `data/processed/baseline_{N}.json` key `lambda_max`.
- [X] T035a [US3] Implement `code/analysis/regression.py` to ensure **k(σ) independent trials** per noise level are available in `data/raw/`, where **k=50 for σ < 0.01** and **k ≥ 30 for σ ≥ 0.01**, covering the full noise range defined in T018. **Input**: Noise levels `sigma` from T018. **Output**: Verify `data/raw/` contains the required variable number of trajectories per level. **Logic**: For each sigma, count files; if count < (50 if sigma < 0.01 else 30), raise error. **Dependency**: T018 (Generation Loop). **Note**: This task ensures the statistical requirement of SC-003 (variable power) is met.
- [X] T045 [US2] Implement execution of the sliding window sweep: Run the FTLE algorithm (T022/T023) across `T \in {500, 1000, 5000}` for all trials generated in T018. **Dependency**: **T028 (Gating)** must pass before this execution runs. **Aggregation Logic**: Append all results (one row per trial/window) to a list. **Writer Logic**: Save aggregated results to `data/processed/ftle_sweep.json` with schema `{"trial_id": int, "N": int, "sigma": float, "T": int, "lambda_ftle": float}`. **Constraint**: This task includes the writer logic (previously T027) to avoid race conditions.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Deviation Scaling and Generate Visualizations (Priority: P3)

**Goal**: Perform regression analysis on deviation $\Delta \lambda$ and generate visualizations showing bias scaling with noise and dimension.

**Independent Test**: Verify output includes regression plots, p-values, effect sizes, and scaling exponents; regression model selection uses AIC/BIC.

### Tests for User Story 3 ⚠️

- [X] T029 [P] [US3] Unit test for regression statistical significance in `tests/unit/test_regression.py`. **Function**: `test_regression_p_value_significance`. **Assertion**: `assert p_value < 0.05` for a synthetic dataset with known bias; verify `effect_size` is calculated correctly. **Requirement**: Must explicitly verify SC-003 statistical verification (p-value, effect size) before implementation.
- [X] T030 [P] [US3] Integration test for full scaling analysis pipeline in `tests/integration/test_pipeline.py`. **Function**: `test_full_scaling_analysis`. **Assertion**: Verify `data/processed/plot_deviation_vs_noise.png` exists and `data/processed/results.json` contains `p_value_model` and `effect_size_model`. **Requirement**: Must explicitly verify SC-003 statistical verification (p-value, effect size) before implementation.

### Implementation for User Story 3

- [X] T035b [US3] Implement `code/analysis/regression.py` to run t-test on the raw trial means and output p-value and effect size to `data/processed/results.json` (explicitly addressing SC-003). **Input**: `data/processed/ftle_sweep.json`. **Output**: JSON keys `p_value_raw`, `effect_size_raw`, `bias_term_raw`. **Constraint**: Test the difference between noisy means and the clean baseline.
- [X] T031 [P] [US3] Implement `code/analysis/regression.py` to calculate deviation $\Delta \lambda(T, \sigma_{noise})$ from baseline. **Input**: `data/processed/ftle_sweep.json`, `data/processed/baseline_{N}.json`. **Output**: Add `deviation` column to results. **Dependency**: T045.
- [X] T032 [US3] Implement `code/analysis/regression.py` model selection strategy (AIC/BIC) to determine functional form (additive, multiplicative, saturation). **Output**: Select best model and save to `data/processed/regression_model.json`. **Dependency**: T031.
- [X] T032b [US3] Implement `code/analysis/regression.py` to perform **t-test specifically on the bias term coefficient** of the selected regression model. **Library**: Use `scipy.stats.ttest_1samp` on residuals or `statsmodels` OLS summary. **Confidence**: %. **Input**: `data/processed/regression_model.json`. **Output**: Update `data/processed/results.json` with `p_value_model` and `effect_size_model` for the **bias term**. **Constraint**: Do NOT test raw deviations; test the model coefficient.
- [X] T034 [US3] Implement `code/analysis/regression.py` scaling exponent calculation relating system dimension to FTLE bias magnitude
- [X] T036 [US3] Implement `code/analysis/regression.py` visualization module: plot deviation vs. noise with error bars (SE). **Output**: `data/processed/plot_deviation_vs_noise.png`. **Library**: `matplotlib`. **Data**: `data/processed/results.json`. **Prerequisite**: Must use data from k(σ) trials (T035a) to derive standard error.
- [X] T037a [US3] Implement `code/main.py` orchestration to run full analysis pipeline and save results to `data/processed/`
- [X] T037b [US3] Implement `code/analysis/regression.py` visualization module: convergence plot (FTLE vs. T) for **at least three distinct noise levels** (explicitly selecting three levels as required by FR-005). **Output**: `data/processed/plot_convergence.png`. **Data**: `data/processed/ftle_sweep.json`. **Dependency**: T045.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037c [P] Update `quickstart.md` with CLI arguments for `--noise-level` and `--N`
- [ ] T037d [P] Update `README.md` with full pipeline run instructions
- [ ] T038 Code cleanup and refactoring for readability
- [ ] T039 Performance optimization: parallelize trials across CPU cores using `multiprocessing`
- [ ] T040 [P] Additional unit tests for edge cases (high noise, non-chaotic params) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [X] T042 [US1/US2/US3] Implement integration test in `tests/integration/test_pipeline.py` that runs the full N=5 generation and analysis loop, verifying total runtime <= 30s (Addressing US-1 Acceptance Scenario 3). **Note: This task requires US1, US2, and US3 to be implemented.**
- [X] T043 [US2] Implement `code/analysis/boundedness.py` to perform **Boundedness/Escape Time Check** as a post-generation validation step (not a blocking dependency for FTLE calculation). **Output**: Log validation status. **Dependency**: T018 (Generation). **Logic**: Use `check_boundedness` from T007 to verify trajectory remains within attractor bounds; calculate escape time if trajectory diverges. **Constraint**: Implements the required boundedness check exclusively, as mandated by the Plan for stochastic regimes.
- [X] T044 [P] [US2] Implement `code/analysis/ftle.py` to explicitly log and handle the case where `T` (window size) approaches total trajectory length, ensuring a strict `T < total_length - 10` check is enforced to prevent tangent vector propagation errors.
- [X] T046 [P] [US1] Implement `code/data/generator.py` to explicitly handle the case where `sigma_noise > 1.0` by logging a specific "Unphysical Trajectory" event, **raising `UnphysicalTrajectoryError`**, and **halting further analysis for that specific trial** without crashing the entire sweep.
- [ ] T047 [P] [US3] Implement `code/analysis/regression.py` to explicitly report the scaling exponent relating system dimension (N) to the magnitude of the FTLE bias, ensuring this metric is included in the final `data/processed/results.json` as required by US-3 Acceptance Scenario 3.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 & US2 results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Explicit Task Dependencies (Critical for Ordering)

- **T022, T023 (Noisy FTLE)**: DEPEND ON **T024 (Baseline Data)**, **T026 (Error Classes)**, **T007 (Stability Utils)**. (T028 is a gate for execution, not implementation).
- **T018 (Generation Loop)**: DEPEND ON **T017 (Loader/Save)**. T018 triggers the loop and relies on T017 to persist artifacts.
- **T037a (Analysis Orchestration)**: DEPEND ON **T045 (FTLE Results)** and **T024 (Baseline)**.
- **T045 (Sweep Execution)**: DEPEND ON **T022, T023, T035a, AND T028 (Gating)**.
- **T035a (Trials)**: DEPEND ON **T018**.
- **T031, T032, T032b (Regression)**: DEPEND ON **T045**.
- **T036, T037b (Visualizations)**: DEPEND ON **T032b** and **T045**.
- **T042 (Full Pipeline Benchmark)**: DEPEND ON **T018, T045, T037a** (all phases).
- **T043 (Boundedness Check)**: DEPEND ON **T018** (Generation).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for noise injection statistics in tests/unit/test_generator.py"
Task: "Unit test for clean trajectory numerical precision in tests/unit/test_generator.py"
Task: "Unit test for 'unphysical' flagging in tests/unit/test_generator.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/generator.py with coupled Lorenz ODE system"
Task: "Implement code/data/generator.py trajectory integration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate trajectories, verify noise stats)
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (FTLE & Baseline)
 - Developer C: User Story 3 (Analysis & Viz)
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
