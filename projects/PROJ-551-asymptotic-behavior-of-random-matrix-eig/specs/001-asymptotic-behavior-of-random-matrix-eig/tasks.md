---
description: "Task list template for feature implementation"
---

# Tasks: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Input**: Design documents from `/specs/001-asymptotic-behavior-of-random-matrix-eig/`, `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md (required for Phase 6), data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
- [X] T002 Initialize Python 3.x project with dependencies in `code/requirements.txt` with **explicit version pinning** (e.g., `numpy==1.26.4`, `scipy==1.13.0`, `pydantic==2.7.0`, `matplotlib==3.9.0`, `pandas==2.2.2`, `ruff==0.4.0`, `black==24.3.0`) to satisfy Constitution Principle I (Reproducibility) and Principle V (Versioning Discipline).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/` by creating `code/.ruff.toml` with standard rules and `code/pyproject.toml` with `[tool.black]` configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management for seeds, tolerances, and paths in `code/utils/config.py`
- [X] T005 [P] Implement data hygiene utilities (checksums) in `code/utils/checksum.py` per Constitution Principle III
- [X] T006 [P] Create base data models/entities in `code/data_models.py` implementing `SimulationRun` and `PerturbationConfig` Pydantic models with full schema (run_id, N, seed, theta, eigenvalues, outlier_flag, rank, support_density, type) to satisfy the Data Model requirement for linking raw data to logical runs.
- [X] T007a [P] Implement iterative solver wrapper with `tol=1e-10` in `code/analysis/eigen_solver.py` using `scipy.sparse.linalg.eigsh` and `LinearOperator`; ensure convergence criteria are met and handle non-convergence gracefully.
- [X] T007b [P] Implement validation logic function in `code/analysis/eigen_solver.py` to distinguish outliers from numerical artifacts using a strict tolerance of `1e-10` relative to the theoretical semicircle edge (±2.0). This task implements the **pure function** for validation (binary pass/fail) and does not execute on data; execution is delegated to downstream tasks. (Depends on T006).
- [X] T008 [P] Implement outlier detection logic (bulk edge vs. BBP prediction) in `code/analysis/outlier_detect.py`
- [X] T012 [P] Implement Wigner matrix generator (dense, scaled $1/\sqrt{N}$) in `code/generators/wigner.py`. This task is foundational and must be completed before US1 (T014) and US2 (T020).
- [X] T013 [P] Implement perturbation matrix constructor (diagonal, block-sparse, random sparse) in `code/generators/perturbation.py`; verify rank preservation during sparsity masking per Spec Objectives 2, 7 and Constitution Principle VII (Sparse Perturbation Structural Fidelity). This task includes generation of 'block-sparse' and 'random sparse' perturbation matrices with explicit rank and support density parameters.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Spectral Analysis of Perturbed Wigner Matrices (Priority: P1) 🎯 MVP

**Goal**: Generate Wigner matrices, apply deterministic sparse perturbations, and compute eigenvalues to identify outliers.

**Independent Test**: Run a script generating a single N=1000 instance with a rank-1 diagonal perturbation (θ=2.5) and verify an eigenvalue > 2.0 exists.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for Wigner matrix generation (mean/variance check) in `tests/unit/test_wigner.py`
- [X] T011 [P] [US1] Unit test for perturbation construction (rank/sparsity verification) in `tests/unit/test_perturbation.py`

### Implementation for User Story 1

- [ ] T019 [US1] **ATOMIC DATA HYGIENE**: Generate raw Wigner matrix instances and immediately checksum them. Read seed from `config.py` or CLI arg `--seed` (default 42). Save matrix to `data/raw/matrix_N{N}_seed{seed}.npy` using NumPy. Compute SHA-256 checksum and write to `state/checksums_raw.json`. This task MUST produce the `.npy` file and the checksum entry atomically per Constitution Principle III. (Depends on T005, T012).
- [ ] T019b [US1] **TRACEABILITY**: Immediately associate the checksum generated in T019 with the `SimulationRun` metadata record in `data/processed/single_run_results.json` (or a preliminary metadata file), capturing parameters (N, seed, theta) and the checksum hash to satisfy the Data Model requirement for linking raw data to logical runs. (Depends on T019).
- [X] T014 [US1] Implement core simulation loop: load raw matrix from `data/raw/` (produced by T019), add $P_N$, compute top 10 eigenvalues in `code/main.py` (single run mode). (Depends on T019, T013, T007a, T007b).
- [X] T015 [US1] Add logic to record results (eigenvalues, perturbation params) to `data/processed/single_run_results.json` with metadata schema: `{"run_id": str, "N": int, "theta": float, "seed": int, "eigenvalues": list, "outlier_flag": bool}` to satisfy Constitution Principle III (Data Hygiene).
- [X] T017 [US1] Add structured logging for simulation run parameters; write structured JSON logs to `data/logs/simulation_run.log` including the exact random seed state, parameter values, and timestamp to satisfy Constitution Principle I (Reproducibility).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phase Transition Threshold Detection (Priority: P2)

**Goal**: Systematically sweep perturbation norms and dimensions to empirically determine the critical threshold $\theta_c$.

**Independent Test**: Execute a parameter sweep script and verify the output dataset shows a monotonic transition from "no outlier" to "outlier" as $\theta$ increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Integration test for full parameter sweep (small N, few runs) in `tests/integration/test_sweep.py`

### Implementation for User Story 2

- [X] T040a [US2] **ATOMIC DATA HYGIENE & GRID DEFINITION**: Define the parameter grid explicitly: N: [low, medium, high ranges], theta: [a range of values], seeds: [, 123, 456, 789] (deterministic list). For each configuration, generate raw matrix instances and immediately checksum them. Save to `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`. Compute SHA-256 checksums and record in `state/checksums_sweep.json`. This task MUST produce all `.npy` files and checksums atomically before any downstream processing per Constitution Principle III. (Depends on T005, T012).
- [X] T040b [US2] **DENSITY GRID DEFINITION**: Define the sparsity density grid for sensitivity analysis: densities: [a range of low to moderate values], seeds: [, 123, 456]. This task produces the configuration file `data/configs/density_grid.json` used by T028. (Depends on T006).
- [X] T020a [US2] Implement parameter sweep orchestrator in `code/analysis/threshold_sweep.py` that: (1) consumes the parameter grid from T040a, (2) ingests the checksummed raw data, (3) executes the simulation loop, (4) manages iterations, and (5) produces `data/processed/mc_results.csv` and `data/processed/convergence_data.json` (containing solver residuals). T020a depends on T040a completion. (Depends on T040a, T014, T007a).
- [X] T020b [US2] **VALIDATION**: Apply the 1e-10 outlier validation logic (from T007b) to the sweep results in `data/processed/mc_results.csv` to ensure every data point meets the spec's strict tolerance before fitting. Output validated results to `data/processed/validated_sweep_results.csv`. **Schema**: The output CSV contains columns `run_id`, `N`, `theta`, `seed`, `eigenvalue_top`, `outlier_flag` (boolean). **No statistical residuals are produced here.** (Depends on T020a, T040a, T007b).
- [X] T021c [US2] **ATOMIC ANALYSIS & VALIDATION**: Run Monte Carlo sweep and fit threshold model. Implement statistical inference logic using 'Logistic Regression' with `solver='lbfgs'`, `max_iter=1000`, and `tol=1e-8` to calculate transition probability and derive the critical $\theta_c$ value with confidence intervals. **CRITICAL**: Validate that the Logistic Regression model converges within the specified `tol=1e-8` (standard statistical convergence) internally. **Input**: `data/processed/validated_sweep_results.csv` (produced by T020b) containing binary outlier flags. **Output**: `data/processed/threshold_identification.json`. This task does NOT consume statistical residuals; it consumes binary flags to fit a probability curve. (Depends on T020b, T020a, T040a).
- [X] T023 [US2] **PRIMARY DELIVERABLE**: Extract the fitted critical threshold $\theta_c$ and its confidence interval from the statistical model and write to `data/processed/critical_threshold_report.json` as the primary answer to Spec Objective 4. (Depends on T021c).
- [X] T022b [US2] Extract fitted parameters and validate fit quality against standard statistical metrics (e.g., R-squared, AIC) in `code/analysis/fit_utils.py`. (Depends on T021c).
- [X] T022c [US2] Write fitted parameters to `data/processed/threshold_fit_params.json`. (Depends on T021c).
- [X] T024 [US2] Generate aggregated results file `data/processed/threshold_sweep_results.csv` by combining validated results and fitted parameters. (Depends on T020b, T021c).
- [X] T025 [US2] Add visualization script to plot probability of outlier emergence vs. $\theta$ for different sparsity patterns; output plot to `data/figures/outlier_probability_vs_theta.png`. **Input**: `data/processed/threshold_sweep_results.csv` (produced by T024). (Depends on T024).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Sparsity Thresholds (Priority: P3)

**Goal**: Perform sensitivity analysis on sparsity parameters to ensure findings are robust to discrete configuration choices.

**Independent Test**: Run a script sweeping sparsity density $p \in \{0.1, 0.2, 0.3\}$ and verify the report explicitly states if $\theta_c$ shifts > 5%.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for sparsity density calculation and mask generation in `tests/unit/test_sparsity_utils.py`

### Implementation for User Story 3

- [X] T031a_impl [US3] Implement logic to generate the rank-0 (unperturbed) Wigner matrix and run spectral analysis to produce the verification log.
- [X] T031 [US3] Verify semicircle law compliance for rank $k=0$ using results from T031a_impl; output verification log to `data/logs/edge_case_rank0.log`. (Depends on T031a_impl).
- [X] T027 [P] [US3] Implement sparsity sensitivity runner (fixed rank, variable support density) in `code/analysis/sensitivity_analysis.py`
- [X] T028 [US3] Execute sweep over support density set $\{0.1, 0.2, 0.3, 0.4, 0.5\}$ for each sparsity pattern type (diagonal, block-sparse, random sparse); **run multiple seeds per density level** to generate a distribution of results; output results to `data/processed/sensitivity_density_sweep.csv` including `theta_c` per run. **Reuses T020a orchestrator logic** but applies it to density sweeps defined in T040b. (Depends on T013, T006, T040b, T020a, T040a).
- [X] T028b [US3] **DATA MODEL**: Instantiate and record the `PerturbationConfig` entity for each sensitivity run in `data/processed/sensitivity_metadata.json`, capturing 'rank' and 'support density' explicitly as required by the spec. (Depends on T028).
- [X] T029b_impl [US3] Implement statistical validation logic (calculate p-values or confidence intervals on the threshold shift) in `code/analysis/sensitivity_analysis.py` to prove robustness as required by the plan; output `data/processed/sensitivity_statistics.json`.
- [X] T029a [US3] Compute variation in critical threshold $\theta_c$. Use the specific metric: 'Calculate the standard deviation of the critical threshold theta_c values across the density sweep' by reading `data/processed/sensitivity_density_sweep.csv` (produced by T028). **CRITICAL**: Perform a two-sample t-test using `scipy.stats.ttest_ind` grouping by density level to verify the 'robustness' claim. **Null Hypothesis (H0)**: There is no difference in mean $\theta_c$ between density levels. **Grouping Variable**: Support density. If the shift in $\theta_c$ is > 5% with p < 0.05, flag as sensitive. Output `data/processed/sensitivity_variation.csv` with schema: `{"density": float, "theta_c": float, "std_dev": float, "p_value": float, "shift_flag": bool}`. (Depends on T028, T029b_impl).
- [X] T030 [US3] Generate sensitivity report `data/processed/sensitivity_report.md` stating stability or shift magnitude, including statistical validation results. (Depends on T029a).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation, Contextualization & Polish (Priority: P1)

**Goal**: Ensure documentation, reproducibility, and performance meet project standards while explicitly framing the study as observational and addressing the "observer" critique from prior research reviews (FR-007).

**Independent Test**: Verify that `quickstart.md` and `research.md` are complete, reproducible, and explicitly state that the "observer" is the computational algorithm measuring spectral statistics, not a physical entity, aligning with the EPR critique response.

### Implementation for Documentation & Contextualization

- [X] T032_init [P] [Docs] Create and initialize `research.md` with the project overview, methodology, and initial structure, addressing the need for a target artifact for subsequent updates.
- [X] T032a [P] [Docs] Update `quickstart.md` to include instructions for reproducing the full parameter sweep and sensitivity analysis.
- [X] T033 [P] [Docs] **INITIAL FR-007 CONTEXT**: Update `research.md` to explicitly address the EPR critique and FR-007. This single task MUST: (1) Define the "observer" as the deterministic algorithm (spectral solver) measuring statistical correlations in simulated data, (2) Distinguish between the mathematical model (Wigner matrices + perturbations) and potential physical analogs, (3) Explicitly state that no specific physical system is being modeled, and (4) Add a "Limitations" section clarifying that "sparse perturbations" are mathematical constructs, not physical fluctuations. This task sets the initial context for the final resolution. (Depends on T032_init).
- [X] T035 [P] Code cleanup and refactoring for memory efficiency (ensure < 7 GB RAM for N=2000); generate memory profile report `state/memory_profile_N2000.log` to verify compliance. Use `memory_profiler` to record peak memory usage and verify it remains within the runner's physical limit (~7 GB) without hardcoding a specific threshold flag.
- [X] T035b [P] [Docs] **CODE VERIFICATION**: Perform a static analysis or audit of `code/` to verify adherence to FR-007 (purely observational constraint), ensuring the implementation strictly adheres to the "purely observational" constraint. Output `state/code_observation_audit.log`.
- [X] T035c [P] **CONSTRAINT VERIFICATION**: Verify the "No GPU" constraint across the entire codebase by checking `config.py` and CI scripts for any GPU device assignments; ensure all solvers are CPU-bound. Output `state/gpu_constraint_audit.log`.
- [X] T036 Performance optimization: verify full parameter sweep completes within 6 hours; record execution time in `state/sweep_timing.log`.
- [X] T037 [P] Additional unit tests for edge cases (N=100, $\theta=1.0$, rank=0) in `tests/unit/`
- [X] T038 Run `quickstart.md` validation to ensure reproducibility; output pass/fail log to `state/quickstart_validation.log`.
- [X] T039 Final checksum generation for all `data/` artifacts in `state/checksums.json`.

**Checkpoint**: The project now includes rigorous documentation and performance validation while strictly adhering to observational constraints and addressing the "observer" critique.

---

## Phase 7: EPR Critique Response & Conceptual Clarification (Priority: P1) 🎯 Review Response

**Goal**: Directly address the "observer" and "frame of reference" critique from the Albert Einstein (simulated) review by explicitly defining the computational observer and the nature of the "sparse" perturbations as mathematical constructs rather than physical fluctuations.

**Independent Test**: Verify that `research.md` contains a dedicated section defining the "observer" as the spectral solver algorithm and explicitly stating that the project models a mathematical system, not a physical quantum field or chaotic billiard, thereby satisfying the EPR demand for a correspondence between theory and the defined computational reality.

### Implementation for EPR Critique Response

- [X] T041 [P] [Docs] **FINAL EPR CRITIQUE RESOLUTION**: Update `research.md` to include a new section "The Computational Observer and Frame of Reference". This section MUST: (1) Define the "observer" as the deterministic algorithm (the spectral solver and statistical aggregator) that measures correlations in the simulated data, (2) Explicitly state that the "sparse perturbations" are controlled mathematical parameters (rank, support density) rather than physical noise or lack of knowledge, (3) Clarify that the "probability distribution" arises from the ensemble of random matrix realizations generated by the algorithm, not from a physical gambling table, and (4) Reiterate that the project is a study of asymptotic mathematical behavior, not a model of a specific physical system (e.g., quantum field, chaotic billiard). This task directly resolves the "where is the observer?" and "God does not play dice" critiques by reframing the dice as a controlled mathematical parameter and the observer as the code itself. **This task depends on T033 to ensure the initial context is established before the final resolution is applied.** (Depends on T032_init, T033).
- [X] T042 [P] [Docs] **PHYSICAL REALITY CORRESPONDENCE**: Update `research.md` to include a "Correspondence with Physical Reality" subsection. This subsection MUST: (1) State clearly that the random matrices are mathematical objects with no direct physical counterpart in this specific study, (2) Explain that while Wigner matrices are often used to model physical systems (nuclear spectra, chaotic billiards), this project isolates the mathematical phenomenon of the BBP transition without asserting a physical model, and (3) Define the "elements of physical reality" in this context as the reproducible, deterministic outputs of the algorithm (eigenvalues, thresholds) which correspond to the mathematical elements of the theory. This addresses the EPR demand for a one-to-one correspondence between theory and reality by defining the reality as the computational experiment itself. (Depends on T041).
- [X] T043 [P] [Docs] **LIMITATIONS AND SCOPE**: Update `research.md` to expand the "Limitations" section to explicitly address the critique. This MUST include: (1) A statement that the "sparse" nature of the perturbation is a mathematical constraint, not a physical fluctuation, (2) A clarification that the "observer" is the algorithm, not a conscious entity or physical frame, and (3) A disclaimer that the findings are valid for the defined mathematical ensemble but do not necessarily imply physical laws for unknown systems. This ensures the project does not overclaim physical significance. (Depends on T042).
- [X] T044 [P] [Docs] **REVIEW RESPONSE LOG**: Create `state/review_response_einstein.log` documenting exactly how tasks T041, T042, and T043 address the specific points raised in the `albert-einstein-simulated__2026-06-03__research.md` review (observer, frame of reference, physical reality, "God does not play dice"). This log serves as the audit trail for the revision. (Depends on T043).

**Checkpoint**: The project now explicitly addresses the EPR-style critique by defining the computational observer, clarifying the mathematical nature of the perturbations, and establishing a clear correspondence between the theory and the defined computational reality.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Documentation & Contextualization (Phase 6)**: Can run in parallel with User Story implementation but must be complete before final paper drafting; depends on Foundational phase for data model context and T032_init for the research.md artifact.
- **EPR Critique Response (Phase 7)**: Depends on T032_init (creation of research.md) AND T033 (initial FR-007 context) to ensure sequential updates to the same artifact. T041 explicitly depends on T033. T042 depends on T041. T043 depends on T042. T044 depends on T043.
- **Polish (Final Phase)**: Depends on all desired user stories and review responses being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses US1 generators; T020a depends on T040a for raw data hygiene. T020b depends on T040a and T020a. T021c depends on T040a, T020a, and T020b.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses US1/US2 logic; T028 depends on T040b (density grid), T020a (orchestrator), and T040a (grid definition).
- **Documentation & Contextualization (Phase 6)**: Depends on Foundational phase for data model context; can proceed independently of specific US implementation details but requires the data model structure and T032_init for the research.md artifact.
- **EPR Critique Response (Phase 7)**: Depends on T032_init (creation of research.md) and T033 (initial FR-007 context) and can proceed independently of specific US implementation details.
- **Polish (Final Phase)**: Depends on all desired user stories and review responses being complete

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
- EPR Critique Response tasks (Phase 7) can run in parallel with Phase 6 and User Story implementation once T032_init and T033 are complete.

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
5. Add EPR Critique Response (Phase 7) → Validate conceptual clarity
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Must complete T040a before T020a)
 - Developer C: User Story 3 (Must complete T040b before T028)
 - Developer D: Documentation & Contextualization (Phase 6, starting with T032_init) AND EPR Critique Response (Phase 7, starting with T041 after T033)
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
- **Review Response (T033, T041-T044)**: These tasks directly address prior EPR-style critiques. T033 establishes the initial context (Initial FR-007 Context), while T041 provides the final resolution (Final EPR Critique Resolution) with explicit dependency T041 -> T033 to ensure sequential updates to research.md. This task implements Spec Key Assumptions (FR-007).
- **Data Hygiene Note**: Task T040a ensures raw data for the sweep is checksummed before T020a processes it, strictly adhering to Constitution Principle III. Task T019 ensures raw data for US1 is checksummed before T014. T019b links the checksum to the metadata record. T005 provides the utility for both.
- **Ordering Note**: T019 (generate+checksum) must complete before T019b. T040a (generate+checksum) must complete before T020a. T040b (density grid) must complete before T028. T032_init (create research.md) must complete before T033 and T041. T033 must complete before T041. T041 must complete before T042. T042 must complete before T043. T043 must complete before T044. T031a_impl (generate unperturbed) must complete before T031. T029b_impl (implement logic) must complete before T029a. T020a (produce mc_results.csv) must complete before T021c. T028 (produce sensitivity_density_sweep.csv with multiple seeds) must complete before T029a. T028 depends on T040b (density grid), T020a (orchestrator), and T040a (grid definition). T020b depends on T040a (grid definition) and T020a. T021c depends on T040a (grid definition), T020a, and T020b.