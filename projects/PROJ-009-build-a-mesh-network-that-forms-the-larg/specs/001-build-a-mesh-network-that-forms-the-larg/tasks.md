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

- [ ] T001 [P] Create project structure per implementation plan: `code/orchestrator`, `code/analysis`, `code/simulation`, `code/data/raw`, `code/data/processed`, `code/tests/unit`, `code/tests/integration`, `code/tests/contract`. Include `__init__.py` in all directories and a `.gitignore` excluding `data/`, `*.log`, `__pycache__`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `paramiko`, `scikit-learn`, `pandas`, `pygam`, `statsmodels`, `pytest`, `pyyaml`, `numpy`, `simpy`, `scipy`, `jsonschema`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools: Create `pyproject.toml` with ruff rules (E, W, F, I) and black line-length=88.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base configuration manager in `code/orchestrator/config.py` to load node lists, granularity settings, and CI timeouts
- [X] T005 [P] Implement mock SSH node generator in `code/tests/unit/mock_nodes.py` for CI unit tests (no real hardware dependency)
- [X] T006 [P] Setup logging infrastructure in `code/orchestrator/logger.py` to capture wall-clock timestamps and heartbeat events
- [X] T008 [P] Create data model classes in `code/orchestrator/models.py` for `PhysicalNode`, `TaskChunk`, and `ExecutionRun` entities
- [X] T007 [P] Implement schema validation framework in `code/tests/contract/` using `jsonschema` and `pyyaml` to validate `ExecutionRun` and `RegressionModel` structures. **Specifics**: Define YAML schemas for `ExecutionRun` (node_count, granularity, throughput, overhead_ratio) and `RegressionModel` (coefficients, p_values, r_squared, residuals, theoretical_bound_deviation). Implement a `validate_json_against_schema()` utility function that raises `ValidationError` on mismatch. **Dependency**: T008.
- [X] T009 [P] Implement `enforce_pipeline_timeout()` in `code/orchestrator/timeout_guard.py` to enforce a hard timeout for the entire execution, analysis, AND simulation calibration pipeline (Required for FR-007, SC-004). **Specifics**: This utility must be explicitly integrated into US1, US2, US3, and Phase 6 execution flows. **CI vs Local**: For CI runs (free-tier), enforce a strict time limit. For local physical runs (T_Physical), use a configurable local timeout to avoid killing mandatory physical validation. (DEPENDS ON T004)
- [X] T010 [US1] Implement `validate_data_completeness()` in `code/analysis/data_validator.py` to check for critical variables. **Specifics**: Logic: 'Exclude run if critical variables (throughput, latency) are missing; proceed with reduced model ONLY if non-critical covariates are missing'. **Specifics**: Flag runs where `packet_loss_rate` > 20%. If critical, exclude run. If non-critical, proceed with reduced model complexity (exclude packet_loss as a predictor). **Output**: Generate and save `code/data/processed/reduced_model_config.yaml` listing excluded predictors and a warning log entry. **CRITICAL**: If non-critical variables are missing, this task MUST ALSO filter the raw dataset and save a distinct artifact `code/data/processed/reduced_model_data.csv` containing only the runs with available non-critical variables, ensuring the 'reduced model' data is verifiable and reproducible (SC-006). (Required for SC-006). DEPENDS ON T008, T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Physical Testbed Orchestration & Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Deploy scheduler to physical mesh, inject network impairments, and collect raw execution logs (wall-clock, packets, CPU).

**Independent Test**: Launch a single benchmark job across multiple physical nodes with injected latency, verifying that the system distributes tasks, records `tcpdump` packet counts and `mpstat` CPU usage per node, and outputs a CSV file matching the schema defined in Key Entities.

### Mandatory Block: US1 Core Infrastructure (Atomic Execution Required)
*The following tasks MUST be completed in sequence before any other US1 tasks. T013a is the absolute prerequisite.*

