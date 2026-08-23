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
- [ ] T001b [P] Create `code/__init__.py`, `code/data/__init__.py`, `code/analysis/__init__.py`
- [ ] T001c [P] Create `tests/unit/`, `tests/integration/` directories
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scipy, numpy, matplotlib, pandas, pytest, statsmodels)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with hyperparameters (seeds, N values, noise levels, tolerances `rtol=1e-9`, `atol=1e-12`)
- [ ] T005 [P] Implement `code/__init__.py` and package structure
- [ ] T006 Setup `code/data/__init__.py` and `code/analysis/__init__.py`
- [ ] T007 Create base utility for numerical stability checks (convergence detection, boundedness checks)
- [ ] T008 Configure `pytest` with fixtures for random seeds and temporary data directories
- [ ] T009 Implement `code/main.py` pipeline orchestrator skeleton with argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Noisy High-Dimensional Chaotic Trajectories (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic time-series data from coupled Lorenz oscillators with controllable noise levels as ground truth.

**Independent Test**: Verify output dimensions match system definition and noise statistics match injected parameters within 1% tolerance; clean trajectory matches deterministic integration within numerical precision.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Unit test for noise injection statistics in `tests/unit/test_generator.py` (verify mean/variance match `sigma_noise`)
- [ ] T011 [P] [US1] Unit test for clean trajectory numerical precision in `tests/unit/test_generator.py` (verify error < 1e-9 against reference)
- [ ] T012 [US1] Unit test for "unphysical" flagging when `sigma_noise > 1.0` and trajectory leaves attractor in `tests/unit/test_generator.py` (verify `UnphysicalTrajectoryError` is raised)
- [ ] T042 [US1] Benchmark test to verify N=5 trajectory generation completes within 30 seconds on standard CPU in `tests/integration/test_performance.py` (Verify N=5 trajectory generation completes within 30 seconds (US-1 Acceptance Scenario 3))

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/data/generator.py` with coupled Lorenz ODE system definition (N oscillators, coupling topology)
- [ ] T014 [US1] Implement `code/data/generator.py` trajectory integration using `scipy.integrate.solve_ivp` with method 'DOP853' and strict tolerances
- [ ] T015 [US1] Implement `code/data/generator.py` additive Gaussian white noise injection logic (`np.random.normal`)
- [ ] T016 [US1] Implement `code/data/generator.py` "unphysical" detection logic: If `sigma_noise > 1.0` AND `max(|state_vector|) > 100` (attractor bound), raise `UnphysicalTrajectoryError` with message "Trajectory left attractor bounds (sigma={sigma})".
- [ ] T017 [US1] Implement `code/data/loader.py` to save/load trajectories to `data/raw/` with SHA-256 checksums
- [ ] T018 [US1] Implement `code/main.py` logic to trigger the full loop (N \in \mathbb{Z}^+, \sigma \in [10^{-4}, 1.0]) and explicitly rely on T017's save logic to produce the artifacts consumed by Phase 4.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Finite-Time Lyapunov Exponents and Asymptotic Baselines (Priority: P2)

**Goal**: Calculate FTLE over sliding windows and establish a robust asymptotic baseline for the clean system to quantify deviation.

**Independent Test**: Verify FTLE converges to numerically computed asymptotic baseline for clean system as T increases; noisy trajectories show expected deviation.

### Tests for User Story 2 ⚠️

- [ ] T019 [P] [US2] Unit test for FTLE convergence on clean trajectory in `tests/unit/test_ftle.py` (verify error < 5% at T=5000)
- [ ] T020 [P] [US2] Unit test for Jacobian propagation stability in `tests/unit/test_ftle.py` (verify no NaN/Inf in tangent vectors)
- [ ] T021 [US2/FR-006] Unit test for "non-chaotic" detection (rho < 24.74) and abort in `tests/unit/test_baseline.py` (verify `NonChaoticSystemError` is raised; aligns with Edge Cases and FR-006)

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/analysis/ftle.py` with tangent-linear propagation algorithm (Jacobian evaluation at noisy points). **DEPENDS ON T028a**.
- [ ] T023 [US2] Implement `code/analysis/ftle.py` sliding window logic for `T \in \{small, medium, large, very large\}` ensuring `T < total_length - 10`. **DEPENDS ON T028a**.
- [ ] T024 [US2] Implement `code/analysis/baseline.py` with Richardson extrapolation to compute numerically converged asymptotic baseline for specific (N, D) configuration; save to `data/processed/baseline_{N}.json` with keys `lambda_max` (float), `error_estimate` (float); stop when relative change `|lambda_{k} - lambda_{k-1}| / |lambda_{k-1}| < 1e-6`.
- [ ] T025 [US2] Implement `code/analysis/baseline.py` validation logic: confirm clean system max Lyapunov exponent is stable before proceeding
- [ ] T026 [US2] Implement `code/analysis/baseline.py` logic to detect non-chaotic regimes: read `config.RHO`; if `config.RHO < 24.74`, raise `NonChaoticSystemError` with message "Non-chaotic regime detected: rho={rho} < 24.74".
- [ ] T028 [US2/FR-006] Implement `code/main.py` gating mechanism: enforce hard fail-stop if T025 validation fails before any noisy analysis (T022/T023) proceeds. This task is the gatekeeper for Phase 4.
- [ ] T028a [US2/FR-006] Implement `code/main.py` explicit gating mechanism: Create a function `validate_and_gate(baseline_results)` that halts execution if T025 validation fails, ensuring T022/T023 cannot run without a valid baseline.
- [ ] T027 [US2] Implement `code/analysis/ftle.py` to output exponent values, window sizes, and noise levels to `data/processed/ftle_results.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Deviation Scaling and Generate Visualizations (Priority: P3)

**Goal**: Perform regression analysis on deviation $\Delta \lambda$ and generate visualizations showing bias scaling with noise and dimension.

**Independent Test**: Verify output includes regression plots, p-values, effect sizes, and scaling exponents; regression model selection uses AIC/BIC.

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Unit test for regression statistical significance (t-test, p-value, effect size) in `tests/unit/test_regression.py`
- [ ] T030 [P] [US3] Integration test for full scaling analysis pipeline in `tests/integration/test_pipeline.py` (verify plot generation)

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `code/analysis/regression.py` to calculate deviation $\Delta \lambda(T, \sigma_{noise})$ from baseline
- [ ] T032 [US3] Implement `code/analysis/regression.py` model selection strategy (AIC/BIC) to determine functional form (additive, multiplicative, saturation)
- [ ] T033 [US3] Implement `code/analysis/regression.py` t-test and effect size calculation for bias term significance
- [ ] T034 [US3] Implement `code/analysis/regression.py` scaling exponent calculation relating system dimension to FTLE bias magnitude
- [ ] T035 [US3] Implement `code/analysis/regression.py` visualization module: plot deviation vs. noise with error bars (SE)
- [ ] T036 [US3] Implement `code/analysis/regression.py` visualization module: convergence plot (FTLE vs. T) for distinct noise levels
- [ ] T037 [US3] Implement `code/main.py` orchestration to run full analysis pipeline and save results to `data/processed/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037a [P] Update `quickstart.md` with CLI arguments for `--noise-level` and `--N`
- [ ] T037b [P] Update `README.md` with full pipeline run instructions
- [ ] T038 Code cleanup and refactoring for readability
- [ ] T039 Performance optimization: parallelize trials across CPU cores using `multiprocessing`
- [ ] T040 [P] Additional unit tests for edge cases (high noise, non-chaotic params) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline reproducibility

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

- **T022, T023 (Noisy FTLE)**: DEPEND ON **T028a (Baseline Validation Gate)**. T028a must pass (validating clean baseline) before T022/T023 can execute.
- **T018 (Generation Loop)**: DEPEND ON **T017 (Loader/Save)**. T018 triggers the loop and relies on T017 to persist artifacts.
- **T037 (Analysis Orchestration)**: DEPEND ON **T027 (FTLE Results)** and **T024 (Baseline)**.

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
3. Add User Story 2 → Test independently → Deploy/Demo (FTLE + Baseline)
4. Add User Story 3 → Test independently → Deploy/Demo (Regression + Plots)
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
