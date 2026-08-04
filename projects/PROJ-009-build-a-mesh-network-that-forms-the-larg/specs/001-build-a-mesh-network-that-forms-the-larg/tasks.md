# Tasks: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Input**: Design documents from `/specs/001-mesh-supercomputer/`
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

- [ ] T001 Create project structure per implementation plan (`code/orchestrator`, `code/analysis`, `code/simulation`, `code/data`, `code/tests`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `paramiko`, `scikit-learn`, `pandas`, `pygam`, `statsmodels`, `pytest`, `pyyaml`, `numpy`, `simpy`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base configuration manager in `code/orchestrator/config.py` to load node lists, granularity settings, and CI timeouts
- [X] T005 [P] Implement mock SSH node generator in `code/tests/unit/mock_nodes.py` for CI unit tests (no real hardware dependency)
- [X] T006 [P] Setup logging infrastructure in `code/orchestrator/logger.py` to capture wall-clock timestamps and heartbeat events
- [ ] T007 [P] Implement schema validation framework in `code/tests/contract/` using `pyyaml` to validate `ExecutionRun` and `RegressionModel` structures (DEPENDS ON T008) <!-- FAILED: unspecified -->
- [X] T008 [P] Create data model classes in `code/orchestrator/models.py` for `PhysicalNode`, `TaskChunk`, and `ExecutionRun` entities
- [X] T009 [P] Implement `enforce_pipeline_timeout()` in `code/orchestrator/timeout_guard.py` to enforce a hard timeout for the entire execution, analysis, AND simulation calibration pipeline (Required for FR-007, SC-004). This task provides the utility function; integration into specific execution flows (US1/US2/US3/Phase 6) occurs in those respective tasks.
- [X] T010 [P] Implement `validate_data_completeness()` in `code/analysis/data_validator.py` to check for critical variables. Logic: 'Exclude run if critical variables (throughput, latency) are missing; proceed with reduced model ONLY if non-critical covariates are missing' (Required for SC-006). DEPENDS ON T008.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Physical Testbed Orchestration & Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Deploy scheduler to physical mesh, inject network impairments, and collect raw execution logs (wall-clock, packets, CPU).

**Independent Test**: Launch a single benchmark job across multiple physical nodes with injected latency, verifying that the system distributes tasks, records `tcpdump` packet counts and `mpstat` CPU usage per node, and outputs a CSV file matching the schema defined in Key Entities.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for `ExecutionRun` CSV schema in `code/tests/contract/test_execution_schema.py`
- [X] T012 [P] [US1] Integration test for node heartbeat detection and re-assignment logic in `code/tests/integration/test_heartbeat_recovery.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `node_manager.py` in `code/orchestrator/` to handle SSH connections, heartbeat pings, and device discovery
- [ ] T014a [US1] Implement `instrumentor_remote.py` in `code/orchestrator/` to remotely execute `tcpdump` (packet counts) and `mpstat` (CPU usage) commands on target nodes via SSH. DEPENDS ON T013.
- [ ] T014b [US1] Implement `mpstat_parser.py` in `code/orchestrator/` to parse raw `mpstat` output strings into the structured `cpu_utilization_pct` field of the `PhysicalNode` entity. DEPENDS ON T014a.
- [ ] T015 [US1] Implement `scheduler.py` in `code/orchestrator/` to distribute `TaskChunk` units and handle OOM/straggler detection logic. DEPENDS ON T013.
- [ ] T016 [US1] Implement `benchmark.py` in `code/orchestrator/` to run the Monte Carlo integration workload on remote nodes
- [ ] T017 [US1] Implement `data_collector.py` in `code/orchestrator/` to aggregate raw logs from nodes and write to `code/data/raw/` as CSV. DEPENDS ON T014b, T016.
- [X] T018 [US1] Implement `check_network_saturation()` in `code/orchestrator/instrumentor_remote.py` to detect >20% packet loss and abort the run (Required for Edge Cases). DEPENDS ON T014a.
- [ ] T019 [US1] Implement `detect_dropout_events()` in `code/orchestrator/node_manager.py` to detect and record "dropout" events when nodes enter sleep mode or lose power. DEPENDS ON T013.
- [ ] T020 [US1] Implement `capture_unmodeled_vars()` in `code/orchestrator/instrumentor_remote.py` to log thermal throttling and OS noise metrics for the "Golden Dataset". DEPENDS ON T014a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Scheduler & Granularity Parameter Sweep (Priority: P2)

**Goal**: Execute parameter sweep varying task chunk sizes (fine/medium/coarse), node counts (a range of values), and network conditions to generate dataset for "sweet spot" identification.

**Independent Test**: Run three distinct execution campaigns (fine, medium, coarse granularity) with identical node sets and network conditions, verifying that the output contains three distinct throughput measurements and that coordination overhead differs between them.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for parameter sweep configuration YAML in `code/tests/contract/test_sweep_config.py`
- [ ] T022 [P] [US2] Integration test for granularity variation impact on overhead ratio in `code/tests/integration/test_granularity_sweep.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `sweep_runner.py` in `code/orchestrator/` to iterate through combinations of node counts (small, medium, and large) and granularity settings
- [ ] T024 [US2] Implement `overhead_calculator.py` in `code/analysis/` to compute `coordination_overhead_ratio` (handshake time vs. compute time) per run
- [ ] T025a [US2] Implement `network_impairment_local.py` in `code/orchestrator/` as a local utility to define and calculate latency/packet loss parameters (Injection configuration).
- [ ] T025b [US2] Implement `remote_impairment_orchestrator.py` in `code/orchestrator/` to apply the calculated network impairments to remote nodes via SSH (e.g., executing `tc` commands) during the sweep. DEPENDS ON T025a, T013.
- [ ] T026 [US2] Integrate `sweep_runner` with `data_collector` to ensure every run is tagged with `node_count`, `granularity`, and `injected_latency` in the output CSV
- [ ] T027 [US2] Implement `straggler_detector.py` in `code/orchestrator/` to identify high-variance completion times and log "heterogeneity penalty" metrics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Theoretical Validation (Priority: P3)

**Goal**: Perform multiple linear regression (MLR) and ANOVA on physical data; validate against Ong & Motani theoretical bounds. (Note: Plan.md adds GAM as a methodological update; tasks must implement BOTH to satisfy FR-005 and Plan).

**Independent Test**: Feed physical execution logs into the analysis module and verify that the system outputs a regression model object containing an R² value, p-values for interaction terms, and a comparison metric against the theoretical capacity bound.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for `RegressionModel` JSON output schema in `code/tests/contract/test_regression_schema.py`
- [ ] T029 [P] [US3] Integration test for theoretical bound calculation sanity check in `code/tests/integration/test_bound_validation.py`

### Implementation for User Story 3

- [ ] T030a [P] [US3] Implement `fit_mlr_with_interactions()` in `code/analysis/regression.py` using `statsmodels` to perform Multiple Linear Regression (required by FR-005/SC-001) modeling throughput as a function of heterogeneity, granularity, and injected latency. **MUST include interaction terms between heterogeneity and granularity**. DEPENDS ON T010.
- [ ] T030b [P] [US3] Implement `fit_gam_with_interactions()` in `code/analysis/regression.py` using `pygam` to model throughput as a Generalized Additive Model (required by Plan.md methodological update). DEPENDS ON T010.
- [ ] T031 [US3] Implement `anova_test.py` in `code/analysis/` to determine statistical significance (p < 0.05) of granularity differences
- [ ] T032 [US3] Implement `theoretical_bound.py` in `code/analysis/` to calculate Ong & Motani () capacity limits AND **flag if empirical performance exceeds the theoretical limit** (Unified validation logic). DEPENDS ON T030a.
- [ ] T033 [US3] Implement `validation.py` in `code/analysis/` to compare empirical curves against theoretical bounds and flag violations (measurement errors). DEPENDS ON T032.
- [ ] T034 [US3] Implement `report_generator.py` in `code/analysis/` to output final `RegressionModel` JSON with coefficients, p-values, R², and deviation metrics. DEPENDS ON T030a, T030b, T033, T010.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Simulation & Validation (Constitution Principle VI)

**Goal**: Build and calibrate a Discrete-Event Simulation (DES) model using the "Golden" physical dataset to validate internal state.

**Independent Test**: Run the DES model with parameters derived from physical runs and verify that the simulation output matches the physical data within a defined tolerance.

### Implementation for Phase 6

- [ ] T036 [P] [US3] Implement `des_model.py` in `code/simulation/` using `simpy` to model task scheduling, network latency, and node heterogeneity
- [ ] T037 [US3] Implement `calibration.py` in `code/simulation/` to fit DES parameters against the `data/raw/` physical logs (the "Golden Dataset" generated by T017). DEPENDS ON T036, T017.
- [ ] T038 [US3] Implement `internal_state_validator.py` in `code/simulation/` to perform the **validation logic** required by Constitution Principle VI: compare DES outputs against the "Golden Dataset" to verify internal state fidelity and ensure no circular predictions. DEPENDS ON T037.
- [ ] T039 [US3] Ensure simulation extrapolation logic is documented and bounded by the validated parameter space

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` including `quickstart.md` for running the physical testbed
- [ ] T041 Code cleanup and refactoring of `orchestrator` and `analysis` modules
- [ ] T042 [P] Performance optimization for the 6-hour CI limit (parallelize sweep execution where possible)
- [ ] T043 [P] Additional unit tests for `tcpdump` and `mpstat` parsing logic in `tests/unit/`
- [ ] T044 Security hardening of SSH key handling: Implement `SSHKeyManager` class in `code/orchestrator/node_manager.py`
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility

---

## Phase 8: Robustness & Error Handling (Review Concerns)

**Goal**: Address specific reviewer concerns regarding data integrity, failure modes, and CI reliability.

- [ ] T046 [US1] **Patch** `node_manager.py` to implement strict real data loading: ensure `node_manager.py` **fails loudly** (raises exception) if real device discovery or data fetch fails, explicitly **removing** any `try/except` blocks that fallback to `generate_synthetic_data()` or mock data (Addresses "Loader must fail loudly" rule).
- [ ] T047 [US2] **Patch** `scheduler.py` to implement adaptive chunking: dynamically split `TaskChunk` units when a node's available RAM (reported via `mpstat`/`free`) is insufficient, ensuring no OOM crashes occur on low-end devices (Addresses US1 Acceptance Scenario 3).
- [ ] T048 [US3] **Patch** `scheduler.py` to implement asynchronous timeout handling: enforce a 2x median task time limit for straggler nodes, re-assigning tasks immediately and logging "heterogeneity penalty" (Addresses Edge Case: Straggler stall).
- [ ] T049 [US3] **Patch** `data_validator.py` to implement run rejection: automatically flag and exclude runs where `packet_loss_rate` > 20% from the regression dataset, preventing corrupted data from skewing the model (Addresses Edge Case: Network saturation).
- [ ] T050 [US2] Implement `granularity_sweeper_config.py` to define the exact "fine/medium/coarse" ranges and node count steps (10, 15, 20) in a validated YAML config, ensuring the parameter sweep is reproducible and explicitly stated (Addresses US2 Acceptance Scenario 3).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T008 must complete before T007
 - T010 must complete before T030a/T030b
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Simulation (Phase 6)**: Depends on Phase 3 (US1) completion to have physical data for calibration
- **Polish (Phase 7)**: Depends on all desired user stories being complete
- **Robustness (Phase 8)**: Depends on US1 and US2 core logic being implemented to inject error handling

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T013 must complete before T014a, T015
 - T014a must complete before T014b
 - T014b must complete before T017, T018, T020
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - T010 must complete before T030a/T030b
 - T030a must complete before T032
 - T032 must complete before T033, T034
- **Simulation (Phase 6)**: Must wait for US1 to generate the "Golden Dataset"
 - T036 must complete before T037
 - T037 must complete before T038
- **Robustness (Phase 8)**: Must wait for core logic in US1/US2/US3
 - T046 depends on T013 (node discovery)
 - T047 depends on T015 (scheduler)
 - T049 depends on T010 (validator)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **except** where dependencies exist (T008 -> T007, T010)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for ExecutionRun CSV schema in code/tests/contract/test_execution_schema.py"
Task: "Integration test for node heartbeat detection in code/tests/integration/test_heartbeat_recovery.py"

# Launch all models for User Story 1 together:
Task: "Implement node_manager.py in code/orchestrator/node_manager.py"
# Note: T014a (instrumentor) depends on T013 (node_manager) and cannot run in parallel with it.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (collect real logs from a small cluster)
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
 - Developer A: User Story 1 (Orchestration & Data)
 - Developer B: User Story 2 (Sweep & Overhead)
 - Developer C: User Story 3 (Analysis & Bounds)
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
- **Data Hygiene**: Ensure all raw logs in `code/data/raw/` are preserved unchanged; derived stats go to `code/data/processed/`.
- **Real Data**: All analysis tasks must consume the REAL dataset generated by US1. Do not fabricate data for the regression model.
- **CI Limit**: The full parameter sweep (multiple runs) must be optimized to fit within the CI time limit.; if physical hardware is unavailable, use the mock node generator for unit tests only.
- **Timeout Enforcement**: T009 must be integrated into the main execution flow to enforce the 6-hour limit (FR-007) across all phases including simulation.
- **Network Saturation**: T018 must detect >20% packet loss and abort runs (Edge Cases).
- **Data Validation**: T010 must exclude runs with critical missing variables (SC-006).
- **Interaction Terms**: T030a must include interaction terms between heterogeneity and granularity (FR-005).
- **Unified Validation**: T032 must calculate bounds AND flag violations (FR-006).
- **Unmodeled Variables**: T020 must capture thermal throttling and OS noise (Assumptions).
- **Strict Real Data**: T046 ensures no synthetic fallbacks exist; the system must fail if real data cannot be fetched.
- **Adaptive Chunking**: T047 ensures low-RAM devices do not crash the system.
- **Straggler Handling**: T048 ensures the system does not hang on slow nodes.
- **Run Rejection**: T049 ensures saturated network runs do not corrupt the dataset.
- **Golden Dataset Validation**: T038 ensures the simulation model is validated against physical reality as required by Constitution Principle VI.