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
- [X] T002 Initialize a Python project with `requirements.txt` (pinning `paramiko`, `scikit-learn`, `pandas`, `pygam`, `statsmodels`, `pytest`, `pyyaml`, `numpy`, `simpy`, `scipy`, `jsonschema`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools: Create `pyproject.toml` with ruff rules (E, W, F, I) and black line-length=88.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base configuration manager in `code/orchestrator/config.py` to load node lists, granularity settings, and CI timeouts
- [X] T005 [P] Implement mock SSH node generator in `code/tests/unit/mock_nodes.py` for CI unit tests (no real hardware dependency)
- [X] T006 [P] Setup logging infrastructure in `code/orchestrator/logger.py` to capture wall-clock timestamps and heartbeat events
- [X] T008 [P] Create data model classes in `code/orchestrator/models.py` for `PhysicalNode`, `TaskChunk`, and `ExecutionRun` entities
- [X] T007 [P] Implement schema validation framework in `code/tests/contract/` using `jsonschema` and `pyyaml` to validate `ExecutionRun` and `RegressionModel` structures. **Specifics**: Define YAML schemas in `code/tests/contract/schemas/execution_run.yaml` and `code/tests/contract/schemas/regression_model.yaml`. Implement a `validate_json_against_schema()` utility function that raises `ValidationError` on mismatch. **Dependency**: T008.
- [X] T009 [P] Implement `enforce_pipeline_timeout()` in `code/orchestrator/timeout_guard.py` to enforce a hard timeout for the entire execution, analysis, AND simulation calibration pipeline (Required for FR-007, SC-004). **Specifics**: This utility must be explicitly integrated into US1, US2, US3, and Phase 6 execution flows. (DEPENDS ON T004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Physical Testbed Orchestration & Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Deploy scheduler to physical mesh, inject network impairments, and collect raw execution logs (wall-clock, packets, CPU).

**Independent Test**: Launch a single benchmark job across multiple physical nodes with injected latency, verifying that the system distributes tasks, records `tcpdump` packet counts and `mpstat` CPU usage per node, and outputs a CSV file matching the schema defined in Key Entities.

### Mandatory Block: US1 Core Infrastructure (Atomic Execution Required)
*The following tasks MUST be completed in sequence before any other US1 tasks. T013a is the absolute prerequisite. T013b, T013c, T012, and T049 run in parallel after T013a. T014a and T014c run after T013b/T012/T049. T014b runs after T014a. T015b/c/d run after T013c/T014a. T017 runs after T014b.*

- [ ] T013a [US1] Implement `node_manager.py` in `code/orchestrator/` to handle SSH connections, heartbeat pings, and device discovery. **Specifics**:
 - **Discovery**: `discover_nodes(ip_list)` accepts a list of IP strings (e.g., `['192.168.1.10', '192.168.1.11']`).
 - **Output**: Returns a list of dictionaries: `[{'ip': '...', 'hostname': '...', 'status': 'online'/'offline'},...]`.
 - **Recovery**: This task handles ONLY *initial* discovery. Runtime heartbeat monitoring and re-assignment logic are handled in T013c.
 - **Fail Loudly**: Raise `NodeDiscoveryError` if *all* nodes are unreachable.
 - **Dependency**: None (Base task).
- [ ] T013b [US1] Implement `completion_feedback.py` in `code/orchestrator/` to handle the 'completion feedback' loop required by FR-001. **Specifics**: Implement `receive_task_status(node_id, task_id, status)` and `update_scheduler_state(task_id, status)`. **Dependency**: T013a. **Note**: This task updates the `SchedulerState` object defined in T008, not the full T015b instance.
- [ ] T013c [US1] Implement `heartbeat_monitoring.py` in `code/orchestrator/` to handle **heartbeat loss detection** and **re-assignment logic** mandated by FR-001. **Specifics**:
 - **Monitoring**: Continuously poll nodes for heartbeat signals.
 - **Detection**: If a heartbeat is missed for > `timeout_threshold`, mark the node as `unresponsive` and the associated task as `failed`.
 - **Re-assignment**: Trigger the re-queue of the failed task to the next available node and log the event.
 - **Output**: Raises `HeartbeatLostEvent` to be consumed by the scheduler (T015b).
 - **Dependency**: T013a.
- [ ] T012 [US1] Implement `remote_tools_manager.py` in `code/orchestrator/` to verify and install required CLI tools on remote nodes. **Specifics**:
 1. **Check**: Verify `tcpdump` and `mpstat` via `which`. Raise `ToolMissingError` if missing and cannot be installed.
 2. **Install**: If check fails, attempt `apt-get install` or `yum install` (with sudo prompt handling).
 3. **Context**: This task consolidates T012a and T012b for robustness. **Dependency**: T013a.
- [ ] T049 [US1] Implement `node_profiler.py` in `code/orchestrator/` to measure and record CPU details for heterogeneity calculation. **Specifics**:
 - **Execution**: Run `lscpu | grep 'CPU MHz'` (or `sysctl -n hw.cpufrequency` on macOS) to obtain `cpu_speed_mhz`. Additionally, extract the CPU model string via `grep 'model name' /proc/cpuinfo` (or `sysctl -n machdep.cpu.brand_string` on macOS) and store it as `cpu_model`.
 - **Output**: Return a dict `{'cpu_speed_mhz': float, 'cpu_model': str}`.
 - **Dependency**: T013a.
- [ ] T014a [US1] Implement `instrumentor_remote.py` in `code/orchestrator/` to remotely execute `tcpdump` (packet counts) and `mpstat` (CPU usage) commands on target nodes via SSH. **Specifics**:
 - **Execution**: Run `tcpdump -i any -nn -c 0` (continuous capture) and pipe output to a line‑counter that matches the strict regex `^\d{2}:\d{2}:\d{2}\.\d+` for packet timestamps. Count only lines matching this regex; if no lines match, raise `InstrumentationFailureError`.
 - **Parsing Logic**:
   - `tcpdump`: Use the above regex to count packets reliably across OSes.
   - `mpstat`: Parse the `Average` line (or the last interval) to extract `CPU%` (user+system). If missing, log a WARNING and set utilization to 0.
 - **Output**: Return a dict `{'packet_count': int, 'cpu_utilization_pct': float}`.
 - **Network Saturation Detection**: Implement `check_network_saturation()` that computes packet loss from `tcpdump` statistics; if loss >20 % raise `NetworkSaturationSignal` (sent to T014b). 
 - **Missing Tool Handling**: If `tcpdump` is missing after T012 attempts installation, raise `InstrumentationFailureError` to abort the run (per spec edge case). If `mpstat` is missing, log a WARNING and set CPU utilization to 0 but continue.
 - **Dependency**: T012.
- [ ] T014b [US1] Implement `network_saturation_handler.py` in `code/orchestrator/` to handle the abort logic. **Specifics**: Receive the `NetworkSaturationSignal` from T014a. **Action**:
 - **Terminate Remote Processes**: Send a SIGKILL to the benchmark process ID (captured during T016 start) on all active nodes.
 - **Verify Termination**: Poll the remote process list (e.g., `ps -p <pid>`) to confirm termination, retry up to 3 times with a 1‑second delay.
 - **Log Failure**: If termination fails, log an ERROR and raise `TerminationFailedError`.
 - **Abort Mechanism**: **Raise `NetworkSaturationError`** exception to signal the orchestrator (T017, T015b) to stop the pipeline and exclude the run.
 - **Update State**: Log the failure with error code `NETWORK_SATURATION` and abort the current run.
 - **Dependency**: T014a.
- [ ] T014c [US1] Implement `remote_wall_clock_timer.py` in `code/orchestrator/` to capture wall‑clock execution time on remote nodes. **Specifics**: Use SSH to start a high‑resolution timer before benchmark launch and stop it after completion. **Output**: Return the elapsed seconds and **format the output to match the CSV schema** defined in Key Entities (PhysicalNode, TaskChunk) with a `wall_clock_time` column. **Dependency**: T013a.
- [ ] T015a [US1] Implement `scheduler_setup.py` in `code/orchestrator/` to configure the scheduler logic. **Specifics**:
 - **Configuration**: Load chunk size, node list, and timeout settings.
 - **Dependency**: T013a, T013b, T009.
- [ ] T015b [US1] Implement `scheduler_execution.py` in `code/orchestrator/` to distribute `TaskChunk` units. **Specifics**:
 - **assign_chunk(chunk, node)**, **monitor_task(task_id)**.
 - **RAM Check**: Query `free -m` via SSH to determine `available_ram`.
 - **Adaptive Chunking Algorithm**:
   - Base Chunk Size: A fixed, predefined threshold suitable for the target storage architecture.
   - Minimum Chunk Size: 1 MB.
   - If `available_ram < chunk_size`, recursively halve the chunk until it fits (minimum 1 MB).
 - **OOM Detection**: Parse remote logs for OOM signals and trigger re‑assignment.
 - **Straggler Handling**: Implement an asynchronous timeout (e.g., `asyncio.wait_for`) that re‑assigns any task exceeding `A multiple of median_task_time`.
 - **Dependency**: T013a, T013b, T013c, T012, T014a, T014c, T009, T015a. **Note**: T014b is an async handler; T015b should catch `NetworkSaturationError` from T014b to stop scheduling.
- [ ] T016 [US1] Implement `benchmark.py` in `code/orchestrator/` to run the Monte Carlo integration workload on remote nodes. **Specifics**: Accept `chunk_size` and `iterations` as args. Output `wall_clock_time` and `ops_per_sec`. **Timeout Integration**: Invoke `enforce_pipeline_timeout()` at start. **Dependency**: T013a, T013b.
- [ ] T017 [US1] Implement `data_collector.py` in `code/orchestrator/` to aggregate raw logs from nodes and write to `code/data/raw/` as CSV. **Specifics**:
 - **Aggregation**: Compute run‑level `wall_clock_time` as the maximum of node‑level times (exclude missing nodes with a WARNING).
 - **Output Schema**: CSV columns: `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `run_id`, `cpu_speed_mhz`, `cpu_model`.
 - **Validation**: Verify `packet_count` matches parsed value from T014a; if a node is marked 'uninstrumented', set `packet_count` to -1 and log a WARNING.
 - **Exclusion**: **Check for `NetworkSaturationError` from T014b and `validation_status.json` from T010a**. Skip runs flagged as saturated or excluded.
 - **Dependency**: T016, T014a, T014c, T049, **T014b**, T010a.
 
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
- [ ] T023 [P] [US2] Implement `sweep_runner.py` in `code/orchestrator/` to iterate through combinations of node counts and granularity settings. **Specifics**: Load configuration from `config/sweep_config.yaml`. Execute `benchmark.py` for each combination. **Timeout Integration**: Invoke `enforce_pipeline_timeout()` from T009. **Dependency**: T017, T050, T009.
- [ ] T024 [US2] Implement `overhead_calculator.py` in `code/analysis/` to compute `coordination_overhead_ratio` (handshake time vs. compute time) per run.
- [ ] T025a [US2] Implement `network_impairment_local.py` in `code/orchestrator/` as a local utility to define and calculate latency/packet loss parameters (Injection configuration).
- [ ] T025b [US2] Implement `remote_impairment_orchestrator.py` in `code/orchestrator/` to apply the calculated network impairments to remote nodes via SSH (e.g., executing `tc` commands) during the sweep. **Specifics**:
   1. **Check**: Verify `tc` availability and root privileges on the remote node.
   2. **Execute**: If available, run `tc qdisc add dev eth0 root netem delay <latency>ms` and `tc qdisc add dev eth0 root netem loss <loss>%`.
   3. **Failure Condition**: If `tc` is unavailable (e.g., on macOS, Android, or non‑Linux systems), raise `NetworkImpairmentError` and abort the run. No software‑based simulation fallback is permitted.
   - **Dependency**: T025a, T013a.
- [ ] T026 [US2] Integrate `sweep_runner` with `data_collector` to ensure every run is tagged with `node_count`, `granularity`, and `injected_latency` in the output CSV.
- [ ] T027 [US2] Implement `straggler_detector.py` in `code/orchestrator/` to identify high‑variance completion times and log "heterogeneity penalty" metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Theoretical Validation (Priority: P3)

**Goal**: Perform multiple linear regression (MLR) and ANOVA on physical data; validate against Ong & Motani theoretical bounds. (Note: Plan.md adds GAM as a methodological update; tasks must implement BOTH to satisfy FR-005 and Plan).

**Independent Test**: Feed physical execution logs into the analysis module and verify that the system outputs a regression model object containing an R² value, p‑values for interaction terms, and a comparison metric against the theoretical capacity bound.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for `RegressionModel` JSON output schema in `code/tests/contract/test_regression_schema.py`
- [ ] T029 [P] [US3] Integration test for theoretical bound calculation sanity check in `code/tests/integration/test_bound_validation.py`

### Implementation for User Story 3

- [ ] T010a [US3] Implement `validate_data_completeness()` in `code/analysis/data_validator.py` to check for critical variables. **Specifics**:
   - **Critical Variables**: `throughput`, `latency` (injected).
   - **Non‑Critical Variables**: `packet_loss_rate`, `thermal_zone`, `loadavg`.
   - **Step 1**: If any critical variable is missing, **write `validation_status.json` with `status: 'excluded'`** and log an error. **Exclude the run from downstream processing**.
   - **Step 2**: If non‑critical variables are missing, FLAG a WARN and proceed with a reduced model (exclude those predictors).
   - **Output**: `validation_status.json` with schema `{"critical_missing": [...], "non_critical_missing": [...], "excluded_terms": [...], "warnings": [...], "status": "excluded|valid"}`.
   - **Dependency**: T017.
- [ ] T010b [US3] Implement `dynamic_formula_configurator()` in `code/analysis/data_validator.py` to generate the regression configuration object based on T010a's output. **Specifics**:
   - **Input**: `validation_status.json`. **Check `status`**: If `excluded`, **abort processing for this run**.
   - **Logic**: Start with base formula `throughput ~ heterogeneity * granularity + injected_latency`. Remove any terms involving variables listed in `excluded_terms`.
   - **Variable Encoding**:
     - `heterogeneity`: Coefficient of variation of CPU speeds (from T049) across nodes.
     - `granularity`: Categorical dummy variables (fine, medium, coarse).
     - `injected_latency`: Continuous numeric value.
   - **Output**: Configuration object listing included terms.
   - **Dependency**: T010a.
- [ ] T051 [US3] Implement `dynamic_formula_builder.py` in `code/analysis/` to construct the final `statsmodels` formula string. **Specifics**:
   - **Input**: Configuration object from T010b.
   - **Action**: Build a formula string, automatically pruning interaction terms for any missing variables.
   - **Output**: String ready for `statsmodels` fitting (e.g., `"throughput ~ C(granularity) * heterogeneity + injected_latency"`).
   - **Dependency**: T010b.
- [ ] T030a [P] [US3] Implement `fit_mlr_with_interactions()` in `code/analysis/regression.py` using `statsmodels`. **Specifics**:
   - **Formula**: Use the string generated by T051.
   - **Must include** interaction terms between heterogeneity and granularity.
   - **Output**: Save fitted model to `code/analysis/output/mlr_model.json` containing `coefficients`, `p_values`, `r_squared`, `formula_string`.
   - **Dependency**: T051, T017.
- [ ] T030b [P] [US3] Implement `fit_gam_with_interactions()` in `code/analysis/regression.py` using `pygam`. **Dependency**: T051.
- [ ] T035b [US3] Implement `model_selector.py` in `code/analysis/` to compare MLR and GAM results. **Specifics**: Compute AIC, BIC, and R² for both models; select the model with highest R² while respecting parsimony. Log rationale. **Output**: JSON specifying `selected_model` (`mlr` or `gam`) and the metrics for both. **Critical**: Must NOT suppress the MLR artifact; both model files remain on disk. **Dependency**: T030a, T030b.
- [ ] T031 [US3] Implement `anova_test.py` in `code/analysis/` to determine statistical significance (p < 0.05) of granularity differences.
- [ ] T032 [US3] Implement `theoretical_bound.py` in `code/analysis/` to calculate Ong & Motani capacity limits AND **calculate the deviation metric** between empirical and theoretical curves. **Specifics**: Use the capacity formula from Ong & Motani (2007) with measured bandwidth and SNR; output `theoretical_capacity`, `empirical_throughput`, `deviation_metric`; flag if empirical > capacity. **Dependency**: T030a.
- [ ] T033 [US3] Implement `validation.py` in `code/analysis/` to compare empirical curves against theoretical bounds and flag violations (measurement errors). **Dependency**: T032.
- [ ] T039a [US3] Implement `validate_extrapolation_bounds()` in `code/analysis/` to identify the "sweet spot" where coordination overhead is minimized. **Specifics**:
   - Compute derivative of throughput vs. node count (or granularity).
   - Sweet spot = point where marginal gain < predefined threshold.
   - Input: Aggregated throughput data from T023.
   - Output: `extrapolation_check.json` with identified parameters.
   - **Dependency**: T023, T024, T017.
- [ ] T034 [US3] Implement `report_generator.py` in `code/analysis/` to output final `RegressionModel` JSON. **Specifics**:
   - **Read** `mlr_model.json` (from T030a) and `gam_model.json` (from T030b) directly from disk.
   - **Validate** against schema from T007.
   - **Verify** that interaction terms (`heterogeneity:granularity`) are present.
   - **Mandatory Output**: The final JSON **MUST include** `mlr_coefficients`, `mlr_p_values`, and `mlr_r_squared` as primary fields, regardless of the selected model, to satisfy FR-005.
   - **Dependency**: T030a, T030b, T035b, T032, **T033**, T007. **Note**: T034 must consume T033's validation result to ensure the report includes the validation status.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Simulation & Validation (Constitution Principle VI)

**Goal**: Build and calibrate a Discrete‑Event Simulation (DES) model using the "Golden" physical dataset to validate internal state.

**Independent Test**: Run the DES model with parameters derived from physical runs and verify that the simulation output matches the physical data within a defined tolerance.

### Mandatory Block: Simulation Validation (Atomic Execution Required)
*The following tasks MUST be completed in sequence. T035a determines the path. T035b produces the Golden Dataset. T037 calibrates.*

- [ ] T035a [US3] Implement `ci_validation_gate.py` in `code/simulation/` to handle the CI environment detection. **Specifics**:
   - **Context Check**: If environment variable `PHYSICAL_VALIDATION=1` is set, proceed to generate the Golden Dataset (T035b). 
   - If not set, **raise `PhysicalValidationRequiredError`** (do not proceed with mock data) to enforce Constitution Principle VI. The pipeline must fail if physical hardware is unavailable for the mandatory validation step.
   - **Dependency**: None.
- [ ] T035b [US3] Implement `physical_validation_job.py` in `code/simulation/` to handle the mandatory physical validation when `PHYSICAL_VALIDATION=1`. **Specifics**:
   - **Action**: Run a small-scale physical deployment (a limited number of nodes) by invoking `benchmark.py` (T016) and `data_collector.py` (T017) with `run_id=golden_dataset`.
   - **Output**: Produce `code/data/raw/golden_dataset.csv`.
   - **Behavior**: If hardware is unavailable while `PHYSICAL_VALIDATION=1`, raise `PhysicalHardwareUnavailableError` with a clear message; CI will treat this as a failure of the manual validation step, not of the overall pipeline.
   - **Dependency**: T017, T016.
- [ ] T036 [P] [US3] Implement `des_model.py` in `code/simulation/` using `simpy` to model task scheduling, network latency, and node heterogeneity. **Specifics**: Create `TaskScheduler` and `Node` processes.
- [ ] T037 [US3] Implement `calibration.py` in `code/simulation/` to fit DES parameters against the `code/data/raw/golden_dataset.csv`. **Specifics**:
   - **Input**: Must read `golden_dataset.csv`; if the file is missing, raise `CalibrationDataMissingError`.
   - **Flag Check**: **Check `skip_golden` flag from T035a**. If `skip_golden=True`, **raise `CalibrationSkippedError`** (do not proceed with mock data).
   - **Optimization**: Adjust parameters (e.g., `packet_loss_rate`, `cpu_variance`) to minimize MSE between simulation output and physical data.
   - **Convergence Criterion**: Maintain a deque of the last 5 MSE values. After each iteration compute `relative_change = abs(current - value_5_steps_ago) / value_5_steps_ago`. Stop when `relative_change < 1e-4` for five consecutive checks or after `max_iterations = 1000`.
   - **Timeout Integration**: **Invoke `enforce_pipeline_timeout()` from T009** to ensure the calibration phase respects the CI limit.
   - **Dependency**: T036, T035a.
- [ ] T038 [US3] Implement `internal_state_validator.py` in `code/simulation/` to compare DES outputs against the Golden Dataset. **Specifics**: Compute MSE, Pearson correlation; if `abs(simulated - physical) > tolerance` (tolerance = 0.05 × mean physical), raise `ValidationFailure`. Output `validation_report.json` with metrics and pass/fail status.

---

## Phase 7: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` including `quickstart.md` for running the physical testbed
- [ ] T040a [P] Write `docs/simulation_extrapolation.md` to explicitly document the simulation extrapolation logic, bounds, and validation approach. **Specifics**: Explain sweet‑spot detection and limits enforced by T039a.
- [ ] T041 Code cleanup and refactoring of `orchestrator` and `analysis` modules
- [ ] T042 [P] Performance optimization for the CI limit (parallelize sweep execution where possible). **Specifics**: Ensure T037 (calibration) and T023 (sweep) respect the hard timeout enforced by T009.
- [ ] T043 [P] Additional unit tests for `tcpdump` and `mpstat` parsing logic in `tests/unit/`. **Specifics**: Create `test_tcpdump_parsing.py` to verify the strict regex logic in T014a against known `tcpdump` outputs.
- [ ] T044 Security hardening of SSH key handling: Implement `SSHKeyManager` class in `code/orchestrator/node_manager.py`
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility

The research question is whether parallelizing sweep execution can effectively reduce continuous integration turnaround time. The method involves analyzing parallelization strategies for CI workflows. References: [Citation Placeholder].

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T008 must complete before T007
 - T010a must complete before T010b
 - T010b must complete before T051
 - T051 must complete before T030a/T030b
 - T007 must complete before T034
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Simulation (Phase 6)**: Depends on Phase 3 (US1) completion to have physical data for calibration (or manual run).
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T013a must complete before T013b, T013c, T012, T014a, T014c, T015a, T015b, T016
 - T012 must complete before T014a
 - T014a must complete before T014b
 - T013a must complete before T014c
 - T014b must complete before T017
 - T014c must complete before T017
 - T013b must complete before T015b, T016
 - T013c must complete before T015b
 - **Critical Path**: T012 → T014a → T014b → T015b
 - T017 must complete before T010a
 - T010a must complete before T010b
 - T010b must complete before T051
 - T051 must complete before T030a/T030b
 - T009 must complete before T015b
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - T050 must complete before T023
 - T009 must complete before T023
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - T010a must complete before T010b
 - T010b must complete before T051
 - T051 must complete before T030a/T030b
 - T030a must complete before T032, T035b
 - T032 must complete before T033, T034
 - T030a, T030b must complete before T035b
 - T007 must complete before T034
 - T017 must complete before T034
 - **T035b is the hard prerequisite for Phase 5 completion** (must route MLR/GAM objects to T034)
- **Simulation (Phase 6)**: Must wait for US1 to generate the "Golden Dataset" (or manual run) before calibration.
 - T035a must complete before T037
 - T036 must complete before T037
 - T037 depends on existence of golden dataset; will raise if missing.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **except** where dependencies exist (T008 -> T007, T010a -> T010b)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Mandatory Block: T013a‑T017)
4. **STOP and VALIDATE**: Test User Story 1 independently (collect real logs from a small cluster)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Orchestration & Data)
 - Developer B: User Story 2 (Sweep & Overhead)
 - Developer C: User Story 3 (Analysis & Bounds)
