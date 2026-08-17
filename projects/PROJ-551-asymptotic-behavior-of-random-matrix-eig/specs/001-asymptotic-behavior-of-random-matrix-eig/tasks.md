# Tasks: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Input**: Design documents from `/specs/001-asymptotic-behavior-of-random-matrix-eig/`, `plan.md`, `spec.md`, `research.md`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md (required for Phase 6), data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan in `projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/` by executing `mkdir -p code/generators code/analysis code/utils code/data_models tests/unit tests/integration data/raw data/processed data/logs data/figures state` and creating `__init__.py` in all `code/` and `tests/` subdirectories, and `requirements.txt` in `code/`.
- [X] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/` by creating `code/.ruff.toml` with standard rules and `code/pyproject.toml` with `[tool.black]` configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management for seeds, tolerances, and paths in `code/utils/config.py`
- [X] T005 [P] Implement data hygiene utilities (checksums) in `code/utils/checksum.py` per Constitution III
- [X] T006 [P] Create base data models/entities in `code/data_models.py` (SimulationRun, PerturbationConfig)
- [X] T007a [P] Implement iterative solver wrapper with `tol=1e-10` in `code/analysis/eigen_solver.py` using `scipy.sparse.linalg.eigsh` and `LinearOperator`; ensure convergence criteria are met and handle non-convergence gracefully.
- [X] T007b [P] Implement validation logic in `code/analysis/eigen_solver.py` to STRICTLY validate results against the theoretical semicircle edge (±2.0) to ensure outliers are not artifacts, and use the BBP threshold as the target for empirical verification, not a constraint to avoid.
- [X] T008 [P] Implement outlier detection logic (bulk edge vs. BBP prediction) in `code/analysis/outlier_detect.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Spectral Analysis of Perturbed Wigner Matrices (Priority: P1) 🎯 MVP

**Goal**: Generate Wigner matrices, apply deterministic sparse perturbations, and compute eigenvalues to identify outliers.

