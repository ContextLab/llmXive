# Tasks: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Input**: Design documents from `/specs/001-llmxive-density-horizon/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create directories `data/raw/`, `data/processed/`, `output/plots/`, `code/`, `code/utils/`, `code/config/`, `tests/unit/`, `tests/integration/`, `tests/contract/` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`. **Verification**: All directories exist and are writable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `entropy.py` utility in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/utils/entropy.py` to calculate Shannon Entropy on UTF-8 byte-level tokens (FR-008). **Verification**: Unit tests in `test_entropy.py` pass, confirming entropy calculation and clamping for zero density values (Edge Case).
- [X] T008 [P] Implement `heuristics.py` utility in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/utils/heuristics.py` to define the composite density formula `A weighted combination of Shannon_Entropy and Technical_Token_Ratio`. **Requirement**: The list of "technical terms" MUST be loaded from a configuration file `code/config/density_terms.json` at runtime, not hardcoded. The task must create a default `density_terms.json` with a representative list of search/retrieval terms (e.g., `['search_context', 'retrieval_window', 'semantic_density', 'agent_state', 'trajectory_log', 'masking_policy', 'evidence_turn', 'focus_decay', 'stale_observation', 'retention_limit', 'critical_evidence', 'heuristic_solver', 'logistic_function', 'regime_map']`) but the code must read this from the file. **Verification**: Unit tests in `test_heuristics.py` pass, confirming the config file is loaded correctly and the formula is applied.
- [X] T009 [P] Create `test_entropy.py` unit test in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/unit/test_entropy.py` to verify entropy calculation, clamping for zero density, and **logging of zero-density events** (Edge Case, FR-008).
- [X] T010 [P] Create `test_heuristics.py` unit test in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/unit/test_heuristics.py` to verify technical token ratio calculation and config file loading (FR-008).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Trajectory Generation with Controlled Density (Priority: P1) 🎯 MVP

**Goal**: Generate a set of synthetic search trajectories with parameterized semantic density and ground-truth critical evidence injection.

**Independent Test**: The system can be tested by running the generator with fixed seeds and verifying that the output JSON file contains a sufficient number of trajectories where the calculated entropy per token for injected evidence blocks matches the requested density levels (low, medium, high) within a tolerance of ±0.01 bits/token. [UNRESOLVED-CLAIM: c_dacf7717 — status=not_enough_info]

### Implementation for User Story 1

- [X] T011 [US1] Implement `generate_trajectories.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/generate_trajectories.py` to create exactly **500** synthetic trajectories (aligned with Spec SC-005 and Plan Summary) with controlled density (low/med/high) and critical evidence injection. **Deliverable**: Output JSON to `data/raw/` containing an array of trajectory objects. Each object MUST include metadata fields: `evidence_turn_index` (int), `density_value` (float), and `is_critical` (boolean). **Requirements**: Include clamping logic for zero density values (Edge Case) and validation to ensure density is computed solely from input text statistics (FR-007). (US-1 Acceptance 3, FR-001, FR-007).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Agent Simulation with Variable Retention Horizons (Priority: P2)

**Goal**: Run a simulation loop where a rule-based agent processes trajectories with varying retention horizons to observe success rate fluctuations.

**Independent Test**: The system can be tested by running the simulation on a small subset of trajectories with a known "ground truth" retention horizon. The system must correctly report "failure" when the retention horizon is set to < 5 turns for high-density evidence, and "success" when ≥ 5 turns.

### Implementation for User Story 2

- [X] T014 [US2] Implement `simulate_agent.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/simulate_agent.py` to load trajectories and apply retention horizons (1 to T). **Requirements**:
 1. Implement the "Heuristic Solver" using the specific logistic function `P(retrieval) = sigmoid(α * (density - threshold))` to determine success probabilistically (FR-009). Explicitly define `α` (scaling) and `threshold` (critical density) as **configurable CLI arguments with default values** (e.g., `--alpha 1.0 --threshold 0.5`) to ensure the pipeline can run end-to-end without manual intervention (Constitution I).
 2. Implement success logic: `1 if (critical_evidence_turn_index >= current_turn - retention_horizon + 1) AND (agent_heuristic_success = true), else 0` (FR-002). Sample from the logistic function to determine `agent_heuristic_success`.
 3. Implement streaming approach to write results to `data/processed/` immediately after each batch to manage RAM (FR-005).
 4. Handle edge case where critical evidence is at the very last turn ($T$) to ensure horizon $T$ retains it correctly.
 **Verification**: Ensure the system correctly reports "failure" for horizon < 5 and "success" for horizon ≥ 5 given ground truth (US-2 Acceptance 1 & 2). Confirm peak RAM usage remains < 7 GB during full run. [UNRESOLVED-CLAIM: c_591f8fb2 — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for simulation output schema in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/contract/test_simulation_output.py`
- [X] T017 [P] [US2] Integration test for horizon masking logic in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/integration/test_horizon_masking.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Regime Mapping (Priority: P3)

**Goal**: Perform logistic regression (GLM) with natural splines to quantify the interaction effect and generate a 3D surface plot.

**Independent Test**: The system can be tested by feeding it a synthetic dataset where the interaction effect is hard-coded. The regression output must show a statistically significant interaction term (p < 0.05) and the plot must visually display the surface shift.