- [ ] T013a [US1] Implement `node_manager.py` in `code/orchestrator/` to handle SSH connections, heartbeat pings, and device discovery. **Specifics**: Use `paramiko.SSHClient` with `SSH2` protocol, `timeout=2s`. Implement `discover_nodes(ip_list)`, `ping_node(ip, timeout=2)`, `reassign_task(task_id, new_ip)`. **Fail Loudly**: Raise `NodeDiscoveryError` if *all* nodes are unreachable. **Recovery**: Preserve `try/except` for *runtime* heartbeat monitoring to detect individual node dropouts and trigger re-assignment. Handle `AuthenticationException` and `SocketTimeout` explicitly. **Robustness**: Integrate re-queue logic for dropout events directly here.
- [X] T012 [US1] Implement `remote_tool_manager.py` in `code/orchestrator/` to verify required CLI tools on remote nodes. **Specifics**: Check for `tcpdump` and `mpstat` via `which`. **Fail Loudly**: If missing, raise `ToolMissingError` immediately. **Do NOT attempt installation**. The spec assumes tools are pre-configured. (DEPENDS ON T013a).
- [X] T014c [US1] Implement `remote_wall_clock_timer.py` in `code/orchestrator/` to capture wall-clock execution time on remote nodes. **Specifics**: Use SSH to start/stop timers on remote nodes to capture node-level wall-clock time, distinct from the benchmark's internal timing. Output `start_timestamp` and `end_timestamp` to the raw log. (DEPENDS ON T013a).
- [X] T014a [US1] Implement `instrumentor_remote.py` in `code/orchestrator/` to remotely execute `tcpdump` (packet counts) and `mpstat` (CPU usage) commands on target nodes via SSH. **Specifics**: Execute `tcpdump -c <count> -i any -n` and `mpstat <interval> 5`. Parse output to extract `packet_count` and `cpu_utilization_pct`. **Network Saturation**: Implement `check_network_saturation()` to detect >20% packet loss. **Logic**: If packet loss is critical (per SC-006), log the failure to `code/data/raw/abort_log.json` containing `{run_id, reason: 'network_saturation', packet_loss_pct, timestamp}` AND THEN abort the run. Do NOT discard the run silently. If packet loss is non-critical for the specific model configuration, flag as WARN and proceed with reduced model complexity (exclude packet_loss as a predictor). **Unmodeled Vars**: Implement `capture_unmodeled_vars()` to log thermal throttling and OS noise metrics (thermal_zone, loadavg). Handle remote execution failures by raising `RemoteExecutionError`. **Wall-Clock**: Ensure node-level wall-clock time is captured via remote start/stop timing (via T014c). **Dependency**: DEPENDS ON T012, T014c.
- [X] T014b [US1] Implement `mpstat_parser.py` in `code/orchestrator/` to parse raw `mpstat` output strings into the structured `cpu_utilization_pct` field of the `PhysicalNode` entity. DEPENDS ON T014a.
- [X] T015 [US1] Implement `scheduler.py` in `code/orchestrator/` to distribute `TaskChunk` units. **Specifics**: Implement `assign_chunk(chunk, node)`, `monitor_task(task_id)`. **RAM Check**: Query `free -m` via SSH to determine `available_ram`. **Adaptive Chunking**: Dynamically split `TaskChunk` units if `available_ram < chunk_size` (recursive splitting: `new_chunk_size = chunk_size / 2` until `new_chunk_size < available_ram`). **OOM Detection**: Implement `parse_oom_signals()` to detect OOM from remote logs and trigger re-assignment. **Straggler Handling**: Enforce a median task time limit. If `task_time > 2 * median`, re-assign task immediately and log "heterogeneity penalty". **Re-queue**: Integrate re-queue logic for heartbeat loss directly here. **Dependencies**: DEPENDS ON T013a, T012, T014a, T014b, T014c.
- [X] T016 [US1] Implement `benchmark.py` in `code/orchestrator/` to run the Monte Carlo integration workload on remote nodes. **Specifics**: Accept `chunk_size` and `iterations` as args. Output `wall_clock_time` and `ops_per_sec`. **Timeout Integration**: Explicitly invoke `enforce_pipeline_timeout()` from T009 at the start of execution. DEPENDS ON T013a.
- [X] T017 [US1] Implement `data_collector.py` in `code/orchestrator/` to aggregate raw logs from nodes and write to `code/data/raw/` as CSV. **Specifics**: Aggregate `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`. **Exclusion**: Exclude runs flagged as saturated by T014a (if critical). DEPENDS ON T014b, T014c, T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Scheduler & Granularity Parameter Sweep (Priority: P2)

**Goal**: Execute parameter sweep varying task chunk sizes (fine/medium/coarse), node counts (a range of values), and network conditions to generate dataset for "sweet spot" identification.

**Independent Test**: Run three distinct execution campaigns (fine, medium, coarse granularity) with identical node sets and network conditions, verifying that the output contains three distinct throughput measurements and that coordination overhead differs between them.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for parameter sweep configuration YAML in `code/tests/contract/test_sweep_config.py`
- [ ] T022 [P] [US2] Integration test for granularity variation impact on overhead ratio in `code/tests/integration/test_granularity_sweep.py`

