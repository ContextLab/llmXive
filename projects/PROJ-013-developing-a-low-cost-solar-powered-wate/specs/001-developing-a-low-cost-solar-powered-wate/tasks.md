# Tasks: 001-solar-purification-tradeoff

**Input**: Design documents from `/specs/001-solar-purification-tradeoff/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/` directories)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scipy, numpy, pandas, matplotlib, requests, beautifulsoup4, pyyaml, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/plots/`)
- [X] T005 [P] Implement utility helpers for logging, error handling, and path resolution in `code/utils.py`
- [X] T006 Create base configuration loader for API keys and simulation parameters in `code/config.py`
- [ ] T007 Setup environment configuration management (`.env` support for NASA POWER keys)
- [X] T008 Implement `code/data_ingestion.py` helper: Fetch solar irradiance profiles from NASA POWER API for Sub-Saharan Africa; handle missing/zero data by defaulting to a representative average as per spec edge cases. **Prerequisite for T021.** (Blocking: Must complete before T021).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Cost Function Construction (Priority: P1) 🎯 MVP

**Goal**: Retrieve thermal properties from NIST (hardcoded for reproducibility) and scrape market prices to construct a deterministic cost function $C = \sum (mass_i \times price_i)$.

**Independent Test**: Run the data ingestion script and verify that `data/processed/materials.csv` contains a representative set of material-geometry combinations with non-null thermal properties and valid positive cost values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These tests verify specific function signatures and logic.

- [X] T009 [P] [US1] Unit test for cost function calculation in `tests/unit/test_data_ingestion.py`: Verify `calculate_cost` exists with signature `(materials: List[MaterialProfile], geometry: GeometryConfig) -> float` and asserts `calculate_cost` returns a float > 0 for valid inputs.
- [X] T010 [P] [US1] Contract test for material schema validation in `tests/unit/test_material_schema.py`: Verify `load_material_schema` exists with signature `(path: str) -> Schema` and asserts the schema loads correctly for the defined `MaterialProfile`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data_ingestion.py`: Load thermal properties (conductivity, emissivity, specific heat, density) for Aluminum, Copper, Black-painted Steel, and Plastic from the **hardcoded JSON file** `data/raw/nist_materials.json`. Ensure keys match `data-model.md` (MaterialProfile): `thermal_conductivity`, `emissivity`, `specific_heat`, `density`. **Do NOT fetch live from NIST API.**
- [ ] T012 [US1] Implement `code/data_ingestion.py`: Fetch raw NIST data from the canonical source ONCE (if available) or use the hardcoded JSON, save to `data/raw/nist_materials.json`, and compute a SHA256 checksum of the resulting file. Save the checksum to `data/raw/nist_materials.json.sha256`. This ensures reproducibility for subsequent runs.
- [X] T013 [US1] Implement `code/data_ingestion.py`: Scrape current market prices for the 4 materials from ` Name or service not known)"))]. **Fallback**: If this fails, attempt to fetch a verified CSV from `. **Edge Case Handling**: If a price is unavailable after all attempts, **exclude** that material from the simulation, log a warning, and **add a `status` field** (e.g., "invalid_price") to the output CSV for that material to ensure traceability. **DO NOT** fallback to synthetic data.
- [X] T014 [US1] Implement cost function logic in `code/data_ingestion.py`: Calculate total cost $C$ for a specific geometry by summing (mass × price) for all components, ensuring all costs are strictly positive. **Strictly follow spec: $C = \sum (mass_i \times price_i)$ without additional complexity factors.**
- [ ] T015 [US1] Generate `data/processed/materials.csv` containing material_id, thermal properties, density, unit price, calculated cost, and a `status` field (e.g., "valid", "invalid_price").
- [ ] T016 [US1] Validate that the output CSV contains no missing values for valid materials and that all costs are positive scalars.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 1D Transient Heat Transfer Simulation (Priority: P1)

**Goal**: Implement a 1D transient heat transfer model in Python using `scipy.integrate` to simulate thermal dynamics for three geometries under solar irradiance profiles, calculating time-averaged thermal efficiency $\eta$.

