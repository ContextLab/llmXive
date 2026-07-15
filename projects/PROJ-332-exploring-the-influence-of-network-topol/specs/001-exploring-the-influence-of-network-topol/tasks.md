# Tasks: Influence of Network Topology on Thermal Conductivity in Nanomaterials

**Input**: Design documents from `/specs/001-network-topology-thermal/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan by executing: `mkdir -p code data/raw data/processed tests/unit tests/contract tests/integration specs/001-network-topology-thermal/contracts`
- [X] T001a [P] Initialize state directory and file: `mkdir -p state/projects` and create `state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml` with initial empty artifact_hashes map and `updated_at` timestamp.
- [X] T002 Initialize a Python project with dependencies in `projects/PROJ-332-exploring-the-influence-of-network-topol/code/requirements.txt`. The file MUST contain exactly:
 ```
 networkx==3.2.1 [UNRESOLVED-CLAIM: c_c314b052 — status=not_enough_info]
 scipy==1.13.1 [UNRESOLVED-CLAIM: c_cd5aabf5 — status=not_enough_info]
 numpy==1.26.4 [UNRESOLVED-CLAIM: c_ac07d587 — status=not_enough_info]
 pandas==2.2.2 [UNRESOLVED-CLAIM: c_0d4070f9 — status=not_enough_info]
 pyyaml==6.0.1 [UNRESOLVED-CLAIM: c_429b5584 — status=not_enough_info]
 pytest==8.2.2 [UNRESOLVED-CLAIM: c_77a1880f — status=not_enough_info]
 statsmodels==0.14.2 [UNRESOLVED-CLAIM: c_022d91dd — status=not_enough_info]
 ```
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`. Ensures code quality for FR-009 (Reproducibility) and SC-005 (Runtime/Quality).

### Phase 1.5: Linting Specifics (Split from T003)

- [X] T003a [P] Create `code/.pre-commit-config.yaml` with hooks for black and ruff.
- [X] T003b [P] Create `code/ruff.toml` with specific rules: E402, F401, W293, and enforce double quotes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/material_db.py` with NIST defaults are Si=149, CNT=3500, Ag=429, Au=318 W/(m·K). [UNRESOLVED-CLAIM: c_0368ef5b — status=not_enough_info] and validation logic per FR-010. MUST include explicit logic to raise a clear error with message "Material <material> not found in local store or NIST defaults; please provide value in W/(m·K)." for non-standard materials.
- [X] T004a [P] Create `specs/001-network-topology-thermal/contracts/simulation_result.schema.yaml` defining the exact JSON/YAML schema for the CSV output (columns: seed, N, p, avg_degree, conductivity, percolation_flag, scaling_factor). This file is required for T021.
- [X] T005 [P] Create `code/config.py` to load environment variables for simulation parameters (N, p, d, l, seed)
- [X] T006 [P] Implement `code/utils.py` with helper functions for logging, CSV writing, and error formatting
- [X] T007 Setup `data/` directory structure (`data/raw/`, `data/processed/`) and `.gitkeep` files
- [X] T007a [P] Initialize `data/processed/simulation_results.csv` with the header row matching the schema defined in T004a. This file must exist before T015, T029, or T035 run.
- [X] T008 Configure `pytest` in `code/pytest.ini` and create base test fixtures in `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Topology‑Specific Nanowire Networks (Priority: P1) 🎯 MVP

**Goal**: Create synthetic nanowire network graphs with prescribed average node degree and compute effective thermal conductivity.

**Independent Test**: Run the generator for a single target degree (e.g., 4) and The produced graph's The produced graph's measured average degree is within ±5 % of the target and that an effective conductivity value is produced.

### Implementation for User Story 1

