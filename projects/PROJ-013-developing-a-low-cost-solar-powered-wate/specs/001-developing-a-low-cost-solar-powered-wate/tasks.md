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

- [X] T001 Create project structure: `code/`, `data/raw/`, `data/processed/`, `data/plots/`, `tests/unit/`, `tests/integration/`. Initialize `README.md` and `.gitignore`. **Initialize `state/...yaml` artifact hash map and generate initial checksums for the directory structure as required by Constitution Principle III.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/plots/`)
- [X] T005 [P] Implement utility helpers for logging, error handling, and path resolution in `code/utils.py`
- [X] T006 Create base configuration loader for API keys and simulation parameters in `code/config.py`
- [X] T007 Setup environment configuration management (`.env` support for NASA POWER keys)
- [X] T020b [P] **Documentation & Spec Amendment Task**:
 1. **Update `specs/.../spec.md`**: In section FR-003, replace the text "modeling slope variations via effective projected area" with "modeling slope variations via angle-dependent view factors and convective heat transfer coefficients".
 2. **Create `specs/.../deviations.md`**: Create a new file with the following content:
 ```markdown
 # Deviations Log
 ## Deviation 1: Slope Modeling Method
 **Original Spec (FR-003)**: Model slope variations via "effective projected area".
 **Implemented Approach**: Model slope variations via "view factors" and "convective heat transfer coefficients".
 **Rationale**: Scientific rigor requires explicit calculation of geometric physics (view factors) rather than simple projected area approximations to capture slope effects accurately.
 **Status**: Approved by Plan Summary "Note on Spec Constraints".
 ```
 3. **Commit**: Ensure these changes are committed before T020 begins. **This task MUST complete before T020.** **Note**: This task amends the Spec to authorize the implementation in T020. **Verification**: Compute SHA256 of the new `deviations.md` file and log the hash to the build output to verify completion.
- [X] T008 [US2] **Blocking**: Implement `code/data_ingestion.py`: {{claim:c_fd54f849}}
 **Endpoint**: ` (Use the correct, reachable NASA POWER API endpoint for daily solar radiation).
 **Parameters**: `start=YYYY-MM-DD`, `end=YYYY-MM-DD`, `parameters=RSR`, `aggregation=daily`.
 **Traceability**: FR-003, US-2.
 **Boundary Condition**: This data provides the boundary conditions for the 'view factors' and 'convective coefficients' modeling (See T020b deviation).
 **Fallback Logic**: If the API returns < 30 days of historical data, default to a hardcoded representative average of **550 W/m²** (Reference: Plan Summary - Representative Average Note). Handle missing/zero data by defaulting to this representative average.
 **Prerequisite for T021**. (Blocking: Must complete before T021).

References: [DOI/arXiv/author-year placeholder]

Research Question: [Research Question placeholder]

Method: [Method placeholder]

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Cost Function Construction (Priority: P1) 🎯 MVP

**Goal**: Retrieve thermal properties from NIST (fetched on every run for reproducibility) and scrape current market prices to construct a deterministic cost function $C = \sum (mass_i \times price_i)$.

**Independent Test**: Run the data ingestion script and verify that `data/processed/materials.csv` contains a representative set of material-geometry combinations with non-null thermal properties and valid positive cost values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These tests verify specific function signatures and logic.

- [X] T009 [US1] Unit test for cost function calculation in `tests/unit/test_data_ingestion.py`: Verify `calculate_cost` exists with signature `(materials: List[MaterialProfile], geometry: GeometryConfig) -> float` and asserts `calculate_cost` returns a float > 0 for valid inputs.
- [X] T010 [US1] Contract test for material schema validation in `tests/unit/test_material_schema.py`: Verify `load_material_schema` exists with signature `(path: str) -> Schema` and asserts the schema loads correctly for the defined `MaterialProfile`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_ingestion.py`: **Fetch and Validate Script**: Fetch raw NIST data for Aluminum (ID: 7429-90-5), Copper (ID: 7440-50-8), Black-painted Steel (mapped to Carbon Steel Alloy 1018), and Plastic (Polyethylene) from the NIST Chemistry WebBook. **This script runs on every execution.** If the local cache checksum fails, re-fetch. **Endpoints**: Use specific NIST property keys: `thermal_conductivity`, `emissivity`, `specific_heat`, `density`. Save the fetched data to `data/raw/nist_materials.json` and compute a SHA256 checksum. Save the checksum to `data/raw/nist_materials.json.sha256`. **Note**: This satisfies FR-001 "retrieve" by fetching from the canonical source on every run. **Prerequisite for T011.**
- [ ] T013 [US1] Implement `code/data_ingestion.py`: **Fetch Current Prices**: Fetch **current** market prices for the 4 materials from the **World Bank Commodity Prices API** (` Name or service not known)"))] with specific material codes for Aluminum, Copper, Steel, Plastic). **NO STATIC FALLBACKS**. **Edge Case Handling**: If the live API is unreachable or returns no data, the script MUST **FAIL LOUDLY** (raise an exception with a specific error code) and **NOT** proceed with synthetic or static data. Save the fetched data to `data/raw/market_prices.json` and compute a SHA256 checksum. **Note**: This satisfies FR-002 "current market prices" requirement with a verified endpoint. **Prerequisite for T014.** <!-- FAILED: unspecified -->
- [ ] T011 [US1] Implement `code/data_ingestion.py`: Load thermal properties (conductivity, emissivity, specific heat, density) for Aluminum, Copper, Black-painted Steel, and Plastic from the **cached JSON file** `data/raw/nist_materials.json` generated in **T012**. **Prerequisite: T012 must complete before T011.** Ensure keys match `data-model.md` (MaterialProfile): `thermal_conductivity`, `emissivity`, `specific_heat`, `density`. **Note**: This loads the fetched data. If the checksum in T012 fails, the file is re-fetched. <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement cost function logic in `code/data_ingestion.py`: Calculate total cost $C$ for a specific geometry by suming (mass × price) for all components, ensuring all costs are strictly positive. **Strictly follow spec: $C = \sum (mass_i \times price_i)$ without additional complexity factors.** **Prerequisite: T013 (Prices) and T011 (Properties) must complete.** <!-- FAILED: unspecified -->
- [ ] T015 [US1] Generate `data/processed/materials.csv` containing material_id, thermal properties, density, unit price, calculated cost, and a `status` field (e.g., "valid", "invalid_price").
- [X] T016 [US1] Validate that the output CSV contains no missing values for valid materials and that all costs are positive scalars. **Artifact**: Generate `data/processed/materials_validation.json` with validation results.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 1D Transient Heat Transfer Simulation (Priority: P1)

