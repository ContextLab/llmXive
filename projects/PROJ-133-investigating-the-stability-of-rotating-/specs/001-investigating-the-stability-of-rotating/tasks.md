# Tasks: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

**Input**: Design documents from `/specs/001-investigating-the-stability-of-rotating/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [ ] T001a Create `code/` directory structure: `code/`, `code/simulation`, `code/analysis`, `code/statistics`, `code/viz`, `code/utils`
- [ ] T001b Create `data/` directory structure: `data/raw`, `data/processed`, `data/aggregated`
- [ ] T001c Create `tests/` directory structure: `tests/unit`, `tests/contract`, `tests/integration`
- [X] T002 Create `code/requirements.txt` containing: numpy, scipy, matplotlib, pandas, pytest, numba, ruff, black
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup `data/` directory structure: `raw/`, `processed/`, `aggregated/` (Note: This duplicates T001b, but kept for explicit Phase 2 grouping per plan)
- [X] T005 [P] Implement deterministic random seed management utility in `code/utils/seed_manager.py`
- [X] T006 [P] Setup file-based I/O helpers for `.npy` and `.csv` in `code/utils/io_helpers.py`
- [X] T007 [P] Create base `SimulationRun` and `StabilityMetric` dataclasses in `code/models/entities.py` (Note: StabilityMetric must use `vortex_density` per spec FR-004)
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [X] T009 Setup environment configuration management for grid parameters in `code/config/grid_config.py`
- [X] T013b [P] [US1] Implement adaptive/fixed time-step logic and stability criteria check in `code/simulation/gpe_solver.py` (FR-001). This task defines the time-stepping rules used by the solver in T013a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Stability Phase Diagram (Priority: P1) 🎯 MVP

**Goal**: Run the time-dependent GPE solver across the parameter grid to generate raw simulation data.

**Independent Test**: Can be fully tested by executing the simulation script for a single parameter set (e.g., Ω=0.5, ε_dd=0.5, N=10^4) and verifying that it completes within the CI limit without GPU errors, producing density and phase snapshot files.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test `tests/unit/test_gpe_solver.py::test_split_step_preserves_norm` for split-step Fourier stability
- [X] T011 [P] [US1] Integration test `tests/integration/test_single_run.py::test_single_run_completes` for single run completion

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement Thomas-Fermi initial condition generator in `code/simulation/initial_conditions.py` (FR-002)
- [X] T013a [US1] Implement split-step Fourier GPE solver with dipolar term in `code/simulation/gpe_solver.py` (FR-001). Must implement conditional grid size: 64x64 if RUN_FULL_GRID=true (full scan), else 256x256 (verification). (Depends on T013b).
- [X] T014 [US1] Implement batch runner to iterate over (Ω, ε_dd, N) grid in `code/simulation/runner.py` (US-1) ensuring N ∈ {small, intermediate, large}, Ω ∈ [, 0.9], ε_dd ∈ {0.0, 0.5, 1.0, 1.5}.
- [X] T015 [US1] Add logic to handle numerical instability crashes (log failure, set status=unstable, vortex_density=0) in `code/simulation/runner.py`
- [X] T016 [US1] Add logging for simulation steps and resource usage in `code/simulation/runner.py`
- [X] T017 [US1] Create verification script `code/simulation/verify_performance.py` to run 256x256 (subset) and 64x64 (full grid) and log peak memory usage to validate memory limit assumption (substantial capacity) and runtime constraint (a fixed time limit). Must verify runtime < 6h and memory < 14 GB (SC-001).
- [X] T017a [P] [US1] Update spec.md performance assumptions to formally document the 64x64 full scan vs 256x256 verification deviation and the performance validation results. (Depends on T017).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Detect Vortices and Calculate Stability Metrics (Priority: P2)

**Goal**: Automatically detect vortex positions via phase winding and calculate stability metrics (vortex density, radial variance, structure factor).

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated "stable" and "unstable" snapshot file and verifying that it correctly counts vortices and outputs the three defined metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `tests/unit/test_vortex_detector.py::test_phase_winding_detects_single_vortex` on synthetic vortex data
- [X] T019 [P] [US2] Contract test `tests/contract/test_metrics_schema.py::test_metrics_schema` for metrics output schema

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement phase-winding vortex detection algorithm in `code/analysis/vortex_detector.py` (FR-003, handle vortex-antivortex pairs)
- [X] T021 [US2] Implement stability metric calculation: Vortex Density, Radial Variance, Structure Factor Sharpness in `code/analysis/metrics.py` (FR-004). (Depends on T007 and output artifacts from T013a/T014).
- [ ] T024 [US2] Implement logic for Metastability Boundary: classify as metastable if condensate density drops > 30% OR if vortex density exceeds specific threshold. Explicitly calculate/report variation in false-positive/negative rates. (FR-006, SC-002).
- [X] T023 [US2] Integrate vortex detection and metric calculation into a processing pipeline in `code/analysis/pipeline.py`
- [X] T025 [P] [US2] Create unit test `tests/unit/test_edge_cases.py::test_zero_initial_vortices` for edge cases (zero initial vortices, annihilation events)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Statistical Phase Maps and Visualizations (Priority: P3)

**Goal**: Aggregate results from repeated simulations, perform Two-Way ANOVA, and generate contour maps.

**Independent Test**: Can be fully tested by running the visualization script on a mock dataset of repeats per point and verifying that it produces a contour map distinguishing stable/unstable regions and a summary table of ANOVA p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test `tests/unit/test_statistics.py::test_two_way_anova` for Two-Way ANOVA calculation
- [X] T027 [P] [US3] Integration test `tests/integration/test_aggregation.py::test_full_aggregation_pipeline` for full aggregation pipeline

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement data aggregation logic (multiple repeats per point) in `code/statistics/aggregators.py`
- [X] T029 [US3] Implement Two-Way ANOVA (Ω × ε_dd) and Dunnett's post-hoc test in `code/statistics/aggregators.py`. Note: This follows the Plan's correction to FR-005. The original Spec FR-005 mandated an invalid One-Sample t-test which is being superseded by this Two-Way ANOVA approach. (Depends on T028).
- [X] T030 [US3] Implement statistical significance flagging (α=0.05) against null hypothesis in `code/statistics/aggregators.py`. Must format and output P-values with at least 4 decimal places (SC-003).
- [X] T031 [US3] Implement 3D parameter space contour map generation (Ω vs ε_dd vs Stability) in `code/viz/plotter.py`
- [X] T032 [US3] Generate representative density/phase plots for stable, metastable, and unstable regimes in `code/viz/plotter.py`
- [X] T033 [US3] Create summary table of ANOVA p-values and export to `data/aggregated/` in `code/viz/reporter.py`
- [X] T034 [P] [US3] Validate that the statistical design handles the "zero initial vortex" case without division errors in `tests/unit/test_zero_vortex_stats.py::test_no_division_by_zero`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Documentation: Update `README.md` with specific usage examples, parameter descriptions, and installation instructions.
- [ ] T035b [P] Documentation: Add comprehensive docstrings (numpy style) to all public functions and classes in `code/`.
- [ ] T035c [P] Documentation: Generate API documentation in `docs/` using Sphinx or similar tool based on the docstrings.
- [ ] T036a [P] Refactor `gpe_solver.py` to reduce cyclomatic complexity to a lower, maintainable level.
- [ ] T036b [P] Refactor `runner.py` for readability and maintainability.
- [ ] T037 [P] Performance optimization: ensure full grid (300 runs) completes in ≤6 hours on GitHub Actions runner and memory usage does not exceed 14 GB (SC-001). Optimize `gpe_solver.py` with Numba and add CI benchmark script that fails if runtime > 6h OR memory > 14 GB.
- [ ] T038 [P] Additional unit tests for numerical convergence in `tests/unit/test_convergence.py::test_convergence_rate`
- [ ] T039a [P] Security hardening: Validate grid parameters in `grid_config.py` (reject negative, enforce a maximum limit).
- [ ] T039b [P] Security hardening: Validate N, Ω, ε_dd bounds in `runner.py`.
- [ ] T040 Run quickstart.md validation and end-to-end CI check
- [ ] T041 [P] [Review] Update `spec.md` Section 5 (Assumptions) to explicitly state that the 64x64 grid is sufficient for the full parameter scan and that 256x256 is reserved for verification, referencing T017 results.
- [ ] T042 [P] [Review] Add a `data-model.md` file in `specs/001-investigating-the-stability-of-rotating/` defining the exact JSON schema for `SimulationRun` and `StabilityMetric` to ensure contract tests (T019) have a source of truth.
- [ ] T043 [P] [Review] Implement a `quickstart.md` in `specs/001-investigating-the-stability-of-rotating/` with a single-command example to run the full 64x64 grid scan and generate the phase diagram.
- [ ] T044 [P] [Review] Create a `contracts/` directory in `specs/001-investigating-the-stability-of-rotating/` containing YAML schemas for `SimulationRun` and `StabilityMetric` to support T019.
- [ ] T045 [P] [Review] Add a `research.md` file in `specs/001-investigating-the-stability-of-rotating/` documenting the theoretical background for the dipolar GPE, Thomas-Fermi approximation, and the justification for Two-Way ANOVA over One-Way ANOVA.
- [ ] T046 [P] [Review] Refactor `code/simulation/runner.py` to ensure that any numerical instability (crash) results in a `status=unstable` and `vortex_density=0` entry in the metrics CSV, and that the pipeline continues without raising an exception (as per SC-001).
- [ ] T047 [P] [Review] Add a `test_zero_vortex_stats.py` unit test in `tests/unit/` to verify that the Two-Way ANOVA implementation handles cases where all repeats for a parameter set result in zero initial vortices without raising division-by-zero errors.