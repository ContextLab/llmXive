---
description: "Task list for Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations"
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
- [X] T002 Initialize Python 3.x project with dependencies in `code/requirements.txt` with **explicit version pinning** (e.g., `numpy==1.26.4`, `scipy==1.13.0`, `pydantic==2.7.0`, `matplotlib==3.9.0`, `pandas==2.2.2`, `ruff==0.4.0`, `black==24.3.0`) to satisfy Constitution Principle I (Reproducibility) and Principle V (Versioning Discipline). The deliverable is the content of `code/requirements.txt`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/` by creating `code/.ruff.toml` with standard rules and `code/pyproject.toml` with `[tool.black]` configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management for seeds, tolerances, and paths in `code/utils/config.py` including a configurable `OUTLIER_TOLERANCE` parameter (default e).
- [X] T005 [P] Implement data hygiene utilities (checksums) in `code/utils/checksum.py` per Constitution Principle III
- [X] T006 [P] Create base data models/entities in `code/data_models.py` implementing `SimulationRun` and `PerturbationConfig` Pydantic models with full schema. `SimulationRun` must include: run_id, N, seed, theta, eigenvalues, outlier_flag. `PerturbationConfig` must include: rank, support_density, type (diagonal, block-sparse, random sparse). This satisfies the Data Model requirement for linking raw data to logical runs.
- [X] T007a Implement iterative solver wrapper with `tol` loaded from `config.py` in `code/analysis/eigen_solver.py` using `scipy.sparse.linalg.eigsh` and `LinearOperator`; ensure convergence criteria are met and handle non-convergence gracefully. (Depends on T004, T006).
- [X] T007b Implement validation logic function in `code/analysis/eigen_solver.py` to distinguish outliers from numerical artifacts using a strict tolerance loaded from `config.py` (default a sufficiently small value) relative to the theoretical semicircle edge (±2.0). This task implements the **pure function** for validation (binary pass/fail) and does not execute on data; execution is delegated to downstream tasks. (Depends on T004, T006). **Traceability**: This task implements Spec Validation Criteria (strict tolerance).
- [X] T008 Implement outlier detection logic (bulk edge vs. BBP prediction) in `code/analysis/outlier_detect.py` (Depends on T007b).
- [X] T012 Implement Wigner matrix generator (dense, scaled $1/\sqrt{N}$) in `code/generators/wigner.py`. This task is foundational and must be completed before US1 (T014) and US2 (T020a). (Depends on T006).
- [X] T013 Implement perturbation matrix constructor (diagonal, block-sparse, random sparse) in `code/generators/perturbation.py`; verify rank preservation during sparsity masking per Spec Objectives 2, 7 and Constitution Principle VII (Sparse Perturbation Structural Fidelity). This task includes generation of 'block-sparse' and 'random sparse' perturbation matrices with explicit rank and support density parameters. (Depends on T006).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Spectral Analysis of Perturbed Wigner Matrices (Priority: P1) 🎯 MVP

**Goal**: Generate Wigner matrices, apply deterministic sparse perturbations, and compute eigenvalues to identify outliers.

**Independent Test**: Run a script generating a single N=1000 instance with a rank-1 diagonal perturbation (θ=2.5) and verify an eigenvalue > 2.0 exists.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for Wigner matrix generation (mean/variance check) in `tests/unit/test_wigner.py`
- [X] T011 [P] [US1] Unit test for perturbation construction (rank/sparsity verification) in `tests/unit/test_perturbation.py`

### Implementation for User Story 1

- [X] T019 [US1] **ATOMIC DATA HYGIENE**: Generate raw Wigner matrix instances and immediately checksum them. Read seed from `config.py` or CLI arg `--seed` (default a representative baseline value). Execute `python code/generators/wigner.py --seed <seed_value> --N <N_value>` to produce `data/raw/matrix_N{N}_seed{seed}.npy`. Compute SHA-256 checksum and write to `state/metadata_registry.json` (unified registry). This task MUST produce the `.npy` file and the checksum entry atomically per Constitution Principle III. (Depends on T005, T012).
- [ ] T019b [US1] **TRACEABILITY**: Create or update the `state/metadata_registry.json` file to register the checksum generated in T019 with the `SimulationRun` metadata record. The JSON schema MUST be: `{ "runs": [ { "run_id": str, "checksum": str, "parameters": { "N": int, "seed": int, "theta": float } } ] }`. If the file does not exist, this task MUST create it. (Depends on T019).
- [ ] T014 [US1] Implement core simulation loop: load raw matrix from `data/raw/` (produced by T019), load perturbation logic from T013 (code artifact) to construct $P_N$ in memory, compute top eigenvalues in `code/main.py` (single run mode). **Validation**: This task MUST call the validation function from T007b to determine the `outlier_flag`. **Deliverable**: This task must expose a reusable function `run_single_simulation(params)` in `code/analysis/simulation_loop.py` that can be imported by downstream tasks. (Depends on T019, T013, T007a, T007b).
- [ ] T015 [US1] Add logic to record results (eigenvalues, perturbation params) to `data/processed/single_run_results.json` with metadata schema: `{"run_id": str, "N": int, "theta": float, "seed": int, "eigenvalues": list, "outlier_flag": bool}` to satisfy Constitution Principle III (Data Hygiene).
- [ ] T017 [US1] Add structured logging for simulation run parameters; write structured JSON logs to `data/logs/simulation_run.log` including the exact random seed state, parameter values, and timestamp to satisfy Constitution Principle I (Reproducibility).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phase Transition Threshold Detection (Priority: P2)

**Goal**: Systematically sweep perturbation norms and dimensions to empirically determine the critical threshold $\theta_c$.

**Independent Test**: Execute a parameter sweep script and verify the output dataset shows a monotonic transition from "no outlier" to "outlier" as $\theta$ increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Integration test for full parameter sweep (small N, few runs) in `tests/integration/test_sweep.py`

### Implementation for User Story 2

- [ ] T040a [US2] **ATOMIC DATA HYGIENE & GRID DEFINITION**: Define the parameter grid explicitly: N: [lower bound, intermediate values, upper bound], theta: [range of values], seeds: [,, 456, 789]. For each configuration, generate raw matrix instances and immediately checksum them. Save to `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`. Compute SHA-256 checksums and record in `state/metadata_registry.json` (unified registry). This task MUST produce all `.npy` files and checksums atomically before any downstream processing per Constitution Principle III. (Depends on T005, T012).
- [ ] T040c [US2] **GRID LOADER**: Implement a generic grid loader in `code/utils/grid_loader.py` that can consume any parameter grid (theta or density) and yield configurations. (Depends on T006).
- [ ] T014b [US2] **REUSABLE SIMULATION LOOP**: Extract the core simulation loop logic from T014 into a reusable function in `code/analysis/simulation_loop.py` that accepts parameters (N, theta, seed, perturbation_type) and returns eigenvalues and outlier flags. (Depends on T014, T007a, T007b).
- [ ] T020a [US2] **GENERIC ORCHESTRATOR**: Implement a generic simulation orchestrator in `code/analysis/threshold_sweep.py` that: (1) consumes any parameter grid (theta or density) via T040c, (2) ingests checksummed raw data from `state/metadata_registry.json`, (3) executes the simulation loop using the reusable function from T014b, (4) manages iterations, and (5) produces raw results. (Depends on T014b, T007a, T040c).
- [ ] T020b [US2] **THETA SWEEP EXECUTION**: Run the generic orchestrator (T020a) specifically for the theta grid defined in T040a. Output raw results to `data/processed/mc_results.csv` and `data/processed/convergence_data.json`. (Depends on T020a, T040a).
- [ ] T020c [US2] **VALIDATION**: Apply the e-10 outlier validation logic (from T007b) to the sweep results in `data/processed/mc_results.csv` to ensure every data point meets the spec's strict tolerance before fitting. Output validated results to `data/processed/validated_sweep_results.csv`. **Schema**: The output CSV contains columns `run_id`, `N`, `theta`, `seed`, `eigenvalue_top`, `outlier_flag` (boolean). **No statistical residuals are produced here.** (Depends on T020b).
- [ ] T021c [US2] **ATOMIC ANALYSIS & VALIDATION**: Run statistical inference logic to calculate transition probability and derive the critical $\theta_c$ value. **Input**: `data/processed/validated_sweep_results.csv` (produced by T020c). **Method**: MUST use Logistic Regression via `scikit-learn` to fit the probability of outlier emergence vs. $\theta$. **Explicit Input Mapping**: Feature column = 'theta', Target column = 'outlier_flag'. **Input Filtering**: Input data MUST be pre-filtered by the T007b tolerance logic (outlier_flag must be boolean and derived from strict tolerance relative to the theoretical semicircle edge). **Output**: `data/processed/threshold_identification.json` with schema: `{ "theta_c": float, "confidence_interval": [float, float], "method": "logistic_regression" }`. (Depends on T020c, T007b).
- [ ] T024 [US2] Generate aggregated results file `data/processed/threshold_sweep_results.csv` by combining validated results and fitted parameters. (Depends on T020c, T021c).
- [ ] T024b [US2] **DATA MODEL VALIDATION**: Write a validation script in `code/analysis/validate_data.py` that reads `data/processed/threshold_sweep_results.csv`, instantiates `SimulationRun` objects from T006 for each row, and writes a log `data/logs/validation_log.txt`. (Depends on T024, T006).
- [ ] T025 [US2] Add visualization script to plot probability of outlier emergence vs. $\theta$ for different sparsity patterns; output plot to `data/figures/outlier_probability_vs_theta.png`. **Input**: `data/processed/threshold_sweep_results.csv` (produced by T024). **Dependency**: Must run after T024b to ensure validated data. (Depends on T024, T024b).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Sparsity Thresholds (Priority: P3)

**Goal**: Perform sensitivity analysis on sparsity parameters to ensure findings are robust to discrete configuration choices.

**Independent Test**: Run a script sweeping sparsity density $p$ across a range of values and verify the report explicitly states if $\theta_c$ shifts.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for sparsity density calculation and mask generation in `tests/unit/test_sparsity_utils.py`

### Implementation for User Story 3

- [ ] T031a_impl [US3] Implement logic to generate the rank-0 (unperturbed) Wigner matrix and run spectral analysis to produce the verification log.
- [ ] T031 [US3] Verify semicircle law compliance for rank $k=0$ using results from T031a_impl; output verification log to `data/logs/edge_case_rank0.log`. (Depends on T031a_impl).
- [ ] T027 [P] [US3] Implement sparsity sensitivity runner (fixed rank, variable support density) in `code/analysis/sensitivity_analysis.py`
- [ ] T040b [US3] **DENSITY GRID DEFINITION**: Define the sparsity density grid for sensitivity analysis: densities spanning a range of low to moderate values, seeds: [multiple distinct values]. This task produces the configuration file `data/configs/density_grid.json` used by T028. (Depends on T006).
- [ ] T028 [US3] Execute sweep over support density set $\{, 0.3, 0.4, 0.5\}$ for each sparsity pattern type (diagonal, block-sparse, random sparse); **run multiple seeds per density level** to generate a distribution of results; output results to `data/processed/sensitivity_density_sweep.csv` including `theta_c` per run. **Reuses T020a orchestrator logic** but adapts it by passing the density grid file `data/configs/density_grid.json` as an argument (e.g., `--grid-file data/configs/density_grid.json --grid-type density`). (Depends on T013, T006, T040b, T020a, T040c).
- [ ] T028b [US3] **DATA MODEL**: Instantiate and record the `PerturbationConfig` entity for each sensitivity run in `data/processed/sensitivity_metadata.json`, capturing 'rank' and 'support density' explicitly as required by the spec. (Depends on T028).
- [ ] T029a [US3] Compute variation in critical threshold $\theta_c$. **Input**: `data/processed/sensitivity_density_sweep.csv` (produced by T028). **Method**: Group rows by `density` column, compute mean and standard deviation of `theta_c` for each group to observe trends. Report the variation in theta_c across density levels. Output `data/processed/sensitivity_variation.csv` with schema: `{"density": float, "mean_theta_c": float, "std_dev": float}`. (Depends on T028, T028b).
- [ ] T030 [US3] Generate sensitivity report `data/processed/sensitivity_report.md` stating stability or shift magnitude, including statistical validation results. (Depends on T029a).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation, Contextualization & Polish (Priority: P1)

**Goal**: Ensure documentation, reproducibility, and performance meet project standards while explicitly framing the study as observational (FR-007) without modeling a physical observer.

**Independent Test**: Verify that `quickstart.md` and `research.md` are complete, reproducible, and explicitly state that the study is purely observational and computational, avoiding any modeling of a "physical observer".

### Implementation for Documentation & Contextualization

- [ ] T032_init [P] [Docs] Create and initialize `research.md` with the project overview, methodology, and initial structure, explicitly stating the study is purely observational and computational (FR-007).
- [ ] T032a [P] [Docs] Update `quickstart.md` to include instructions for reproducing the full parameter sweep and sensitivity analysis, and explicitly state the observational nature of the study.
- [ ] T035 [P] Code cleanup and refactoring for memory efficiency (ensure < 7 GB RAM for N=2000); generate memory profile report `state/memory_profile_N2000.log` to verify compliance. Use `memory_profiler` to record peak memory usage. **Deliverable**: `state/memory_profile_N2000.log` must be a JSON file with schema: `{"timestamp": str, "peak_mb": float, "function_name": str}`. (Depends on T014).
- [ ] T035_new [P] **NUMERICAL STABILITY VALIDATION**: Run a simulation with N=2000 (memory-efficient configuration) and compare the resulting eigenvalues against the theoretical semicircle edge (±2.0). **Validation**: If the comparison fails (outliers are not consistent with theory), the task MUST fail and output an error log. **Deliverable**: `state/numerical_stability_N2000.log` with schema: `{"timestamp": str, "status": "PASS"|"FAIL", "eigenvalue_deviation": float}`. (Depends on T014, T007b).
- [ ] T035b [P] [Docs] **CODE VERIFICATION**: Perform a static analysis or audit of `code/` to verify adherence to FR-007 (purely observational constraint). Run `grep -r "physical" code/ --exclude-dir=__pycache__ --exclude="*.pyc"`. If any matches are found that imply a physical observer (excluding comments about FR-007), flag as failure. Output `state/code_observation_audit.log` with the results. **Schema**: JSON object with `{"status": "PASS"|"FAIL", "matches": [{"file_path": str, "line_number": int, "matched_text": str}]}`. (Depends on T035).
- [ ] T035c [P] **CONSTRAINT VERIFICATION**: Verify the "No GPU" constraint across the entire codebase by checking `config.py` and CI scripts for any GPU device assignments. Run `grep -r "torch.cuda\|device=cuda" code/`. Output `state/gpu_constraint_audit.log` with the results (list of matches or "PASS"). (Depends on T035).
- [ ] T036 Performance optimization: verify full parameter sweep completes within 6 hours; record execution time in `state/sweep_timing.log`.
- [ ] T037 [P] Additional unit tests for edge cases (N=100, $\theta=1.0$, rank=0) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure reproducibility; output pass/fail log to `state/quickstart_validation.log`.
- [ ] T039 [P] Final checksum generation for all `data/` and `state/` artifacts in `state/checksums.json`, including `state/sanity_baseline.json` if present.

**Checkpoint**: The project now includes rigorous documentation and performance validation while strictly adhering to observational constraints.

---

## Phase 7: Final Verification & Re-Validation (Priority: P1) 🎯 Review Closure

**Goal**: Re-run the full verification pipeline to ensure that the conceptual clarifications in Phase 6 have not introduced logical inconsistencies in the data generation or analysis pipeline, and to provide a final "clean" state for the project.

**Independent Test**: Execute the full `quickstart.md` pipeline end-to-end and verify that all artifacts (raw data, processed results, reports) are checksummed, reproducible, and that the `research.md` document explicitly references the observational nature of the study.

### Implementation for Final Verification

- [ ] T051a [Test] **BASELINE GENERATION**: Run a single small-scale simulation (N=100, theta=2.5, seed=42) using `code/main.py` and save the output eigenvalue and metadata to `state/sanity_baseline.json`. This artifact MUST be created before T051. (Depends on T014, T007a).
- [ ] T051 [Test] **SANITY CHECK**: Execute a single small-scale run (N=100, theta=2.5) to verify that the code still runs correctly after documentation updates. Run `python code/main.py --N 100 --seed 42`. Compare the output eigenvalue against the stored baseline `state/sanity_baseline.json` (produced by T051a) with a strict numerical tolerance of **1e-6** (absolute difference). **Comparison Logic**: `abs(eigenvalue_current - eigenvalue_baseline) < 1e-6`. If the baseline file is missing or invalid, the task MUST fail and output an error log. Output `state/sanity_check_log.txt` confirming successful execution. (Depends on T051a).

**Checkpoint**: The project is fully closed, with all EPR-style critiques addressed, documented, and re-validated.

---

## Phase 8: Review Response - Mathematical Ensemble Definition (Priority: P1)

**Goal**: Explicitly define the mathematical ensemble and clarify the lack of a physical frame of reference, ensuring the study remains within the "mathematical ensemble" boundary without modeling an observer.

**Independent Test**: Verify that `research.md` contains a dedicated section explicitly defining the Wigner Ensemble and Sparse Perturbations as purely mathematical constructs.

### Implementation for Review Response

- [ ] T061 [Docs] **MATHEMATICAL ENSEMBLE DEFINITION**: Update `research.md` (Section 2: Mathematical Framework) to explicitly define the "Wigner Ensemble" and "Sparse Perturbations" as purely mathematical constructs. This task must state that the "probability distribution" describes the statistical properties of the ensemble, not a physical stochastic process. **Append Text**: "The Wigner Ensemble is defined as the set of symmetric matrices with independent, identically distributed entries. Sparse perturbations are deterministic matrices added to this ensemble. No physical observer or frame of reference is modeled; the study is purely computational and observational." (Depends on T032_init).
- [ ] T062 [Docs] **GAMBLING TABLE ANALOGY RESPONSE**: Add a subsection "2.3 The 'Gambling Table' Analogy" to `research.md` that directly addresses the reviewer's comment. It must explain that while the distribution is abstract, the BBP transition is a rigorous mathematical theorem (proven in literature) that holds for the ensemble regardless of physical interpretation. The "gambling table" is a metaphor for the statistical ensemble, not a claim about physical randomness. **Append Text**: "The 'gambling table' is a metaphor for the statistical ensemble, not a claim about physical randomness. The BBP transition is a rigorous mathematical theorem." (Depends on T061).
- [ ] T054 [Docs] **EPR CRITIQUE RESPONSE - ACKNOWLEDGE**: Update `research.md` (Section 1: Introduction) to explicitly acknowledge the critique regarding the lack of physical reality. **Append Text**: "We acknowledge the critique that the study lacks a specific physical system model." (Depends on T061).
- [ ] T063a [Docs] **NO PHYSICAL SYSTEM CLAIM - STATE**: Update `research.md` (Section 1: Introduction) to explicitly state: "This project does not claim to model a specific physical system (e.g., quantum field, chaotic billiard)." **Append Text**: "This project does not claim to model a specific physical system (e.g., quantum field, chaotic billiard)." (Depends on T054).
- [ ] T063b [Docs] **NO PHYSICAL SYSTEM CLAIM - FRAME**: Update `research.md` (Section 1: Introduction) to explicitly state: "The matrices are synthetic constructs generated to test the BBP phase transition theorem in a controlled, reproducible environment." **Append Text**: "The matrices are synthetic constructs generated to test the BBP phase transition theorem in a controlled, reproducible environment." (Depends on T063a).
- [ ] T064 [Docs] **FRAME OF REFERENCE CLARIFICATION**: Add a subsection "2.4 Frame of Reference" to `research.md` that clarifies that the "frame of reference" in this context is the computational environment (CPU, random seed, algorithm), not a physical coordinate system. It must state that the results are invariant to this computational frame, satisfying the mathematical requirement for the theorem. **Append Text**: "The 'frame of reference' is the computational environment (CPU, random seed, algorithm), not a physical coordinate system." (Depends on T062).
- [ ] T065 [Docs] **FINAL REVIEW RESPONSE LOG**: Update `state/review_response_einstein.log` to mark the "observer" and "physical reality" critique items as "CLOSED" with a detailed cross-reference to T061, T062, T063, and T064, summarizing how the critique was addressed by clarifying the mathematical nature of the study rather than modeling a physical observer. **Schema**: JSON object with `{"status": "CLOSED", "reference_tasks": ["T061", "T062", "T063", "T064"], "summary": "Clarified mathematical nature of study."}`. (Depends on T064).

**Checkpoint**: The project explicitly addresses the Einstein critique by clarifying the mathematical nature of the study, satisfying the reviewer's philosophical concern without violating the "no physical observer" constraint.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Documentation & Contextualization (Phase 6)**: Can run in parallel with User Story implementation but must be complete before final paper drafting; depends on Foundational phase for data model context and T032_init for the research.md artifact.
- **Final Verification (Phase 7)**: Depends on T051a (Baseline Generation) and T014 (Simulation Loop). T051 depends ONLY on T051a. T051a depends on T014.
- **Review Response (Phase 8)**: Depends on T061 (Ensemble Definition). T054 depends on T061. T063a depends on T054. T063b depends on T063a. T064 depends on T062. T065 depends on T064. T061 depends on T032_init. T062 depends on T061.
- **Polish (Final Phase)**: Depends on all desired user stories and review responses being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses US1 generators; T020a depends on T040a for raw data hygiene. T020b depends on T040a and T020a. T021c depends on T020c.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses US1/US2 logic; T028 depends on T040b (density grid), T020a (generic orchestrator), and T040c (grid loader). Note: US3 cannot run in parallel with US2 until T020a is complete.
- **Documentation & Contextualization (Phase 6)**: Depends on Foundational phase for data model context; can proceed independently of specific US implementation details but requires the data model structure and T032_init for the research.md artifact.
- **Final Verification (Phase 7)**: Depends on T051a (Baseline Generation). T051a depends on T014. T051 depends on T051a.
- **Review Response (Phase 8)**: Depends on T032_init (research.md creation). T061 depends on T032_init. T062 depends on T061. T054 depends on T061. T063a depends on T054. T063b depends on T063a. T064 depends on T062. T065 depends on T064.
- **Polish (Final Phase)**: Depends on all desired user stories and review responses being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T005, T006)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) **EXCEPT** US3 which depends on US2's T020a.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **provided dependencies are met**.
- Documentation & Contextualization tasks (Phase 6) can run in parallel with User Story implementation once the data model is established.
- Final Verification tasks (Phase 7) MUST run sequentially: T051a -> T051.
- Review Response tasks (Phase 8) MUST run sequentially: T061 -> T062 -> T054 -> T063a -> T063b -> T064 -> T065.

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
- **Review Response (T061-T065)**: These tasks directly address prior EPR-style critiques by explicitly stating the observational nature of the study and the lack of physical modeling, without constructing an "observer" model. T061, T062, T054, T063a-b, T064, and T065 ensure the final closure and consistency of these conceptual updates. This task implements Spec Key Assumptions (FR-007).
- **Data Hygiene Note**: Task T040a ensures raw data for the sweep is checksummed before T020a processes it, strictly adhering to Constitution Principle III. Task T019 ensures raw data for US1 is checksummed before T014. T019b links the checksum to the metadata record. T005 provides the utility for both.
- **Ordering Note**: T019 (generate+checksum) must complete before T019b. T040a (generate+checksum) must complete before T020a. T040b (density grid) must complete before T028. T032_init (create research.md) must complete before T033 and T050. T033 must complete before T050. T050 must complete before T051. T051 must complete before T052. T052 must complete before T053. T031a_impl (generate unperturbed) must complete before T031. T014b (reusable loop) must complete before T020a and T028. T040c (grid loader) must complete before T020a and T028. T020a (produce mc_results.csv) must complete before T021c. T028 (produce sensitivity_density_sweep.csv with multiple seeds) must complete before T029a. T020b depends on T040a (grid definition) and T020a. T021c depends on T020c. T050 depends on T032_init. T051a depends on T014. T051 depends on T051a. T052 depends on T051. T053 depends on T052. T054a depends on T032_init and T061. T054b depends on T054a. T054c depends on T054b. T054d depends on T054c. T055 depends on T054d. T056 depends on T055. T014 (single run) must expose a reusable function for T014b. T061 depends on T032_init. T062 depends on T061. T063a depends on T054 and T061. T063b depends on T063a. T064 depends on T062. T065 depends on T064.
- **Phase 7 Execution Order**: Tasks T051a, T051 form a strict sequential chain. T051a must complete before T051.
- **Phase 8 Execution Order**: Tasks T061, T062, T054, T063a, T063b, T064, T065 form a strict sequential chain. T061 must complete before T062. T062 must complete before T054. T054 must complete before T063a. T063a must complete before T063b. T063b must complete before T064. T064 must complete before T065.
- **Data Model Validation**: T024b must complete before T025 to ensure T025 uses validated data.
- **Baseline Generation**: T051a must complete before T051 to ensure the baseline artifact exists.
- **Configurable Tolerance**: T007b uses the tolerance value from T004, ensuring configurability and reproducibility.
- **Explicit Grid Values**: T040a and T040b now contain explicit values for N and density, ensuring executability.
- **Mandatory Method**: T021c mandates Logistic Regression, ensuring a testable success metric.
- **Observer Modeling Prohibited**: Tasks T050-T056 and T061-T065 have been rewritten to focus solely on stating the observational nature of the study without modeling an observer, in strict adherence to FR-007. The new tasks in Phase 8 (T061-T065) explicitly address the reviewer's concern by clarifying the mathematical nature of the study, not by modeling an observer.
- **Parallel Tag Correction**: T007a, T007b, T008, T012, T013 are no longer marked [P] as they depend on T004 and T006.
- **Validation Link**: T021c explicitly depends on T007b for input filtering.
- **Memory Validation**: T035_new includes a validation step against the semicircle edge.
- **File Creation**: T019b explicitly creates the metadata registry if missing.
- **Explicit Tolerance**: T051 uses 1e-6 tolerance for sanity checks with explicit comparison logic.
- **Schema Definitions**: T035, T035b, T051, T021c, T019b have explicit schema definitions.
- **Atomic Tasks**: T050-T056 and T061-T065 are now atomic with specific text templates.
- **Logical Ordering**: Phase 8 tasks now follow the logical order: Define Ensemble (T061) -> Respond to Critique (T062-T065).
- **T019 Status**: T019 and T019b are both marked `[ ]` (incomplete) to ensure logical dependency flow.
- **Numerical Stability**: T035_new is a separate task for numerical validation, distinct from memory profiling T035.
- **Dependency Correction**: T051 no longer depends on T039. T054 depends on T061. T063a depends on T054.