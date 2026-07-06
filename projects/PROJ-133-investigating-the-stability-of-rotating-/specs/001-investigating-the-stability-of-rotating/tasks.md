# Tasks: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-133-investigating-the-stability-of-rotating-/` using: `mkdir -p code/{simulation,analysis,statistics,viz,utils} data/{raw,processed,aggregated} tests/{unit,contract,integration} docs`
- [X] T002 Create `code/requirements.txt` containing: numpy, scipy, matplotlib, pandas, pytest, numba, ruff, black
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/` directory structure: `raw/`, `processed/`, `aggregated/`
- [ ] T005 [P] Implement deterministic random seed management utility in `code/utils/seed_manager.py`
- [X] T006 [P] Setup file-based I/O helpers for `.npy` and `.csv` in `code/utils/io_helpers.py`
- [~] T007 [P] Create base `SimulationRun` and `StabilityMetric` dataclasses in `code/models/entities.py` (Note: StabilityMetric must use `vortex_density` per amended spec FR-004 from T021b)
- [~] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [~] T009 Setup environment configuration management for grid parameters in `code/config/grid_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Stability Phase Diagram (Priority: P1) 🎯 MVP

**Goal**: Run the time-dependent GPE solver across the parameter grid to generate raw simulation data.

**Independent Test**: Can be fully tested by executing the simulation script for a single parameter set (e.g., Ω=0.5, ε_dd=0.5, N=10^4) and verifying that it completes within the CI limit without GPU errors, producing density and phase snapshot files.

### Spec Amendment: Grid Resolution (Pre-requisite for Implementation)

- [~] T017b [P] [US1] **SPEC AMENDMENT**: Update `spec.md` FR-001 to replace "256x256 grid" with "256x256 grid for verification, 64x64 grid for full batch scan (conditional on RUN_FULL_GRID=true)". Update Assumptions to reflect 64x64 feasibility. (Pre-requisite for T013).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test `tests/unit/test_gpe_solver.py::test_split_step_preserves_norm` for split-step Fourier stability
- [~] T011 [P] [US1] Integration test `tests/integration/test_single_run.py::test_single_run_completes` for single run completion

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement Thomas-Fermi initial condition generator in `code/simulation/initial_conditions.py` (FR-002)
- [~] T013 [US1] Implement split-step Fourier GPE solver with dipolar term in `code/simulation/gpe_solver.py` (FR-001) with conditional grid size: 64x64 if RUN_FULL_GRID=true (default), else 256x256. (Depends on T017b).
- [ ] T014 [US1] Implement batch runner to iterate over (Ω, ε_dd, N) grid in `code/simulation/runner.py` (US-1) ensuring N ∈ {small, intermediate, large}, Ω ∈ [lower bound, 0.9], ε_dd ∈ {, 0.5, 1.0, 1.5}.
- [ ] T015 [US1] Add logic to handle numerical instability crashes (log failure, set retention=0) in `code/simulation/runner.py`
- [ ] T016 [US1] Add logging for simulation steps and resource usage in `code/simulation/runner.py`
- [ ] T017 [P] [US1] Create verification script `code/simulation/verify_performance.py` to run 256x256 (subset) and 64x64 (full grid) and log peak memory usage to validate memory limit assumption and runtime constraint.
- [ ] T017a [P] [US1] Update spec.md performance assumptions to formally document the 64x64 full scan vs 256x256 verification deviation and the performance validation results. (Parallel to T017b).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Detect Vortices and Calculate Stability Metrics (Priority: P2)

**Goal**: Automatically detect vortex positions via phase winding and calculate stability metrics (vortex density, radial variance, structure factor).

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated "stable" and "unstable" snapshot file and verifying that it correctly counts vortices and outputs the three defined metrics.

### Spec Amendment: Metric Definition (Pre-requisite for Implementation)

- [ ] T021b [P] [US2] **SPEC AMENDMENT**: Update `spec.md` FR-004 to replace "vortex-number retention fraction" with "vortex density (vortices/area)". Update SC-001 and SC-002 to reference "vortex density" instead of "retention fraction". (Pre-requisite for T007, T021).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `tests/unit/test_vortex_detector.py::test_phase_winding_detects_single_vortex` on synthetic vortex data
- [ ] T019 [P] [US2] Contract test `tests/contract/test_metrics_schema.py::test_metrics_schema` for metrics output schema

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement phase-winding vortex detection algorithm in `code/analysis/vortex_detector.py` (FR-003, handle vortex-antivortex pairs)
- [ ] T021 [US2] Implement stability metric calculation: Vortex Density, Radial Variance, Structure Factor Sharpness in `code/analysis/metrics.py` (FR-004). (Depends on T021b).
- [ ] T022 [US2] Implement sensitivity analysis sweep for instability threshold over the EXACT discrete values {, 0.30, 0.35} in `code/analysis/metrics.py` (FR-006, SC-005) and explicitly calculate/report variation in false-positive/negative rates.
- [ ] T023 [US2] Integrate vortex detection and metric calculation into a processing pipeline in `code/analysis/pipeline.py`
- [ ] T024 [US2] Add logic to handle metastable boundary (drop >30%) as binary threshold while recording exact percentage in `code/analysis/metrics.py`
- [ ] T025 [P] [US2] Create unit test `tests/unit/test_edge_cases.py::test_zero_initial_vortices` for edge cases (zero initial vortices, annihilation events)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Statistical Phase Maps and Visualizations (Priority: P3)