**Independent Test**: Run a script generating a single N=1000 instance with a rank-1 diagonal perturbation (θ=2.5) and verify an eigenvalue > 2.0 exists.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for Wigner matrix generation (mean/variance check) in `tests/unit/test_wigner.py`
- [X] T011 [P] [US1] Unit test for perturbation construction (rank/sparsity verification) in `tests/unit/test_perturbation.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement Wigner matrix generator (dense, scaled $1/\sqrt{N}$) in `code/generators/wigner.py`
- [X] T013 [P] [US1] Implement perturbation matrix constructor (diagonal, block-sparse, random sparse) in `code/generators/perturbation.py`; verify rank preservation during sparsity masking per FR-002 and FR-009
- [X] T014 [US1] Implement core simulation loop: generate $W_N$, add $P_N$, compute top 10 eigenvalues in `code/main.py` (single run mode)
- [ ] T019a [US1] Implement logic to generate and save raw Wigner matrix instances to `data/raw/matrix_N{N}_seed{seed}.npy` using NumPy, ensuring the matrix is persisted before checksumming.
- [ ] T019 [US1] Add logic to checksum raw matrix instances generated in T019a using SHA-256 algorithm; write checksums to `state/checksums_raw.json` to satisfy Constitution Principle III (Data Hygiene) and ensure traceability.
- [ ] T015 [US1] Add logic to record results (eigenvalues, perturbation params) to `data/processed/single_run_results.json` with metadata schema: `{"run_id": str, "N": int, "theta": float, "seed": int, "eigenvalues": list, "outlier_flag": bool}` to satisfy Constitution Principle III (Data Hygiene).
- [X] T017 [US1] Add structured logging for simulation run parameters; write structured JSON logs to `data/logs/simulation_run.log` including the exact random seed state, parameter values, and timestamp to satisfy Constitution Principle I (Reproducibility).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phase Transition Threshold Detection (Priority: P2)

**Goal**: Systematically sweep perturbation norms and dimensions to empirically determine the critical threshold $\theta_c$.

**Independent Test**: Execute a parameter sweep script and verify the output dataset shows a monotonic transition from "no outlier" to "outlier" as $\theta$ increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Integration test for full parameter sweep (small N, few runs) in `tests/integration/test_sweep.py`

### Implementation for User Story 2

- [ ] T040a [US2] Generate raw matrix instances for the full parameter sweep in `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy` to satisfy Constitution Principle III (Data Hygiene); this task MUST run before T020 to ensure raw data is preserved.
- [ ] T040b [US2] Compute SHA-256 checksums for all raw matrix instances generated in T040a and record them in `state/checksums_sweep.json`.
- [X] T020 [US2] Implement parameter sweep orchestrator in `code/analysis/threshold_sweep.py` that: (1) defines the parameter grid (N: -2000, theta: a range of plausible values), (2) executes the loop calling T040a/T040b logic to generate and checksum data per iteration, (3) ingests the checksummed raw data, and (4) manages iterations.
- [ ] T021a [P] [US2] Implement Monte Carlo runner (A sufficient number of iterations per configuration) with random seed management in `code/analysis/monte_carlo_runner.py`; output results to `data/processed/mc_results.csv` with schema: `run_id, N, theta, seed, outlier_count, max_eigenvalue`.
- [ ] T021b_impl [US2] Implement statistical inference logic (logistic regression or sigmoid fitting) in `code/analysis/fit_utils.py` to calculate transition probability and derive the critical $\theta_c$ value with confidence intervals; output `data/processed/threshold_identification.json`.
- [ ] T021b [US2] Analyze Monte Carlo results from `data/processed/mc_results.csv` to prepare data for threshold identification; output `data/processed/threshold_identification_raw.json`.
- [X] T022a [P] [US2] Implement curve fitting function using `scipy.optimize.curve_fit` in `code/analysis/fit_utils.py` to estimate critical $\theta_c$ from binary outlier probability vs. theta data.
- [X] T022b [US2] Extract fitted parameters and validate fit quality against the $1e-10$ tolerance threshold in `code/analysis/fit_utils.py`.
- [ ] T022c [US2] Write fitted parameters to `data/processed/threshold_fit_params.json`.
- [ ] T024 [US2] Generate aggregated results file `data/processed/threshold_sweep_results.csv`.
- [ ] T025 [US2] Add visualization script to plot probability of outlier emergence vs. $\theta$ for different sparsity patterns; output plot to `data/figures/outlier_probability_vs_theta.png`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Sparsity Thresholds (Priority: P3)

**Goal**: Perform sensitivity analysis on sparsity parameters to ensure findings are robust to discrete configuration choices.

**Independent Test**: Run a script sweeping sparsity density $p \in \{0.1, 0.2, 0.3\}$ and verify the report explicitly states if $\theta_c$ shifts > 5%.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for sparsity density calculation and mask generation in `tests/unit/test_sparsity_utils.py`

### Implementation for User Story 3

- [ ] T031a_impl [US3] Implement logic to generate the rank-0 (unperturbed) Wigner matrix and run spectral analysis to produce the verification log.
- [ ] T031 [US3] Verify semicircle law compliance for rank $k=0$ using results from T031a_impl; output verification log to `data/logs/edge_case_rank0.log`.
- [X] T027 [P] [US3] Implement sparsity sensitivity runner (fixed rank, variable support density) in `code/analysis/sensitivity_analysis.py`
- [ ] T028 [US3] Execute sweep over support density set $\{0.1, 0.2, 0.3\}$ for each sparsity pattern type; output results to `data/processed/sensitivity_density_sweep.csv`.
- [ ] T029a [US3] Compute variation in critical threshold $\theta_c$ relative to nominal sparsity level; generate `data/processed/sensitivity_variation.csv`. <!-- ATOMIZE: requested -->
- [ ] T029b_impl [US3] Implement statistical validation logic (calculate p-values or confidence intervals on the threshold shift) in `code/analysis/sensitivity_analysis.py` to prove robustness as required by the plan; output `data/processed/sensitivity_statistics.json`.
- [ ] T030 [US3] Generate sensitivity report `data/processed/sensitivity_report.md` stating stability or shift magnitude, including statistical validation results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation, Contextualization & Polish (Priority: P1)

**Goal**: Ensure documentation, reproducibility, and performance meet project standards while explicitly framing the study as observational and addressing the "observer" critique from prior research reviews (FR-007).

**Independent Test**: Verify that `quickstart.md` and `research.md` are complete, reproducible, and explicitly state that the "observer" is the computational algorithm measuring spectral statistics, not a physical entity, aligning with the EPR critique response.

### Implementation for Documentation & Contextualization

- [ ] T032_init [P] [Docs] Create and initialize `research.md` with the project overview, methodology, and initial structure, addressing the need for a target artifact for subsequent updates.
- [ ] T032a [P] [Docs] Update `quickstart.md` to include instructions for reproducing the full parameter sweep and sensitivity analysis.
- [ ] T033 [P] [Docs] Update `research.md` to explicitly define the "observer" as the computational algorithm (the spectral solver) measuring statistical correlations in simulated data, directly addressing the critique in the `albert-einstein-simulated` review. This task must clarify that the study models the *mathematical* properties of random matrices, not a physical quantum field or chaotic billiard, and that "sparse noise" is a deterministic perturbation pattern, not a physical fluctuation.
- [ ] T034 [P] [Docs] Add a "Theoretical Context" section to `research.md` distinguishing between the mathematical model (Wigner matrices + perturbations) and potential physical analogs (e.g., quantum chaos), explicitly stating that no specific physical system is being modeled to avoid scope creep and maintain the observational nature of the study.
- [ ] T035 [P] Code cleanup and refactoring for memory efficiency (ensure < 7 GB RAM for N=2000); generate memory profile report `state/memory_profile_N2000.log` to verify compliance.
- [ ] T036 Performance optimization: verify full parameter sweep completes within 6 hours; record execution time in `state/sweep_timing.log`.
- [ ] T037 [P] Additional unit tests for edge cases (N=100, $\theta=1.0$, rank=0) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure reproducibility; output pass/fail log to `state/quickstart_validation.log`.
- [ ] T039 Final checksum generation for all `data/` artifacts in `state/checksums.json`.

**Checkpoint**: The project now includes rigorous documentation and performance validation while strictly adhering to observational constraints and addressing the "observer" critique.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Documentation & Contextualization (Phase 6)**: Can run in parallel with User Story implementation but must be complete before final paper drafting; depends on Foundational phase for data model context and T032_init for the research.md artifact.
- **Polish (Final Phase)**: Depends on all desired user stories and review responses being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses US1 generators; T020 depends on T040a/T040b for raw data hygiene.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses US1/US2 logic
- **Documentation & Contextualization (Phase 6)**: Depends on Foundational phase for data model context; can proceed independently of specific US implementation details but requires the data model structure and T032_init for the research.md artifact.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Documentation & Contextualization tasks (Phase 6) can run in parallel with User Story implementation once the data model is established.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Wigner matrix generation in tests/unit/test_wigner.py"
Task: "Unit test for perturbation construction in tests/unit/test_perturbation.py"

# Launch all models for User Story 1 together:
Task: "Implement Wigner matrix generator in code/generators/wigner.py"
Task: "Implement perturbation matrix constructor in code/generators/perturbation.py"
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
 - Developer B: User Story 2 (Must complete T040a/T040b before T020)
 - Developer C: User Story 3
 - Developer D: Documentation & Contextualization (Phase 6, starting with T032_init)
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
- **Critical Constraint**: All matrix operations must use CPU-tractable iterative solvers (ARPACK) for N > 500 to fit within 7GB RAM. No GPU tasks.
- **Scope Note**: This project is purely observational (simulated data) with synthetic variables. All findings are framed as associational correlations (FR-007). No physical "observer" or "frame of reference" modeling is required or permitted beyond the computational measurement of spectral statistics.
- **Review Response (T033, T034)**: These tasks directly address the `albert-einstein-simulated` review by explicitly defining the "observer" as the algorithm and clarifying the mathematical vs. physical nature of the model, preventing the project from drifting into unverified physical modeling while satisfying the critique's demand for a "frame of reference."
- **Data Hygiene Note**: Task T040a/T040b ensures raw data for the sweep is checksummed before T020 processes it, strictly adhering to Constitution Principle III. Task T019a ensures raw data for US1 is checksummed before T019.
- **Ordering Note**: T019a (generate) must complete before T019 (checksum). T040a/T040b must complete before T020. T032_init (create research.md) must complete before T033/T034. T031a_impl (generate unperturbed) must complete before T031.