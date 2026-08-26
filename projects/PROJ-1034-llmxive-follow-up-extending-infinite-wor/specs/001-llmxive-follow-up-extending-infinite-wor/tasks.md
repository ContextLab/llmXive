# Tasks: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

- [ ] T001 Create project structure per implementation plan (`src/sim`, `src/analysis`, `src/data`, `src/cli`, `src/tests`)
- [ ] T002 Initialize Python project with dependencies: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `huggingface_hub`, `torch` (cpu-only), `matplotlib`, `seaborn`, `pyyaml`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
**⚠️ ORDERING**: T007 (Data Models) MUST complete before T004a, T004b, T004c, T005, and T006.

- [ ] T004a [P] [US1] Define parameter schema for CA engine (locality, memory, non-linearity) in `src/sim/eco_director.py` (Dep: T007)
- [ ] T004b [P] [US1] Implement core CA update loop in `src/sim/eco_director.py` (Dep: T007)
- [ ] T004c [P] [US1] Implement configuration loader for `src/sim/eco_director.py` (Dep: T007)
- [ ] T005 [P] [US1] Implement `src/sim/neural_baseline.py` (Throttled M Parameter Proxy) with CPU-only constraints (Dep: T007)
- [ ] T006 [P] [US1] Implement `src/sim/physics_oracle.py` (Stochastic Physics Sandbox) to validate external constraints (FR-008) (Dep: T007)
- [ ] T007 Create base data models: `SimulationRun`, `MetricRecord`, `ParameterGrid` in `src/data_models.py`
- [ ] T008 Implement `src/cli/run_simulation.py` entry point with strict memory ceiling and timeout enforcement (FR-003)
- [ ] T009 Configure deterministic random seeds in `src/config.py` and ensure reproducibility across runs
- [ ] T010 Implement logging infrastructure to record `coherence_score`, `diversity_score`, and `step_latency` at intervals

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-Constrained Simulation Baseline (Priority: P1) 🎯 MVP

**Goal**: Run the comparative simulation between the neural baseline and the CA Eco-Director on a standard GitHub Actions free-tier runner to establish performance bounds.

**Independent Test**: The system can be tested by running the simulation script for a fixed duration on the CI runner and verifying that the job completes without OOM errors or timeout, while logging latency per step. The test must also verify the 'Power-Limited' flag and fallback dataset behavior if the primary dataset is unavailable.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T011a [P] [US1] Unit test for parameter schema validation in `src/sim/eco_director.py`
- [ ] T011b [P] [US1] Unit test for eco_director.py state transitions in `tests/unit/test_eco_director.py`
- [ ] T012 [P] [US1] Integration test for simulation pipeline memory limits in `tests/integration/test_simulation_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement throttling logic in `src/sim/neural_baseline.py` to ensure it runs within 6h CPU limits
- [ ] T014 [US1] Implement memory monitoring in `src/cli/run_simulation.py` to detect and terminate runs exceeding a predefined memory threshold. (Edge Case 1), outputting a structured JSON status log
- [ ] T015 [US1] Implement timeout enforcement in `src/cli/run_simulation.py` to handle time-bound baseline runs (Edge Case 2), outputting a structured JSON status log
- [ ] T015b [US1] Implement logic to flag results as 'Power-Limited' and fallback to a smaller synthetic dataset if the primary dataset is unavailable (Edge Case 3), consuming JSON status logs from T014/T015
- [ ] T016 [US1] Execute a minimum of 10,000 time-steps of CA vs Neural baseline per configuration and log `step_latency`
- [ ] T017 [US1] Verify no NaN values in logged metrics and graceful handling of state explosion warnings

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sweep Algorithmic Parameters for Coherence Analysis (Priority: P2)

**Goal**: Systematically vary CA parameters to identify which algorithmic properties correlate with high coherence/diversity scores.

**Independent Test**: The system can be tested by running a single parameter sweep and verifying that the output dataset contains distinct entries for each configuration with corresponding metric scores. The test must also verify that the model adjustment/fallback strategy is triggered correctly if the lag-1 autocorrelation check fails.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for parameter grid generation in `tests/unit/test_param_grid.py`
- [ ] T019 [P] [US2] Integration test for LMM data preparation in `tests/integration/test_lmm_data_prep.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `src/analysis/lmm_runner.py` to perform Linear Mixed-Effects Model analysis (FR-004) (Dep: T032)
- [ ] T021a [US2] Implement `src/analysis/acf_validator.py` to compute ACF and check lag-1 autocorrelation < 0.1 (FR-007)
- [ ] T021b [US2] Implement model adjustment logic or fallback strategy in `src/analysis/acf_validator.py` if lag-1 >= 0.1 (FR-007) (Dep: T021a)
- [ ] T032 [US2] Implement partial correlation analysis to ensure metric independence from input parameters (SC-006) (Dep: T021b)
- [ ] T022 [US2] Implement `src/analysis/rf_runner.py` for Random Forest feature importance analysis (FR-009)
- [ ] T023a [US2] Create parameter grid generator in `src/cli/run_simulation.py`
- [ ] T023b [US2] Create simulation runner wrapper in `src/cli/run_simulation.py`
- [ ] T023c [US2] Create data aggregation script in `src/cli/run_simulation.py`
- [ ] T024 [US2] Implement logic to exclude unstable configurations (state explosion) from statistical analysis (Edge Case 1)
- [ ] T025 [US2] Ensure `data/raw/` logs are saved for every parameter configuration and `data/processed/` aggregates metrics
- [ ] T026 [US2] Run [deferred] time-steps per configuration as per FR-002 and record metrics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Statistical Parity and Latency Trade-offs (Priority: P3)

**Goal**: Confirm if optimal CA configuration achieves statistical parity with neural baseline and meets ≥90% latency reduction target.

**Independent Test**: The system can be tested by comparing aggregate metrics and verifying the latency reduction calculation is explicitly reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for latency reduction calculation in `tests/unit/test_latency_calc.py`
- [ ] T028 [P] [US3] Integration test for sensitivity analysis report in `tests/integration/test_sensitivity_report.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/sensitivity.py` to sweep coherence decision cutoffs across a range of low, moderate, and high thresholds. (FR-006)
- [ ] T030 [US3] Implement statistical comparison logic to calculate p-values for coherence/diversity parity (SC-002)
- [ ] T031 [US3] Implement latency reduction calculator to verify ≥90% target (SC-001, FR-005) (Dep: T013)
- [ ] T033 [US3] Generate final report comparing CA vs Neural baseline including semantic novelty assessment
- [ ] T034 [US3] Validate results against `physics_oracle.schema.yaml` to ensure non-tautological coherence (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T036 Code cleanup and refactoring for modularity
- [ ] T037 Performance optimization for simulation loop (vectorization where possible)
- [ ] T038 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **Critical Ordering**: T007 (Data Models) MUST complete before T004a, T004b, T004c, T005, and T006.
  - T004a, T004b, T004c must be completed in sequence (004a -> 004b -> 004c).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `eco_director` and `physics_oracle` implementation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2

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
Task: "Unit test for parameter schema validation in src/sim/eco_director.py"
Task: "Unit test for eco_director.py state transitions in tests/unit/test_eco_director.py"
Task: "Integration test for simulation pipeline memory limits in tests/integration/test_simulation_pipeline.py"

# Launch all implementation for User Story 1 together:
Task: "Implement throttling logic in src/sim/neural_baseline.py"
Task: "Implement memory monitoring in src/cli/run_simulation.py"
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