**Independent Test**: Run the simulation with fixed inputs (Aluminum, single-slope) and verify that output efficiency $\eta$ is between 0.0 and 0.8, and the simulation completes within 60 seconds on CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for view factor calculation in `tests/unit/test_simulation.py`: Verify `calculate_view_factor` exists with signature `(geometry: GeometryConfig, angle: float) -> float` and asserts the result is within [0, 1].
- [X] T018 [P] [US2] Unit test for convective heat transfer coefficient calculation in `tests/unit/test_simulation.py`: Verify `calculate_convective_coeff` exists with signature `(temp_diff: float, geometry: GeometryConfig) -> float` and asserts the result is positive.
- [X] T019 [P] [US2] Integration test for energy balance closure in `tests/integration/test_simulation.py`: Verify `run_simulation` returns a result where `input_energy ≈ output_energy + losses` within a tolerance of a minimal margin.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/simulation.py`: Define `GeometryConfig` class supporting flat-plate, single-slope, and double-slope. **Model slope variations via "view factors" and "convective heat transfer coefficients"** (as per Plan Summary). Reference `data-model.md` for exact attributes (inclination_angle, surface_area). Calculate effective projected area using view factors, not simple cosine projection.
- [X] T021 [US2] Implement `code/simulation.py`: Create the 1D transient heat transfer ODE system using `scipy.integrate.solve_ivp`, incorporating solar irradiance boundary conditions from the data fetched in **T008**.
- [ ] T022 [US2] Implement `code/simulation.py`: Calculate time-averaged thermal efficiency $\eta$ over the final 30 minutes of the transient simulation for every valid material-geometry combination.
- [ ] T023 [US2] Implement `code/validation.py`: Perform **Primary Validation**: Check **Energy Balance Closure** (Input Energy = Output Energy + Losses). **If this check fails, exclude the data point from results.** This is the hard gate per the Plan.
- [ ] T024 [US2] Implement `code/validation.py`: Perform **Secondary Check**: Log if calculated efficiency $\eta$ falls within ±10% of the mean efficiency (0.45) from Duffie & Beckman as a warning, but **DO NOT** exclude the data point based on this check alone.
- [ ] T025 [US2] Generate `data/processed/simulation_results.csv` containing material_id, geometry_id, steady_state_efficiency, total_cost, and convergence_status. **Conditional: Only generate this file if T023 validation passes.**
- [ ] T026 [US2] Run batch simulation for all material-geometry combinations (3 geometries × 4 materials = 12 combinations); ensure total runtime < 180 seconds on CPU. **Note: Angle sweep (0-80°) is removed to respect Spec scope. **

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Pareto Frontier Optimization and Visualization (Priority: P2)

**Goal**: Perform multi-objective optimization to identify the Pareto frontier of efficiency ($\eta$) vs. cost ($C$) and generate a scatter plot highlighting the "knee point".

**Independent Test**: Execute the optimization script and verify that the generated plot contains non-dominated solutions, a clearly marked Pareto frontier, and a "knee point" representing the optimal trade-off.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Pareto frontier identification algorithm in `tests/unit/test_optimization.py`: Verify `find_pareto_frontier` exists with signature `(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]` and asserts the returned list contains only non-dominated points.
- [ ] T028 [P] [US3] Unit test for knee point calculation (distance to ideal point) in `tests/unit/test_optimization.py`: Verify `calculate_knee_point` exists with signature `(frontier: List[Tuple[float, float]]) -> Tuple[float, float]` and asserts the result is one of the frontier points.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/optimization.py`: Load `data/processed/simulation_results.csv` (Prerequisite: **T025**) and filter for valid (non-dominated) solutions.
- [ ] T030 [US3] Implement `code/optimization.py`: Calculate the Pareto frontier of $\eta$ vs. $C$ using `scipy.optimize` or a standard non-dominated sorting algorithm.
- [ ] T031 [US3] Implement `code/optimization.py`: Calculate the "knee point" as the point on the frontier minimizing Euclidean distance to the ideal point (max $\eta$, min $C$).
- [ ] T032 [US3] Implement `code/optimization.py`: Calculate the coefficient of determination ($R^2$) of a linear fit to the Pareto frontier points. **Report this metric** to confirm the trade-off nature (SC-003).
- [ ] T032b [US3] Validate the trade-off nature: Ensure the $R^2$ metric is < 0.95 to confirm a non-linear trade-off. If $R^2 \ge 0.95$, log a warning that the frontier appears linear, but **DO NOT** fail the pipeline.
- [ ] T033 [US3] Implement `code/utils.py`: Generate a publication-quality scatter plot of efficiency vs. cost with the Pareto frontier highlighted and the knee point explicitly marked.
- [ ] T034 [US3] Save the final plot to `data/plots/pareto_frontier.png` and verify it demonstrates the trade-off relationship (diminishing returns).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Code cleanup and refactoring
- [ ] T037 Performance optimization across all stories (ensure CPU constraints are met)
- [ ] T038 [P] Additional unit tests for edge cases (API failures, convergence issues) in `tests/unit/`
- [ ] T039 Run quickstart.md validation
- [ ] T040 Verify reproducibility: Re-run full pipeline from raw API calls to final plot without manual intervention.

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 data (materials.csv) for simulation inputs. **T008 must complete before T021.**
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - **Explicitly depends on T025** (Generate simulation_results.csv) for optimization. **T025 -> T029 is mandatory.**

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
- All tests for a user story marked [P] can run in parallel (after module structure is created)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for cost function calculation in tests/unit/test_data_ingestion.py"
Task: "Contract test for material schema validation in tests/unit/test_material_schema.py"

# Launch all models for User Story 1 together:
Task: "Implement data ingestion script in code/data_ingestion.py"
Task: "Implement cost function logic in code/data_ingestion.py"
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
- **Critical**: Do NOT fallback to synthetic data if real data fetch fails; exclude invalid materials and log warnings with status flags.
- **Critical**: Use Energy Balance Closure as the primary validation gate (T023); FR-006 mean-efficiency check is a secondary warning (T024).
- **Critical**: Implement "view factors" and "convective coefficients" for slope modeling as per Plan (T020).
- **Critical**: Load hardcoded NIST JSON in T011; T012 handles the one-time fetch/checksum.
- **Critical**: T008 (Fetch Irradiance) must precede T021 (Define ODE).
- **Critical**: T025 (Generate CSV) must only run after T023 (Validation) passes.
- **Critical**: T029 (Load Results) depends on T025 (Generate Results).
- **Critical**: T032 calculates R²; T032b validates the trade-off nature without failing the pipeline.
- **Critical**: T026 restricted to 3 geometries; angle sweep removed to respect Spec scope.