- [X] T009 [US1] Implement graph generation function in `code/generate_networks.py` using NetworkX with user-specified node count N, connection probability p, and target average degree (FR-001).
- [X] T009a [US1] Implement node/edge generation logic in `code/generate_networks.py` (FR-001).
- [X] T009b [US1] Implement target degree validation logic in `code/generate_networks.py` to ensure target degree is within valid bounds (FR-001).
- [X] T010 [US1] Implement degree and connection validation logic in `code/generate_networks.py` to ensure target degree is within valid bounds (FR-001).
- [X] T011 [US1] Implement thermal resistance assignment in `code/thermal_solver.py` based on material bulk conductivity and geometry (FR-002).
- [X] T012 [US1] Implement Fuchs-Sondheimer size-correction factor logic in `code/thermal_solver.py` with explicit conditional check for wire diameter d < 100nm as required by FR-011 (FR-011). **Formula**: `{{claim:c_71f76ac4}}`. Use default `lambda=10nm`, `p=0.5` if not specified.
- [X] T013 [US1] Implement Kirchhoff heat-flow solver in `code/thermal_solver.py` using SciPy sparse linear algebra with Implement Kirchhoff heat-flow solver... with residual ≤ 1e-6 [UNRESOLVED-CLAIM: c_c7485144 — status=not_enough_info], including logic to detect disconnected graphs and return zero conductivity while logging "Graph disconnected; conductivity set to 0.0" (FR-003, Edge Cases).
- [X] T014 [US1] Implement zero-resistance clamping logic in `code/thermal_solver.py` to prevent division-by-zero errors (Edge Cases).
- [X] T015 [US1] Implement logging and CSV output generation in `code/main.py` to record all parameters and results (FR-009). **Depends on T007a**.
- [X] T016 [US1] Implement runtime timeout check in `code/main.py` to Runtime timeout check aborts if > 6 hours [UNRESOLVED-CLAIM: c_3f8f5677 — status=not_enough_info] (FR-008). **Split into T016a and T016b**.
- [X] T016a [US1] Implement Global Timer Wrapper in `code/main.py`: Use `time.time()` to measure elapsed time from project start. Check this value at the start of every simulation iteration in the grid loop. If `elapsed > 6 hours`, trigger abort.
- [X] T016b [US1] Implement Abort Logic in `code/main.py`: If timer check fails, execute `sys.exit(1)` with message "Runtime ceiling (6h) exceeded. Aborting grid." (FR-008).

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T017 [P] [US1] Unit test for graph generation accuracy in `tests/unit/test_network_gen.py::test_avg_degree_within_tolerance` (verify degree within ±5% [UNRESOLVED-CLAIM: c_375943ec — status=not_enough_info])
- [X] T018 [P] [US1] Unit test for material property fallback in `tests/unit/test_materials.py::test_nist_defaults_trigger` (verify NIST defaults trigger correctly)
- [X] T019 [P] [US1] Unit test for disconnected graph handling in `tests/unit/test_solver.py::test_disconnected_graph_returns_zero` (verify 0.0 conductivity and warning log)
- [X] T020 [P] [US1] Unit test for zero-resistance clamping in `tests/unit/test_solver.py::test_zero_resistance_clamped` (verify minimum thermal resistance threshold)
- [X] T021 [P] [US1] Contract test for simulation result schema in `tests/contract/test_schemas.py::test_csv_output_matches_schema` (verify CSV output matches `simulation_result.schema.yaml` created in T004a). **Depends on T004a**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Scaling Between Topology and Conductivity (Priority: P2)

**Goal**: Fit scaling laws between graph metrics and conductivity, identify percolation threshold, and report statistical significance.

**Independent Test**: Execute the full pipeline on a small parameter grid and verify regression outputs include scaling exponents, confidence intervals, and p-values.

### Implementation for User Story 2

- [X] T022 [US2] Implement average degree calculation in `code/generate_networks.py` (FR-004).
- [X] T023 [US2] Implement average shortest-path length calculation in `code/generate_networks.py` (FR-004).
- [X] T024 [US2] Implement clustering coefficient calculation in `code/generate_networks.py` (FR-004).
- [X] T025 [US2] Implement OLS regression on log-transformed data in `code/regression_analysis.py` (FR-005).
- [X] T026 [US2] Implement correlation matrix calculation for all metrics in `code/regression_analysis.py` (FR-006).
- [X] T027 [US2] Implement percolation threshold detection logic (Percolation threshold detection logic (smallest avg degree where ≥80% connected [UNRESOLVED-CLAIM: c_2182d814 — status=not_enough_info])) in `code/regression_analysis.py` (SC-003).
- [X] T027a [US2] Implement explicit calculation and storage of the percolation threshold value (Percolation threshold detection logic (smallest avg degree where ≥80% connected [UNRESOLVED-CLAIM: c_2182d814 — status=not_enough_info])) into `data/processed/simulation_results.csv` as a new column `percolation_threshold`. This fulfills the "identify" requirement of SC-003. <!-- FAILED: unspecified -->
- [X] T028 [US2] Implement conditional reporting of statistically significant scaling exponent (p < 0.05) in `code/regression_analysis.py` when mean degree exceeds the calculated percolation threshold (from T027a), as required by SC-003 (SC-003). <!-- FAILED: unspecified -->
- [X] T029 [US2] Integrate regression results into `code/main.py` to append to `simulation_results.csv`. **Depends on T007a**.