### Implementation for User Story 3

- [X] T018 [US3] Implement `analyze_results.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py` to load simulation logs and perform logistic regression using `statsmodels`. **Requirements**:
 1. Include **natural splines with a fixed number of degrees of freedom** (e.g., `df=3`) for the 'horizon' variable. Do NOT perform runtime power analysis to select `df`; use a deterministic rule or fixed value to ensure reproducibility (FR-003).
 2. Implement validation to check the minimum sample size for statistical power and verify that the interaction term is significant at p < 0.05.
 3. Extract and output regression coefficients and **p-values** for the `density * horizon` interaction term to `output/regression_summary.json` (FR-006, SC-001).
 4. Automatically generate `output/hypothesis_summary.md` containing the regression coefficient, p-value, and a boolean `hypothesis_supported` derived from the p-value threshold (p < 0.05) (US-3, Acceptance 3).
 **Verification**: Confirm `output/regression_summary.json` and `output/hypothesis_summary.md` exist and contain correct data. Verify the boolean logic in the summary file. (FR-003, FR-006).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Contract test for regression output schema in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/contract/test_regression_output.py`
- [X] T024 [P] [US3] Integration test for plot generation in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/integration/test_plot_generation.py`
- [X] T022 [P] [US3] Verify hypothesis summary output: Run `code/analyze_results.py` and confirm `output/hypothesis_summary.md` is created with the correct `.md` extension and contains the expected boolean logic (US-3 Acceptance 3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Update `README.md` with project overview, installation instructions, and usage examples in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`
- [X] T026 [P] Create `docs/api.md` documenting the public functions in `code/utils/`, `code/generate_trajectories.py`, and `code/simulate_agent.py`
- [X] T027 [P] Create `docs/quickstart.md` with a step-by-step guide to run the full pipeline
- [X] T028 Code cleanup: Remove dead code in `code/generate_trajectories.py`
- [X] T029 Code cleanup: Remove dead code in `code/simulate_agent.py`
- [X] T030 Code cleanup: Remove dead code in `code/analyze_results.py` <!-- ATOMIZE: requested -->
- [X] T031 Code cleanup: Standardize import orders in `code/generate_trajectories.py` using `isort`
- [X] T032 Code cleanup: Standardize import orders in `code/simulate_agent.py` using `isort`
- [X] T033 Code cleanup: Standardize import orders in `code/analyze_results.py` using `isort`
- [ ] T034 [S] [US2, US3] Performance optimization: Optimize loops in `simulate_agent.py` and `analyze_results.py` to ensure runtime < 6h and RAM < 7 GB (FR-005, SC-003, SC-004). **Requirement**: Use vectorization (NumPy/Pandas) and **profile memory usage using `memory-profiler` and assert max < 7GB ** to verify constraints. **Critical**: This task is mandatory for the pipeline to be considered executable. **Dependency**: Must run after T014 and T018 are complete.
- [ ] T035 [P] Additional unit tests in `tests/unit/`
- [ ] T036 Run quickstart.md validation

---

## Phase O: Visualization & Reporting

**Goal**: Generate the required 3D surface plot and finalize the regime map visualization.

- [X] T037 [US3] Implement `visualize_results.py` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/visualize_results.py` to generate the 3D surface plot (PNG) visualizing Success Rate vs. Masking Horizon and Semantic Density, specifically the **regime map of optimal retention windows**. **Requirements**:
 1. Use `matplotlib` or `plotly` (CPU-compatible) to render the 3D surface.
 2. Ensure axes are labeled exactly as "Masking Horizon", "Semantic Density", and "Success Rate" (FR-004, SC-002).
 3. Enforce output file size limit of ≤ 5 MB (US-3 Acceptance 2).
 4. Save output to `output/plots/regime_map.png`.
 **Verification**: Verify `output/plots/regime_map.png` exists, is valid PNG, ≤ 5 MB, and contains correctly labeled axes.

---

## Phase P: Final Validation & Documentation

**Goal**: Ensure the entire pipeline runs end-to-end and documentation is up to date.

- [ ] T038 [P] Create `run_pipeline.sh` script in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/` to orchestrate the full flow: `generate_trajectories.py` → `simulate_agent.py` → `analyze_results.py` → `visualize_results.py`. **Requirements**: Include error handling to stop on failure and log exit codes.
- [ ] T039 [P] Execute the full pipeline using `run_pipeline.sh` on a small subset (e.g., a limited number of trajectories) to verify end-to-end data flow and output generation. **Verification**: All expected output files (`data/raw/*.json`, `data/processed/*.csv`, `output/regression_summary.json`, `output/hypothesis_summary.md`, `output/plots/regime_map.png`) are generated and valid.
- [X] T040 Update `docs/quickstart.md` with the final `run_pipeline.sh` instructions and expected output locations.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Visualization (Phase O)**: Depends on User Story 3 (Analysis) completion
- **Final Validation (Phase P)**: Depends on all implementation phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 simulation logs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Services before endpoints/analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement generate_trajectories.py in code/generate_trajectories.py"
Task: "Implement clamping logic in generate_trajectories.py"

# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for trajectory schema in tests/contract/test_trajectory_schema.py"
Task: "Integration test for density injection logic in tests/integration/test_density_injection.py"
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
- [S] tasks = sequential, depend on previous tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence