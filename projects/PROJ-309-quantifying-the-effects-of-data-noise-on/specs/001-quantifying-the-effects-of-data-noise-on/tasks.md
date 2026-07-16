# Tasks: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

**Input**: Design documents from `/specs/001-quantifying-the-effects-of-data-noise-on/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001a [P] Create projects/PROJ-309-quantifying-the-effects-of-data-noise-on/code/ directory at repository root
- [X] T001b [P] Create projects/PROJ-309-quantifying-the-effects-of-data-noise-on/data/raw, projects/PROJ-309-quantifying-the-effects-of-data-noise-on/data/processed, projects/PROJ-309-quantifying-the-effects-of-data-noise-on/data/results directories with `.gitkeep`
- [X] T001c [P] Create projects/PROJ-309-quantifying-the-effects-of-data-noise-on/tests/unit, projects/PROJ-309-quantifying-the-effects-of-data-noise-on/tests/contract, projects/PROJ-309-quantifying-the-effects-of-data-noise-on/tests/integration directories
- [X] T001d [P] Create projects/PROJ-309-quantifying-the-effects-of-data-noise-on/logs/ directory with `.gitkeep`

- [X] T002a [P] Create requirements.txt with pinned Python dependencies (numpy, scipy, pandas, matplotlib, pytest)
- [X] T002b [P] Create pyproject.toml with project metadata and entry points

- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note on Parallel Scaffolding**: Tasks T004-T009 are marked [P] for parallel execution regarding file creation. HOWEVER, Phase 2b (Tasks T039-T044) which implements logic **MUST WAIT** until Phase 2a (T004-T009) has successfully created the files. The [P] tag applies only to the file-creation step, not the logic implementation step. **Parallel file creation only; logic implementation requires sequential verification of shared config**.

### Phase 2a: Scaffolding & Signatures

- [X] T004 [P] Create code/config.py with function signatures and docstrings for constants: SNR levels, system params, seeds, noise type enums (Gaussian, Uniform Quantization).
- [X] T005 [P] Create code/generators.py with function signatures and docstrings for Lorenz/Rössler integration (FR-001).
- [X] T006 [P] Create code/noise.py with function signatures and docstrings for Gaussian/Quantization injection (FR-002, FR-003).
- [X] T007 [P] Create code/metrics.py with function signatures and docstrings for GP, Rosenstein, FNN (FR-004, FR-005, FR-006).
- [X] T008 [P] Create code/analysis.py with function signatures and docstrings for error calc, threshold ID (FR-007, FR-008).
- [X] T009 [P] Create code/visualize.py with function signatures and docstrings for plotting, CSV export (FR-009, FR-010).

### Phase 2b: Core Logic Implementation

- [X] T039 [P] Implement code/config.py constants and enums (SNR levels, system params, seeds, noise types).
- [X] T040 [P] Implement code/generators.py logic for Lorenz/Rössler integration (FR-001).
- [X] T041 [P] Implement code/noise.py logic for Gaussian/Quantization injection (FR-002, FR-003).
- [X] T042 [P] Implement code/metrics.py logic for GP, Rosenstein, FNN (FR-004, FR-005, FR-006).
- [X] T043 [P] Implement code/analysis.py logic for error calc, threshold ID (FR-007, FR-008).
- [X] T044 [P] Implement code/visualize.py logic for plotting, CSV export (FR-009, FR-010).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Clean Chaotic Time-Series Data (Priority: P1) 🎯 MVP

**Goal**: Obtain ground-truth chaotic time-series data from canonical systems (Lorenz, Rössler) with known parameters.

**Independent Test**: Generate a Lorenz attractor trajectory, compute its correlation dimension and Lyapunov exponent using the defined algorithms, and verify the results are stable (within ±1% across two independent runs of the same trajectory generation).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for trajectory schema in tests/contract/test_trajectory.py
- [X] T011 [P] [US1] Integration test for reproducibility (seed stability) in tests/integration/test_reproducibility.py

### Implementation for User Story 1

- [X] T012 [US1] Implement Lorenz attractor integration in code/generators.py using scipy.integrate.solve_ivp with standard parameters (σ=10, ρ=28, β=8/3 (Wikipedia: Lorenz system, https://en.wikipedia.org/wiki/Lorenz_system))
- [X] T013 [US1] Implement Rössler attractor integration in code/generators.py with standard parameters
- [X] T014 [US1] Implement trajectory validation (NaN check, minimum length threshold) in code/generators.py
- [X] T015 [US1] Add logging for integration overflow warnings and trajectory generation metadata: Log at WARNING level to logs/pipeline.log with message format "Integration overflow at time step [t]" when NaN/Inf detected.
- [X] T016 [US1] Write clean trajectories to data/raw/ with naming convention {system_type}_clean_{seed}.csv and sidecar checksum file using SHA-256 algorithm (extension.sha256).
- [X] T017 [US1] **Compute Ground Truth Metrics**: Implement logic in code/metrics.py to compute Correlation Dimension and Lyapunov Exponent for clean trajectories generated in T012/T013. Store results in data/processed/ground_truth_metrics_{seed}.json to serve as the reference for error calculation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Inject Controlled Noise at Specified SNR Levels (Priority: P1)

**Goal**: Apply additive Gaussian noise and uniform quantization noise to clean trajectories across a defined SNR range.

**Independent Test**: Inject Gaussian noise at a moderate SNR into a signal and verify the measured SNR (computed as 10·log₁₀(P_signal/P_noise)) matches the target within ±0.5dB. Additionally, verify that the injected noise causes a measurable divergence in nearby trajectories compared to the clean baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for noisy trajectory schema in tests/contract/test_noisy_trajectory.py
- [X] T019 [P] [US2] Unit test for SNR calculation accuracy in tests/unit/test_noise.py
- [X] T022b [P] [US2] Verify SNR Accuracy: Implement a unit test in tests/unit/test_noise.py that injects noise at a target SNR and asserts the measured SNR error is ≤0.5dB (FR-002).

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement Gaussian noise injection in code/noise.py with target SNR accuracy ±0.5dB (See US-2 Acceptance Scenario 1: Negative to positive decibel levels in fixed increments. per FR-002)
- [X] T021 [US2] Implement uniform quantization noise injection in code/noise.py with user-specified bit resolution (FR-003). For quantization, expose a CLI argument or config parameter to accept user-specified bit resolutions.
- [X] T022 [US2] Implement SNR verification logic (calculate actual SNR post-injection) in code/noise.py
- [X] T023 [US2] Add error handling for unsupported noise types: Raise ValueError with exact message "Unsupported noise type: [type]. Supported: Gaussian, uniform quantization" (See Edge Cases). Inside the inject_noise function in code/noise.py.
- [X] T024 [US2] Write noisy trajectories to data/processed/ with metadata in sidecar JSON file manifest_{system_type}.json containing keys: snr, noise_type, seed, checksum, system_type.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Phase Space Reconstruction Metrics and Compare Against Ground Truth (Priority: P2)

**Goal**: Calculate correlation dimension, Lyapunov exponents, and false nearest neighbors for each noisy trajectory, then compute error rates relative to clean-data ground truth.

**Independent Test**: Run the pipeline on data at a specified signal-to-noise ratio and verify Lyapunov exponent error is ≤10% of ground truth at high SNR, while low SNR data shows error ≥50%.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for metric results schema in tests/contract/test_metrics.py
- [X] T026 [P] [US3] Unit test for Grassberger-Procaccia algorithm correctness on known synthetic data in tests/unit/test_metrics.py

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement Correlation Dimension (Grassberger-Procaccia) in code/metrics.py with embedding dimension search
- [X] T028 [US3] Implement Largest Lyapunov Exponent (Rosenstein's algorithm) in code/metrics.py with convergence checks
- [X] T029 [US3] Implement False Nearest Neighbors (FNN) in code/metrics.py (embedding=2, threshold=10× std)
- [X] T030 [US3] **Implement Error Calculation**: Implement logic in code/analysis.py to calculate absolute error for each metric as |computed_value - ground_truth_value| / |ground_truth_value| × 100. The ground_truth_value MUST be sourced from the metrics computed in Task T017 (Clean Trajectory Metrics). (See FR-007)
- [X] T031 [US3] **Identify Critical Threshold**: Implement logic to identify critical SNR threshold where FNN rate exceeds % (0.5). Algorithm: Iterate SNR levels from low to high using the list defined in code/config.py, spanning a range that includes very low signal-to-noise conditions.; find the lowest SNR where FNN rate > 0.5. Store result in data/processed/critical_threshold.json. (See FR-008, SC-003).
- [X] T032 [US3] Write metric results and error tables to data/processed/ as metrics_summary.csv

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Generate Error-vs-SNR Lookup Table and Visualization (Priority: P3)

**Goal**: Produce a lookup table showing metric error rates across SNR levels, plus plots illustrating the critical threshold where reconstruction quality degrades.

**Independent Test**: Generate the lookup table and verify it contains ≥6 SNR levels (0, 5, 10, 15, 20, 25, 30dB) with corresponding error rates for all three metrics.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US4] Integration test for CSV export format in tests/integration/test_export.py

### Implementation for User Story 4

- [X] T034 [P] [US4] Implement CSV export logic (columns: SNR_dB, noise_type, metric_name, computed_value, ground_truth_value, error_percent) in code/visualize.py
- [X] T035 [US4] Implement line plot generation with critical threshold marker (at the 50% FNN point) in code/visualize.py
- [X] T037 [US4] Add timing logic to verify pipeline completes within 2-hour CPU budget (FR-010): Measure total runtime in code/main.py. Write result to data/results/runtime.json with keys: total_seconds (float), passed_2h_limit (boolean).
- [X] T038 [US4] Write final results and plots to data/results/ including error_vs_snr.png, final_lookup.csv, and critical_threshold_report.json. The critical_threshold_report.json MUST contain keys: threshold_snr (float), metric_name (string), error_percent (float), fnn_rate (float).

---

## Phase 7: Integration & Orchestration

**Purpose**: End-to-end pipeline orchestration and verification

- [X] T036 [P] [Integration] Implement pipeline orchestration in code/main.py to run generation → noise → metrics → analysis → export. This task depends on the completion of US1, US2, and US3 logic.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - Phase 2a (Scaffolding) must complete before Phase 2b (Logic)
 - Phase 2b (Logic) must complete before User Story implementation
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, and US3 completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: **Must run AFTER US1 AND US2 complete** - Requires clean data (US1) and noisy data (US2) to compute error rates (FR-007). Specifically, T030 (Error Calculation) requires the ground truth metrics produced in **Task T017** (US1). T031 (Critical Threshold) requires results from T027-T029 and T030.
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US3 results
- **Phase 7 (Integration)**: Depends on US1 (Data Generation), US2 (Noise Injection), and US3 (Metrics Implementation). T036 requires all previous logic to be functional.
- **Within Each User Story**:
 - Tests (if included) MUST be written and FAIL before implementation
 - Models before services
 - Services before endpoints
 - Core implementation before integration
 - Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Phase 2a tasks marked [P] can run in parallel (Scaffolding)
- All Phase 2b tasks marked [P] can run in parallel (Logic Implementation) **ONLY IF** Phase 2a is complete
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) - **Note: US3 must wait for US1/US2 data artifacts to exist before execution**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 7 (Integration) can run in parallel with US4 (Visualization) once US3 metrics are ready.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for trajectory schema in tests/contract/test_trajectory.py"
Task: "Integration test for reproducibility in tests/integration/test_reproducibility.py"

# Launch all models for User Story 1 together:
Task: "Implement Lorenz attractor integration in code/generators.py"
Task: "Implement Rössler attractor integration in code/generators.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - Complete Phase 2a (Scaffolding)
 - Complete Phase 2b (Logic)
3. Complete Phase 3: User Story 1 (including T017 for Ground Truth Metrics)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add Integration & Orchestration (Phase 7) → Test end-to-end pipeline
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Phase 2a together
2. Team completes Phase 2b together
3. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 (Must wait for US1/US2 data artifacts, specifically T017 output)
 - Developer D: User Story 4 (Can start early with scaffolding)
 - Developer E: Integration & Orchestration (Can start scaffolding, full execution waits for US3 metrics)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Execution Order**: US3 (Metrics) must wait for US1 (Clean Data) and US2 (Noisy Data) to complete and produce artifacts. Specifically, T030 requires the ground truth metrics from T017. T031 requires T030.
- **Removed Scope**: Phase 7 (Cellular Automata) has been **REMOVED** to align with spec.md which restricts the domain to "canonical chaotic systems like the Lorenz attractor" and "Rössler" only. The project now focuses solely on Lorenz and Rössler systems.
- **Phase 2 Refinement**: Phase 2 is now split into 2a (Signatures) and 2b (Logic) to ensure every task is an executable unit of work, resolving concerns about task granularity. Dependency clarification added: 2a must complete before 2b logic implementation.
- **Phase 6/7 Reorganization**: Pipeline orchestration (T036) has been moved to a dedicated "Phase 7: Integration & Orchestration" to ensure it logically follows the completion of US1, US2, and US3.
- **Reviewer Addressed**: The removal of Cellular Automata tasks directly addresses the "Prior research-stage reviews" concern regarding scope creep and constitutional violations (Principle VII).