### Implementation for User Story 2

- [ ] T050 [US2] Implement `granularity_sweeper_config.py` to define the exact "fine/medium/coarse" ranges and node count steps in a validated YAML config (`config/sweep_config.yaml`), ensuring the parameter sweep is reproducible and explicitly stated (Addresses US2 Acceptance Scenario 3).
- [ ] T023 [P] [US2] Implement `sweep_runner.py` in `code/orchestrator/` to iterate through combinations of node counts and granularity settings. **Specifics**: Load configuration from `config/sweep_config.yaml`. Execute `benchmark.py` for each combination. **Timeout Integration**: Explicitly invoke `enforce_pipeline_timeout()` from T009 into this flow. DEPENDS ON T017, T050, T009.
- [ ] T024 [US2] Implement `overhead_calculator.py` in `code/analysis/` to compute `coordination_overhead_ratio` (handshake time vs. compute time) per run
- [ ] T025a [US2] Implement `network_impairment_local.py` in `code/orchestrator/` as a local utility to define and calculate latency/packet loss parameters (Injection configuration).
- [ ] T025b [US2] Implement `remote_impairment_orchestrator.py` in `code/orchestrator/` to apply the calculated network impairments to remote nodes via SSH (e.g., executing `tc` commands) during the sweep. **Specifics**: Execute `tc qdisc add dev eth root netem delay [configurable]ms ms` and `tc qdisc add dev eth0 root netem loss [VALUE]`. **Note**: Replace `[VALUE]` with the value from `config/sweep_config.yaml` at runtime. DEPENDS ON T025a, T013a.
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

- [X] T030a [P] [US3] Implement `fit_mlr_with_interactions()` in `code/analysis/regression.py` using `statsmodels` to perform Multiple Linear Regression (required by FR-005/SC-001) modeling throughput as a function of heterogeneity, granularity, and injected latency. **Specifics**: Formula: `throughput ~ heterogeneity * granularity + injected_latency`. **MUST include interaction terms between heterogeneity and granularity**. **Output**: Save the fitted model object and summary statistics to `code/analysis/output/mlr_model.json` containing keys: `coefficients`, `p_values`, `r_squared`, `formula_string`. **CRITICAL**: This task is a HARD PREREQUISITE for the entire Phase 5 pipeline completion. It MUST produce `mlr_model.json` regardless of whether T035b selects GAM as the primary model. DEPENDS ON T010.
- [ ] T030b [P] [US3] Implement `fit_gam_with_interactions()` in `code/analysis/regression.py` using `pygam` to model throughput as a Generalized Additive Model (required by Plan.md methodological update). DEPENDS ON T010.
- [ ] T035b [US3] Implement `model_selector.py` in `code/analysis/` to compare MLR and GAM results. **Specifics**: Calculate AIC, BIC, and R² for both models. Select the model that best fits the "sweet spot" hypothesis (highest R² with parsimony) and log the selection rationale. **Preservation**: Ensure the mandatory MLR output (from T030a) is preserved as a distinct artifact (`mlr_model.json`) even if GAM is selected as primary. Output the chosen model as the primary `RegressionModel`. DEPENDS ON T030a, T030b.
- [ ] T031 [US3] Implement `anova_test.py` in `code/analysis/` to determine statistical significance (p < 0.05) of granularity differences
- [ ] T032 [US3] Implement `theoretical_bound.py` in `code/analysis/` to calculate Ong & Motani capacity limits AND **flag if empirical performance exceeds the theoretical limit** (Unified validation logic). **Specifics**: Implement `capacity = (N * W) / (* log_base(N))` where N=node_count, W=bw, using a logarithmic base consistent with the theoretical framework. Flag if `empirical > capacity`. DEPENDS ON T030a.
- [ ] T033 [US3] Implement `validation.py` in `code/analysis/` to compare empirical curves against theoretical bounds and flag violations (measurement errors). DEPENDS ON T032.
- [ ] T034 [US3] Implement `report_generator.py` in `code/analysis/` to output final `RegressionModel` JSON with coefficients, p-values, R², and deviation metrics. **Specifics**: Ensure output is validated against schema from T007 using `validate_json_against_schema()`. DEPENDS ON T035b, T033, T010, T007.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Simulation & Validation (Constitution Principle VI)

**Goal**: Build and calibrate a Discrete-Event Simulation (DES) model using the "Golden" physical dataset to validate internal state.

**Independent Test**: Run the DES model with parameters derived from physical runs and verify that the simulation output matches the physical data within a defined tolerance.