### Tests for User Story 2 ⚠️

- [X] T030 [P] [US2] Unit test for regression analysis in `tests/unit/test_regression.py::test_regression_outputs` (verify exponent, CI, and p-value calculation)
- [X] T031 [P] [US2] Unit test for percolation threshold detection in `tests/unit/test_metrics.py::test_percolation_threshold_logic` (verify 80% connectivity cutoff logic)
- [X] T032 [P] [US2] Contract test for correlation matrix output in `tests/contract/test_schemas.py::test_correlation_matrix_schema`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Sensitivity & Robustness Checks (Priority: P3)

**Goal**: Assess sensitivity of conductivity estimates to resistor parameters and percolation cutoff.

**Independent Test**: Run sensitivity sweep over a range of values centered around the baseline and verify Reported variations in sensitivity analysis must stay within ±10% [UNRESOLVED-CLAIM: c_398da03e — status=not_enough_info]

### Implementation for User Story 3

- [X] T033 [US3] Implement sensitivity analysis module in `code/sensitivity_analysis.py` to sweep scaling factors across a range of values. (FR-007).
- [X] T034 [US3] Implement deviation calculation and reporting in `code/sensitivity_analysis.py` (SC-004).
- [X] T035 [US3] Integrate sensitivity results into `code/main.py` and update `simulation_results.csv` with sensitivity metrics. **Depends on T007a**.

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] Unit test for sensitivity analysis in `tests/unit/test_sensitivity.py::test_sensitivity_sweep` (verify ±10% deviation check)
- [ ] T037 [P] [US3] Unit test for missing material error in `tests/unit/test_materials.py::test_non_standard_material_error` (verify clear error for non-standard materials)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Implement `code/update_state.py` to calculate SHA-256 of `simulation_results.csv` and update `state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml` (Constitution Principle V). **Depends on T001a**.
- [ ] T039 [P] Run full integration test suite in `tests/integration/test_full_pipeline.py` covering all user stories.
- [ ] T040 Update `docs/quickstart.md` with instructions for running the default grid (sims x multiple levels).
- [ ] T041 Verify `tasks.md` and `plan.md` consistency against `spec.md` requirements.

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

- Implementation tasks MUST be completed before Test execution tasks
- Models/Helpers before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T003 which depends on T001)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for US1:
Task: "Implement graph generation function in code/generate_networks.py..."
Task: "Implement degree and connection validation logic..."
Task: "Implement thermal resistance assignment..."
Task: "Implement Fuchs-Sondheimer size-correction..."
Task: "Implement Kirchhoff heat-flow solver..."
Task: "Implement zero-resistance clamping..."
Task: "Implement logging and CSV output..."
Task: "Implement runtime timeout check..."

# Launch all test tasks for US1 (after implementation):
Task: "Unit test for graph generation accuracy in tests/unit/test_network_gen.py::test_avg_degree_within_tolerance"
Task: "Unit test for material property fallback in tests/unit/test_materials.py::test_nist_defaults_trigger"
Task: "Unit test for disconnected graph handling in tests/unit/test_solver.py::test_disconnected_graph_returns_zero"
Task: "Unit test for zero-resistance clamping in tests/unit/test_solver.py::test_zero_resistance_clamped"
Task: "Contract test for simulation result schema in tests/contract/test_schemas.py::test_csv_output_matches_schema"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Implementation T009-T016b, then Tests T017-T021)
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

- [P] tasks = different files, no dependencies (unless explicitly noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on a multi-core CPU configuration with sufficient memory, without GPU acceleration. Avoid large datasets or heavy models.
- **Dependencies**: T003 depends on T001. T007a, T004a are prerequisites for T015, T021, T029, T035. T001a is prerequisite for T038. T027a is prerequisite for T028.