**Goal**: Implement a 1D transient heat transfer model in Python using `scipy.integrate` to simulate thermal dynamics for three geometries under solar irradiance profiles, calculating time-averaged thermal efficiency $\eta$.

**Independent Test**: Run the simulation with fixed inputs (Aluminum, single-slope) and verify that output efficiency $\eta$ is between 0.0 and 0.8, and the simulation completes within 60 seconds on CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [US2] Unit test for view factor calculation in `tests/unit/test_simulation.py`: Verify `calculate_view_factor` exists with signature `(geometry: GeometryConfig, angle: float) -> float` and asserts the result is within [0, 1].
- [ ] T018 [US2] Unit test for convective heat transfer coefficient calculation in `tests/unit/test_simulation.py`: Verify `calculate_convective_coeff` exists with signature `(temp_diff: float, geometry: GeometryConfig) -> float` and asserts the result is positive.
- [ ] T019 [US2] Integration test for energy balance closure in `tests/integration/test_simulation.py`: Verify `run_simulation` returns a result where `input_energy ≈ output_energy + losses` within a tolerance of a minimal margin.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/simulation.py`: Define `GeometryConfig` class supporting flat-plate, single-slope, and double-slope. **Model slope variations via "view factors" and "convective heat transfer coefficients"** (as per T020b deviation from Spec FR-003). Reference `data-model.md` for exact attributes (inclination_angle, surface_area). Calculate effective projected area using view factors, not simple cosine projection. **Note**: This physical modeling satisfies the Spec's FR-003 requirement for "effective projected area" by accurately calculating the geometric effect via the authorized deviation. **Prerequisite: T020b must complete.**
- [ ] T021 [US2] Implement `code/simulation.py`: Create the 1D transient heat transfer ODE system using `scipy.integrate.solve_ivp`, incorporating solar irradiance boundary conditions from the data fetched in **T008**. **Prerequisite: T020 (GeometryConfig) and T008 (Irradiance) must complete.**
- [ ] T038 [US2] Verify that `code/simulation.py` explicitly logs the "Energy Balance Closure" error message when the check fails, ensuring the exclusion reason is traceable in `data/processed/validation_log.json`.
- [ ] T039 [US2] Add a `check_convergence` function in `code/simulation.py` that validates the ODE solver's `status` flag before including a result in `simulation_results.csv`, ensuring non-converged runs are excluded per Edge Case handling.
- [X] T023a [US2] **Plan Amendment Task**: Update `plan.md` Summary section to explicitly state: "The implementation will use Energy Balance as the primary gate and **FR-006 literature range check as a hard gate** (exclude if failed)." **Prerequisite**: Must be committed before T023b.
- [ ] T023b [US2] Implement `code/validation.py`: Perform **Primary Validation**: Check **Energy Balance Closure** (Input Energy = Output Energy + Losses). **If this check fails, exclude the result from data/processed/simulation_results.csv.** Perform **Secondary Validation (FR-006)**: Check if calculated efficiency $\eta$ falls within ±10% of the mean efficiency (0.45) from Duffie & Beckman (**Solar Engineering of Thermal Processes, Chapter 10, Section 10.2**). **If FR-006 check fails, EXCLUDE the result and log an error.** **Note**: This task enforces the Spec's FR-006 as a hard gate, as amended in T023a.
- [ ] T025 [US2] Generate `data/processed/simulation_results.csv` containing material_id, geometry_id, steady_state_efficiency, total_cost, and convergence_status. **Conditional: Only generate this file if T023b, T038, and T039 validation passes.** **Prerequisite: T023b must complete.**
- [X] T026 [US2] Run batch simulation for all material-geometry combinations (3 geometries × 4 materials = 12 combinations); ensure total runtime < 180 seconds on CPU. [UNRESOLVED-CLAIM: c_8e6a3932 — status=not_enough_info] **Artifact**: Generate `data/processed/batch_runtime_log.json` with runtime metrics. **Note: Angle sweep (0-80°) is removed to respect Spec scope.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Pareto Frontier Optimization and Visualization (Priority: P2)

**Goal**: Perform multi-objective optimization to identify the Pareto frontier of efficiency ($\eta$) vs. cost ($C$) and generate a scatter plot highlighting the "knee point".

**Independent Test**: Execute the optimization script and verify that the generated plot contains non-dominated solutions, a clearly marked Pareto frontier, and a "knee point" representing the optimal trade-off.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [US3] Unit test for Pareto frontier identification algorithm in `tests/unit/test_optimization.py`: Verify `find_pareto_frontier` exists with signature `(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]` and asserts the returned list contains only non-dominated points.
- [ ] T028 [US3] Unit test for knee point calculation (distance to ideal point) in `tests/unit/test_optimization.py`: Verify `calculate_knee_point` exists with signature `(frontier: List[Tuple[float, float]]) -> Tuple[float, float]` and asserts the result is one of the frontier points.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/optimization.py`: Load `data/processed/simulation_results.csv` (Prerequisite: **T025**) and filter for valid (non-dominated) solutions. **Explicit Prerequisite: T025 must complete before T029.**
- [ ] T030 [US3] Implement `code/optimization.py`: Calculate the Pareto frontier of $\eta$ vs. $C$ using `scipy.optimize` or a standard non-dominated sorting algorithm.
- [ ] T031 [US3] Implement `code/optimization.py`: Calculate the "knee point" as the point on the frontier minimizing Euclidean distance to the ideal point (max $\eta$, min $C$).
- [ ] T032a [US3] Implement `code/optimization.py`: Calculate the coefficient of determination ($R^2$) of a linear fit to the Pareto frontier points using **Ordinary Least Squares (OLS) via `scipy.stats.linregress`**. **Enforce SC-003**: If $R^2 \ge 0.95$, **flag the result as 'linear_tradeoff'** and log the R² value to `data/processed/optimization_log.json`. **Do NOT exclude the data point.** Report this metric to confirm the trade-off nature (SC-003). **Note**: This preserves valid simulation data while correctly identifying the failure of the trade-off hypothesis.
- [ ] T033 [US3] Implement `code/utils.py`: Generate a publication-quality scatter plot of efficiency vs. cost with the Pareto frontier highlighted and the knee point explicitly marked.
- [X] T034 [US3] Save the final plot to `data/plots/pareto_frontier.png` and verify it demonstrates the trade-off relationship (diminishing returns).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates: Update `README.md` with installation steps, `docs/quickstart.md` with pipeline usage, and `docs/api.md` with function signatures.
- [X] T040 [P] Additional unit tests for edge cases (API failures, convergence issues) in `tests/unit/`
- [X] T041 Run quickstart.md validation
- [X] T042 Verify reproducibility: Re-run full pipeline from raw API calls to final plot without manual intervention.

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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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
- **Critical**: Use Energy Balance Closure as the primary gate (T023b); FR-006 is a hard gate (exclude results), as amended in T023a. The Plan now reflects this.
- **Critical**: Implement "view factors" and "convective coefficients" for slope modeling as per T020b deviation (T020).
- **Critical**: Fetch NIST data on every run (T012) and load with checksum validation (T011). **T012 must precede T011.**
- **Critical**: Fetch Prices (T013) must precede Cost Calculation (T014).
- **Critical**: T008 (Fetch Irradiance) must precede T021 (Define ODE).
- **Critical**: T025 (Generate CSV) must only run after T023b, T038, T039 (Validation) pass.
- **Critical**: T029 (Load Results) depends on T025 (Generate Results).
- **Critical**: T032a calculates R² and flags the result as 'linear_tradeoff' if R² >= 0.95, preserving the data.
- **Critical**: T026 restricted to 3 geometries; angle sweep removed to respect Spec scope.
- **Note on Plan/Spec Contradiction**: T023a and T023b align the Plan with the Spec's mandatory FR-006 enforcement. The Plan now states FR-006 is a hard gate.
- **Note on Methodology**: T020 uses "view factors" to satisfy FR-003's "effective projected area" requirement via rigorous physics modeling, authorized by T020b.
- **Critical**: T038 (New) Verify that `code/simulation.py` explicitly logs the "Energy Balance Closure" error message when the check fails, ensuring the exclusion reason is traceable in `data/processed/validation_log.json`.
- **Critical**: T039 (New) Add a `check_convergence` function in `code/simulation.py` that validates the ODE solver's `status` flag before including a result in `simulation_results.csv`, ensuring non-converged runs are excluded per Edge Case handling.
- **Critical**: T020b (Moved to Phase 2) Amends Spec FR-003 and creates `deviations.md` before T020 runs. **T020b must complete before T020.**

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T043 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