**Goal**: Aggregate results from repeated simulations, perform Two-Way ANOVA, and generate contour maps.

**Independent Test**: Can be fully tested by running the visualization script on a mock dataset of repeats per point and verifying that it produces a contour map distinguishing stable/unstable regions and a summary table of ANOVA p-values.

### Spec Amendment: Statistical Method (Pre-requisite for Implementation)

- [ ] T029b [P] [US3] **SPEC AMENDMENT**: Update `spec.md` FR-005 to replace "one-sample t-test" and "one-way ANOVA" with "Two-Way ANOVA (Ω × ε_dd)" and "Dunnett's post-hoc test". Update SC-003 to reference the corrected statistical method. (Pre-requisite for T029).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test `tests/unit/test_statistics.py::test_two_way_anova` for Two-Way ANOVA calculation
- [ ] T027 [P] [US3] Integration test `tests/integration/test_aggregation.py::test_full_aggregation_pipeline` for full aggregation pipeline

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement data aggregation logic (multiple repeats per point) in `code/statistics/aggregators.py`
- [ ] T029 [US3] Implement Two-Way ANOVA (Ω × ε_dd) and Dunnett's post-hoc test in `code/statistics/aggregators.py` (Per Plan correction to FR-005). (Depends on T029b).
- [ ] T030 [US3] Implement statistical significance flagging (α=0.05) against null hypothesis in `code/statistics/aggregators.py`
- [ ] T031 [US3] Implement 3D parameter space contour map generation (Ω vs ε_dd vs Stability) in `code/viz/plotter.py`
- [ ] T032 [US3] Generate representative density/phase plots for stable, metastable, and unstable regimes in `code/viz/plotter.py`
- [ ] T033 [US3] Create summary table of ANOVA p-values and export to `data/aggregated/` in `code/viz/reporter.py`
- [ ] T034 [P] [US3] Validate that the statistical design handles the "zero initial vortex" case without division errors in `tests/unit/test_zero_vortex_stats.py::test_no_division_by_zero`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Documentation: Update `README.md` with specific usage examples, parameter descriptions, and installation instructions.
- [ ] T035b [P] Documentation: Add comprehensive docstrings (numpy style) to all public functions and classes in `code/`.
- [ ] T035c [P] Documentation: Generate API documentation in `docs/` using Sphinx or similar tool based on the docstrings.
- [ ] T036 Code cleanup and refactoring for readability
- [ ] T037 Performance optimization: ensure full grid (300 runs) completes in ≤6 hours on GitHub Actions 2-core runner (optimize `gpe_solver.py` with Numba) and add CI benchmark script that fails if runtime > 6h
- [ ] T038 [P] Additional unit tests for numerical convergence in `tests/unit/test_convergence.py::test_convergence_rate`
- [ ] T039 Security hardening (input validation for grid parameters)
- [ ] T040 Run quickstart.md validation and end-to-end CI check

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (snapshots)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (metrics)

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for split-step Fourier stability in tests/unit/test_gpe_solver.py::test_split_step_preserves_norm"
Task: "Integration test for single run completion in tests/integration/test_single_run.py::test_single_run_completes"

# Launch all models for User Story 1 together:
Task: "Implement Thomas-Fermi initial condition generator in code/simulation/initial_conditions.py"
Task: "Implement split-step Fourier GPE solver in code/simulation/gpe_solver.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T017b amendment first)
4. **STOP and VALIDATE**: Test User Story 1 independently (single run on 256x256, full grid on 64x64)
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
 - Developer A: User Story 1 (GPE Solver) - Starts after T017b
 - Developer B: User Story 2 (Vortex Detection) - Starts after T021b
 - Developer C: User Story 3 (Statistics & Viz) - Starts after T029b
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
- **Critical Correction**: The implementation uses **Two-Way ANOVA** and **Vortex Density** (T029, T021) instead of the Spec's invalid One-Way ANOVA and Retention Fraction (FR-005), as mandated by the Plan's Spec-Plan Alignment Gap. Amendment tasks T017b, T021b, and T029b update the spec to reflect this BEFORE implementation proceeds.