### Mandatory Block: Simulation Validation (Atomic Execution Required)
*The following tasks MUST be completed in sequence. T035a_GenPhys and T035a_GenMock provide the dataset, T035a_Select chooses it, and T037 calibrates.*

- [ ] T035a_GenPhys [US3] Implement `physical_validation_job.py` in `code/simulation/` to handle the mandatory physical validation. **Specifics**: This task MUST check for physical hardware availability. **Conditional Logic**: If physical hardware (a small cluster of local machines) is available, trigger a small-scale physical deployment to generate the "Golden Dataset". **CI Fallback**: If physical hardware is unavailable (e.g., in CI), generate a mock dataset in `code/data/raw/mock_golden.csv` with a specific header and a 'source: mock' flag, and log a WARNING to `code/logs/ci_fallback.log`. **Constraint**: This task MUST NOT use mock or loopback nodes if physical hardware is available. **Dependency**: DEPENDS ON T017 (if available) or triggers the physical run. **Constitution**: This is the ONLY valid source for the Golden Dataset required by Principle VI.
- [ ] T035a_GenMock [US3] Implement `ci_mock_bootstrap.py` in `code/simulation/` to generate a mock dataset for CI unit tests ONLY. **Specifics**: This is a fallback for unit testing when physical hardware is unavailable. It MUST NOT be used for the "Golden Dataset" required by Constitution Principle VI unless explicitly triggered by T035a_GenPhys as a fallback. **Warning**: Using this for calibration will fail Principle VI validation if physical data was available. DEPENDS ON T005.
- [ ] T035a_Verify [US3] Implement `golden_dataset_verifier.py` in `code/simulation/` to perform the **verification step** required by Constitution Principle III and VI. **Specifics**: After T035a_GenPhys generates raw logs (or mock data), this task MUST: 1) Calculate SHA-256 checksum of the raw dataset. 2) Record checksum in `state.yaml` under `artifact_hashes`. 3) Explicitly tag the dataset as "Golden" in metadata (or "Mock" if fallback). 4) Verify the dataset is distinct from any mock data generated by T035a_GenMock. 5) Raise `ValidationFailure` if checksum mismatch or if mock data is detected when physical data was expected. **Dependency**: DEPENDS ON T035a_GenPhys, T017.
- [ ] T035a_Select [US3] Implement `golden_dataset_selector.py` in `code/simulation/` to select the appropriate dataset for calibration. **Specifics**: **CRITICAL**: This task accepts input from EITHER T035a_GenPhys (if physical data exists) OR T035a_GenMock (if in CI and T035a_GenPhys fallback was triggered). **Dependency**: T035a_Select depends on (T035a_GenPhys OR T035a_GenMock). Ensure the selected dataset is passed to T037. **Dependency**: DEPENDS ON T035a_GenPhys, T035a_Verify, T035a_GenMock.
- [ ] T036 [P] [US3] Implement `des_model.py` in `code/simulation/` using `simpy` to model task scheduling, network latency, and node heterogeneity. **Specifics**: Create `TaskScheduler` and `Node` processes.
- [ ] T037 [US3] Implement `calibration.py` in `code/simulation/` to fit DES parameters against the `data/raw/` physical logs (the "Golden Dataset" generated by T035a_GenPhys and verified by T035a_Verify, or the mock dataset if in CI). **Specifics**: Optimize parameters (packet_loss_rate, CPU_variance) to **Minimize MSE** between simulation output and physical data. Use `scipy.optimize.minimize` with method='L-BFGS-B' and tolerance=1e-4. **Timeout Integration**: Explicitly invoke `enforce_pipeline_timeout()` from T009. **Dependency**: DEPENDS ON T036, T017, T035a_Select, T035a_Verify.
- [ ] T038 [US3] Implement `internal_state_validator.py` in `code/simulation/` to perform the **validation logic** required by Constitution Principle VI: compare DES outputs against the "Golden Dataset" to verify internal state fidelity and ensure no circular predictions. **Specifics**: If `abs(simulated - physical) > tolerance`, raise `ValidationFailure`. DEPENDS ON T037.
- [ ] T039 [US3] Ensure simulation extrapolation logic is documented and bounded by the validated parameter space

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` including `quickstart.md` for running the physical testbed
- [ ] T041 Code cleanup and refactoring of `orchestrator` and `analysis` modules
- [ ] T042 [P] Performance optimization for the specified CI limit

The research question is: How can we optimize performance under a constrained confidence interval? The method involves a systematic analysis of algorithmic efficiency. References: [Author et al., 2023] (doi:10.xxxx/xxxx). (parallelize sweep execution where possible)
- [ ] T043 [P] Additional unit tests for `tcpdump` and `mpstat` parsing logic in `tests/unit/`
- [ ] T044 Security hardening of SSH key handling: Implement `SSHKeyManager` class in `code/orchestrator/node_manager.py`
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T008 must complete before T007
 - T010 must complete before T030a/T030b
 - T007 must complete before T010 and T034
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Simulation (Phase 6)**: Depends on Phase 3 (US1) completion to have physical data for calibration (or mock data if in CI)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T013a must complete before T012, T014a, T014b, T014c, T015, T016
 - T012 must complete before T014a
 - T014c must complete before T014a
 - T014a must complete before T014b
 - T014b must complete before T017
 - T014c must complete before T017
 - T013a must complete before T015, T016
 - T015 must complete before T015d, T015e (Note: T015d/e removed as phantom tasks; logic integrated into T015)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - T050 must complete before T023
 - T009 must complete before T023a
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - T010 must complete before T030a/T030b
 - T030a must complete before T032, T035b
 - T032 must complete before T033, T034
 - T030a, T030b must complete before T035b
 - T007 must complete before T034
 - **T030a is a hard prerequisite for Phase 5 completion** (must produce mlr_model.json regardless of T035b outcome)
- **Simulation (Phase 6)**: Must wait for US1 to generate the "Golden Dataset" (or mock data in CI)
 - T035a_GenPhys must complete before T035a_Verify
 - T035a_Verify must complete before T035a_Select
 - **T035a_Select depends on (T035a_GenPhys OR T035a_GenMock)** (Explicit OR logic for CI path)
 - T035a_Select must complete before T037
 - T036 must complete before T037
 - T037 must complete before T038
- **Robustness (Phase 8)**: Merged into Phase 3 (US1) and Phase 2 (Foundational)

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
# Note: T014a (instrumentor) depends on T013a (node_manager) and T014c (wall_clock) and cannot run in parallel with them.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Mandatory Block: T013a-T017)
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
- **Timeout Enforcement**: T009 must be integrated into the main execution flow to enforce the 6-hour limit (FR-007) across all phases including simulation, with explicit handling for local physical runs.
- **Network Saturation**: T014a must detect >20% packet loss and handle it according to SC-006 (abort if critical, proceed with reduced model if non-critical) AND log the failure to `code/data/raw/abort_log.json`.
- **Data Validation**: T010 must exclude runs with critical missing variables (SC-006) AND generate `code/data/processed/reduced_model_config.yaml` AND `reduced_model_data.csv` for non-critical missing variables.
- **Interaction Terms**: T030a must include interaction terms between heterogeneity and granularity (FR-005) AND save `mlr_model.json` as a HARD PREREQUISITE.
- **Unified Validation**: T032 must calculate bounds AND flag violations (FR-006).
- **Unmodeled Variables**: T014a must capture thermal throttling and OS noise (Assumptions).
- **Strict Real Data**: T013a ensures no synthetic fallbacks exist for discovery, but preserves recovery for runtime dropouts.
- **Adaptive Chunking**: T015 ensures low-RAM devices do not crash the system by splitting chunks.
- **Straggler Handling**: T015e ensures the system does not hang on slow nodes.
- **Run Rejection**: T010 ensures saturated network runs are handled according to SC-006 (reduced model if possible).
- **Golden Dataset Validation**: T038 ensures the simulation model is validated against physical reality as required by Constitution Principle VI. T035a_Verify ensures the dataset itself is verified. T035a_GenPhys ensures the physical validation path is available, with a mock fallback for CI.
- **Model Selection**: T035b ensures the final regression model is chosen based on statistical criteria (AIC/BIC) AND preserves the mandatory MLR output.
- **Configurable Sweep**: T023 ensures experimental parameters are loaded from `config/sweep_config.yaml` rather than hardcoded.
- **Tool Verification**: T012 ensures remote nodes have the necessary tools before execution (and fails loudly if missing).
- **Physical Validation**: T035a_GenPhys ensures the simulation is validated against a small-scale physical deployment as required by Constitution Principle VI, with a mock fallback for CI. T035a_GenMock is for CI mocking only. T035a_Verify ensures the "Golden" status is verified.
- **Schema Validation**: T007 and T034 ensure the final `RegressionModel` JSON is structurally valid before being used in downstream analysis or reporting.
- **CI Mock Path**: T035a_Select explicitly allows T035a_GenMock as a valid input to bypass T035a_GenPhys in CI, ensuring the simulation pipeline is executable on free-tier runners without physical hardware.