3. Stories complete and integrate independently without breaking previous stories

### Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **Data Hygiene**: Ensure all raw logs in `code/data/raw/` are preserved unchanged; derived stats go to `code/data/processed/`.
- **Real Data**: All analysis tasks must consume the REAL dataset generated by US1. Do not fabricate data for the regression model.
- **CI Limit**: The full parameter sweep (multiple runs) must be optimized to fit within the CI time limit.; if physical hardware is unavailable, use the mock node generator for unit tests only.
- **Timeout Enforcement**: T009 must be integrated into the main execution flow to enforce the ‑hour limit across all phases including simulation.
- **Network Saturation**: T014a must detect >20 % packet loss and signal T014b to abort (not just flag) as per Edge Cases.
- **Data Validation**: T010a must exclude runs with critical missing variables, and T010b must dynamically prune the formula. T051 must implement the formula construction. T052 has been merged into T051.
- **Interaction Terms**: T030a must include interaction terms between heterogeneity and granularity. T035b must preserve the MLR artifact regardless of selection.
- **Unified Validation**: T032 must calculate bounds AND output a deviation metric (FR‑006/SC‑002) with explicit formula and assumptions.
- **Unmodeled Variables**: T014a must capture thermal throttling and OS noise on a best‑effort basis (Assumptions).
- **Strict Real Data**: T013a ensures no synthetic fallbacks exist for discovery, but preserves recovery for runtime dropouts.
- **Adaptive Chunking**: T015 ensures low‑RAM devices do not crash the system by splitting chunks (min 1 MB).
- **Straggler Handling**: T015 ensures the system does not hang on slow nodes via **asynchronous timeout**.
- **Run Rejection**: T010a ensures saturated network runs are handled according to SC‑006, flagging them as invalid.
- **Golden Dataset Validation**: T038 ensures the simulation model is validated against a physical dataset as required by Constitution Principle VI. T035a ensures the correct dataset source is selected for CI or local runs, failing if physical hardware is missing.
- **Model Selection**: T035b ensures the final regression model is chosen based on statistical criteria (AIC/BIC) AND preserves the mandatory MLR output.
- **Configurable Sweep**: T023 ensures experimental parameters are loaded from `config/sweep_config.yaml` rather than hardcoded.
- **Tool Verification**: T012 ensures remote nodes have the necessary tools before execution.
- **Physical Validation**: T035a ensures a physical validation strategy (manual run) exists, satisfying the Constitution without blocking CI.
- **Schema Validation**: T007 and T034 ensure the final `RegressionModel` JSON is structurally valid before being used in downstream analysis or reporting.
- **Calibration Fallback**: T037 defines explicit error states for calibration failure.
- **Mock Data Prohibition**: T037 explicitly forbids the use of T035c for calibration, preserving Constitution Principle VI.
- **Constraint Preservation**: All tasks now respect FR/SC levels; no weakening of requirements.