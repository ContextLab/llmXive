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

- [ ] T001 [P] Create project structure per implementation plan: `code/orchestrator`, `code/analysis`, `code/simulation`, `code/data/raw`, `code/data/processed`, `code/tests/unit`, `code/tests/integration`, `code/tests/contract`. Include `__init__.py` in all directories and a `.gitignore` excluding `data/`, `*.log`, `__pycache__`. **Specifics**: Create `code/.gitignore` with content: `data/`, `*.log`, `__pycache__/`, `*.pyc`, `.env`, `venv/`, `.pytest_cache/`. **Reference**: `plan.md` Project Structure.
- [X] T002 Initialize a Python project with `requirements.txt` (pinning `paramiko`, `scikit-learn`, `pandas`, `pygam`, `statsmodels`, `pytest`, `pyyaml`, `numpy`, `simpy`, `scipy`, `jsonschema`, `iperf3`)
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
- [X] T009 [P] Implement `enforce_pipeline_timeout()` in `code/orchestrator/timeout_guard.py` to enforce a hard timeout for the entire execution, analysis, and simulation pipeline (Required for FR-007, SC-004). **Specifics**: This utility must be explicitly integrated into US1, US2, US3, and Phase 6 execution flows. (DEPENDS ON T004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Physical Testbed Orchestration & Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Deploy scheduler to physical mesh, inject network impairments, and collect raw execution logs (wall-clock, packets, CPU).

**Independent Test**: Launch a single benchmark job across multiple physical nodes with injected latency, verifying that the system distributes tasks, records `tcpdump` packet counts and `mpstat` CPU usage per node, and outputs a CSV file matching the schema defined in Key Entities.

### Strict Execution DAG

**Note**: The following sequence must be respected. Tasks must be executed in this order to ensure data availability and logical consistency.

1.  **T013a** (Node Discovery) must run first.
2.  **T012** (Tool Verification) depends on T013a.
3.  **T049** (CPU Profiling) and **T048** (Radio Metrics) depend on T012 and T013a.
4.  **T052** (Thermal Monitoring) depends on T012 and T013a.
5.  **T014a** (Instrumentation) depends on T012 and T013a.
6.  **T014c** (Wall Clock) depends on T012 and T013a.
7.  **T013d** (Scheduler State) depends on T008 (Models) and T004 (Config).
8.  **T013b** (Completion Feedback) depends on T013a and T013d.
9.  **T013c** (Heartbeat & Re-assignment) depends on T013a, T013d, T049, T014a, T014c, T052.
10. **T015a** (Scheduler Setup) depends on T013a, T013b, T013d, T009.
11. **T015b** (Scheduler Execution) depends on T013a, T013b, T013c, T012, T014a, T014c, T015a, T013d, T014b, T052.
12. **T016** (Benchmark) depends on T013a, T013b.
13. **T017** (Data Collector) depends on T016, T014a, T014c, T049, T048, T052, T013c.

### Implementation for User Story 1

- [ ] T013a [US1] Implement `node_manager.py` in `code/orchestrator/` to handle SSH connections, heartbeat pings, and device discovery. **Specifics**:
 - **Discovery**: `discover_nodes(ip_list)` accepts a list of IP strings (e.g. `['192.168.1.10', '192.168.1.11']`).
 - **Output**: Returns a list of dictionaries: `[{'ip': '...', 'hostname': '...', 'status': 'online'/'offline'/'unreachable'},...]`. **Explicitly define enum values for 'status'**: 'online', 'offline', 'unreachable'.
 - **Recovery**: This task handles ONLY *initial* discovery. Runtime heartbeat monitoring and re-assignment logic are handled in T013c.
 - **Fail Loudly**: Raise `NodeDiscoveryError` if *all* nodes are unreachable.
 - **Timeout Definition**: Use `ssh -o ConnectTimeout=5 ` to determine status.
 - **Status Logic**: 'offline' = SSH timeout (5s); 'unreachable' = ICMP ping failure.
 - **Dependency**: T004 (config).

- [ ] T012 [US1] Implement `remote_tools_manager.py` in `code/orchestrator/` to verify and install required CLI tools on remote nodes. **Specifics**:
 1. **Check**: Verify `tcpdump`, `mpstat`, `iwlist`/`iw`, `iperf3` via `which`. Raise `ToolMissingError` if missing and cannot be installed.
 2. **Install**: If check fails, attempt `apt-get install` or `yum install` (with sudo prompt handling).
 3. **Context**: This task consolidates T012a and T012b for robustness. **Dependency**: T013a.

- [ ] T049 [US1] Implement `node_profiler.py` in `code/orchestrator/` to measure and record CPU details for heterogeneity calculation. **Specifics**:
 - **Execution**: Run `lscpu | grep 'CPU MHz'` (or `sysctl -n hw.cpufrequency` on macOS) to obtain `cpu_speed_mhz`. Additionally, extract the CPU model string via `grep 'model name' /proc/cpuinfo` (or `sysctl -n machdep.cpu.brand_string` on macOS) and store it as `cpu_model`.
 - **Output**: Return a dict `{'cpu_speed_mhz': float, 'cpu_model': str}`.
 - **Dependency**: T013a, T012.

- [ ] T048 [US1] Implement `radio_metrics_collector.py` in `code/orchestrator/` to **measure** `snr_db` and `bandwidth_Mbps` for theoretical bound validation (FR-006). **Specifics**:
 - **SNR Measurement**:
 - **Primary**: Run `iwlist <interface> scan | grep -E 'Signal level|Noise level'` on the primary Wi-Fi interface. Calculate `snr_db = signal_level - noise_level`.
 - **Fallback 1**: If `iwlist` fails, run `iw dev <interface> link | grep signal`.
 - **Fallback 2**: If `iw` fails, parse `/proc/net/wireless`.
 - **Error Handling**: If all fail, log a WARNING and set `snr_db` to `null` (non-critical, per SC-006). Do NOT raise `RadioMetricError`.
 - **Bandwidth Measurement**: Run `iperf -c <peer_ip> -t [duration] -J` to measure throughput in Mbps.
 - **Output**: Return a dict `{'snr_db': float or null, 'bandwidth_Mbps': float}`.
 - **Dependency**: T012, T013a.

- [ ] T052 [US1] Implement `thermal_monitor.py` in `code/orchestrator/` to detect thermal throttling indicators. **Specifics**:
 - **Execution**: Check `/sys/class/thermal/thermal_zone*/temp` or `lscpu` for thermal info.
 - **Platform Handling**: If thermal interface is missing (e.g., Raspberry Pi without sensors), log a 'thermal_sensor_missing' warning, set `thermal_throttling_detected` to `false`, and proceed. Do NOT raise an error.
 - **Output**: Return a dict `{'thermal_throttling_detected': bool, 'thermal_status': 'normal'/'throttled'/'unknown'}`.
 - **Dependency**: T012, T013a.

- [ ] T014a [US1] Implement `remote_instrumentor.py` in `code/orchestrator/` to remotely execute `tcpdump` (packet counts) and `mpstat` (CPU usage) commands on target nodes via SSH. **Specifics**:
 - **Execution**: Run `tcpdump -i any -nn -c 0` (continuous capture) and pipe output to a line‑counter.
 - **Parsing Logic**:
 - `tcpdump`: Support multiple timestamp formats (absolute `HH:MM:SS.sss` via regex `r'\d{2}:\d{2}:\d{2}\.\d{3}'` and relative `delta` via regex `r'^\d+\.\d+\s+'`). Detect format automatically. Count lines matching timestamps. If no lines match, raise `InstrumentationFailureError`.
 - `mpstat`: Parse the `Average` line (or the last interval) to extract `CPU%` (user+system).
 - **Strict Error Handling (Critical vs Non-Critical)**:
 - **Critical Tools (tcpdump)**: If `tcpdump` is missing after T012 attempts installation, **raise `InstrumentationInstallationFailedError`** immediately if installation failed, or `InstrumentationError` if tool was missing initially. **Do NOT set packet count to 0**.
 - **Critical Tools (mpstat)**: If `mpstat` is missing after T012 attempts installation, **raise `CriticalVariableMissingError`** (per SC-006). **Do NOT set CPU utilization to null**; the run must be excluded immediately.
 - **Network Saturation Detection**: Implement `check_network_saturation()` that computes packet loss using `ip -s link show <interface>` (parse the `RX` and `TX` drop/err fields). If loss >20 % raise `NetworkSaturationException` (sent to T014b).
 - **Output**: Return a dict `{'packet_count': int, 'cpu_utilization_pct': float}`.
 - **Dependency**: T012, T013a.

- [ ] T014b [US1] Implement `network_saturation_handler.py` in `code/orchestrator/` to handle the abort logic. **Specifics**: Receive the `NetworkSaturationException` from T014a. **Action**:
 - **Terminate Remote Processes**: Send a SIGKILL to the benchmark process ID (captured during T016 start) on all active nodes.
 - **Verify Termination**: Poll the remote process list (e.g. `ps -p <pid>`) to confirm termination, retry up to 3 times with a 1‑second delay.
 - **Log Failure**: If termination fails, log an ERROR and raise `TerminationFailedError`.
 - **Abort Mechanism**: **Raise `NetworkSaturationException`** exception to signal the orchestrator (T015b) to stop the pipeline and exclude the run.
 - **Update State**: Log the failure with error code `NETWORK_SATURATION` to `data/raw/validation_status.json`.
 - **Dependency**: T014a.

- [ ] T014c [US1] Implement `remote_wall_clock_timer.py` in `code/orchestrator/` to capture wall‑clock execution time on remote nodes. **Specifics**: Use SSH to start a high‑resolution timer before benchmark launch and stop it after completion. **Output**: Return the elapsed seconds and **format the output to match the CSV schema** defined in Key Entities (PhysicalNode, TaskChunk) with a `wall_clock_time` column. **Dependency**: T012, T013a.

- [ ] T013d [US1] Implement `scheduler_state_manager.py` in `code/orchestrator/` to manage the global state of the scheduler. **Specifics**:
 - **State Object**: Maintain a dictionary of `task_id` -> `node_id`, `status`, `start_time`, `end_time`.
 - **Methods**: `get_available_nodes()`, `assign_task(task_chunk, node_id)`, `get_task_status(task_id)`.
 - **Dependency**: T008 (Models), T004 (Config).

- [ ] T013b [US1] Implement `completion_feedback.py` in `code/orchestrator/` to handle the 'completion feedback' loop required by FR-001. **Specifics**: Implement `receive_task_status(node_id, task_id, status)` and `update_scheduler_state(task_id, status)`. **Dependency**: T013a, T013d.

- [ ] T013c [US1] Implement `heartbeat_monitoring.py` in `code/orchestrator/` to handle **heartbeat loss detection** and **heterogeneity-aware re-assignment logic** mandated by FR-001 and Constitution Principle VII. **Specifics**:
 - **Monitoring**: Continuously poll nodes for heartbeat signals.
 - **Detection**: If a heartbeat is missed for > `timeout_threshold`, mark the node as `unresponsive` and the associated task as `failed`.
 - **Re-assignment**: **Explicitly implement the heterogeneity-aware re-assignment algorithm**:
 1. Identify the failed task chunk.
 2. Query the `SchedulerState` (T013d) for the list of currently available/online nodes.
 3. Calculate a **heterogeneity score** for each available node: `score = (cpu_speed_mhz / max_latency_ms) * (1 - packet_loss_rate) `.
 - `cpu_speed_mhz`: From T049 (current CPU speed, used as **initial baseline**).
 - `max_latency_ms`: From a **rolling window of the last 5 heartbeat response times** (updated every 1 second).
 - `packet_loss_rate`: From T014a (current packet loss rate, used as **initial baseline**).
 4. Select the node with the **highest score**.
 5. Re-queue the task chunk to the new node.
 6. Log the re-assignment event with a timestamp.
 - **Dropout Rate Calculation**: **Explicitly calculate `dropout_rate` per run**: Count total heartbeat losses / total task assignments. Write this rate to `data/raw/dropout_events.json` with `run_id`, `dropout_rate`, and list of `dropped_node_ids`. **This metric is required as a covariate for the regression model (SC-006).**
 - **Output**: Raises `HeartbeatLostEvent` to be consumed by the scheduler (T015b).
 - **Dependency**: T013a, T013d, T049, T014a, T014c, T052.

- [ ] T015a [US1] Implement `scheduler_setup.py` in `code/orchestrator/` to configure the scheduler logic. **Specifics**:
 - **Configuration**: Load chunk size, node list, and timeout settings.
 - **Dependency**: T013a, T013b, T013d, T009.

- [ ] T015b [US1] Implement `scheduler_execution.py` in `code/orchestrator/` to distribute `TaskChunk` units. **Specifics**:
 - **assign_chunk(chunk, node)**, **monitor_task(task_id)**.
 - **RAM Check**: Query `free -m` via SSH to determine `available_ram`.
 - **Adaptive Chunking Algorithm**:
 - **Configuration**: Load `base_chunk_size` and `min_chunk_size` from `config/sweep_config.yaml`.
 - If `available_ram < chunk_size`, recursively halve the chunk until it fits (minimum 1 MB).
 - **OOM Detection**: Parse remote logs for OOM signals and trigger re‑assignment.
 - **Straggler Handling**: Implement an asynchronous timeout (e.g. `asyncio.wait_for`) that re‑assigns any task exceeding a significant multiple of the median task time.
 - **Exception Handling**: **Catch `NetworkSaturationException` raised by T014a/T014b** to stop scheduling.
 - **Dependency**: T013a, T013b, T013c, T012, T014a, T014c, T015a, T013d, T014b, T052.

- [ ] T016 [US1] Implement `benchmark.py` in `code/orchestrator/` to run the Monte Carlo integration workload on remote nodes. **Specifics**: Accept `chunk_size` and `iterations` as args. Output `wall_clock_time` and `ops_per_sec`. **Timeout Integration**: Invoke `enforce_pipeline_timeout()` at start. **Dependency**: T013a, T013b.

- [ ] T017 [US1] Implement `data_collector.py` in `code/orchestrator/` to aggregate raw logs from nodes and write to `code/data/raw/` as CSV. **Specifics**:
 - **Aggregation**: Compute run‑level `wall_clock_time` as the maximum of node‑level times.
 - **Exclusion Logic**: **Exclude nodes with `packet_count == -1` (uninstrumented) or `status == uninstrumented` from the max calculation**; treat missing nodes (no data) as excluded with WARNING.
 - **Output Schema**: CSV columns: `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `run_id`, `cpu_speed_mhz`, `cpu_model`, `snr_db`, `bandwidth_Mbps`, `dropout_rate`, `thermal_throttling_detected`.
 - **Null Handling**: **Explicitly write `null` for `snr_db` and `bandwidth_Mbps` if T048 failed**. Do NOT write 0 or -1.
 - **Validation**: Verify `packet_count` matches parsed value from T014a; if a node is marked 'uninstrumented', set `packet_count` to -1 and log a WARNING.
 - **Exclusion**: **Check for `NETWORK_SATURATION` in `data/raw/validation_status.json` written by T014b** (or read `validation_status.json` written by T014d). Skip runs flagged as saturated.
 - **Dependency**: T016, T014a, T014c, T049, T048, T052, T013c.

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
- [ ] T023 [US2] Implement `sweep_runner.py` in `code/orchestrator/` to iterate through combinations of node counts and granularity settings. **Specifics**: Load configuration from `config/sweep_config.yaml`. Execute `benchmark.py` for each combination. **Timeout Integration**: Invoke `enforce_pipeline_timeout()` from T009. **Dependency**: T017, T050, T009.
- [ ] T024 [US2] Implement `overhead_calculator.py` in `code/analysis/` to compute `coordination_overhead_ratio`. **Specifics**:
 - **Formula**: `coordination_overhead_ratio = handshake_time / total_execution_time`.
 - **Data Sources**: `handshake_time` from scheduler logs (T015b), `total_execution_time` from `wall_clock_time` (T014c).
 - **Output**: Append `coordination_overhead_ratio` to the aggregated CSV.
 - **Dependency**: T023, T017.
- [ ] T025 [US2] Implement `network_impairment_orchestrator.py` in `code/orchestrator/` to apply network impairments across the heterogeneous testbed (Linux, macOS, Android) for FR-003 compliance. **Specifics**:
 1. **Interface Detection**: Dynamically detect the primary network interface using `ip route | grep default | awk '{print $5}'` (Linux) or equivalent for other OS.
 2. **Platform-Specific Execution**:
 - **Linux**: If `tc` is available, run `tc qdisc add dev <interface> root netem delay <latency>ms` and `tc qdisc add dev <interface> root netem loss <loss>%`.
 - **macOS**: Use `pfctl` to apply latency/packet loss rules.
 - **Android**: Use a mobile-specific bridge/app API (documented in `quickstart.md`) to apply impairments.
 3. **Failure Condition**: If the platform-specific tool is unavailable, **raise `NetworkImpairmentRequiredError`**. **Do NOT skip impairment**. This ensures the experiment runs with injected latency as required by US-1 Acceptance Scenario 1.
 - **Dependency**: T050 (config), T013a.
- [ ] T026 [US2] Integrate `sweep_runner` with `data_collector` to ensure every run is tagged with `node_count`, `granularity`, and `injected_latency` in the output CSV. **Specifics**: Modified T017 to accept these parameters and write them to the CSV file.
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
 - **Critical Variables**: `throughput`, `latency` (injected), **`cpu_utilization_pct`** (per SC-006 update).
 - **Non‑Critical Variables**: `packet_loss_rate`, `loadavg_1m`, `snr_db`, `bandwidth_Mbps`, `dropout_rate`, `thermal_throttling_detected`.
 - **Step 1**: If any critical variable is missing, **write `data/raw/validation_status.json` with `status: 'excluded'`** and log an error. **Exclude the run from downstream processing**.
 - **Step 2**: If non-critical variables are missing, FLAG a WARN and proceed with a **reduced model**.
 - **Output**: `data/raw/validation_status.json` with schema `{"critical_missing": [...], "non_critical_missing": [...], "excluded_terms": [...], "warnings": [...], "status": "excluded|valid", "reduced_model_config": {...}}`. **Dependency**: T017.
- [ ] T010b [US3] Implement `dynamic_formula_configurator()` in `code/analysis/data_validator.py` to generate the regression configuration object based on T010a's output. **Specifics**:
 - **Input**: `data/raw/validation_status.json`. **Check `status`**: If `excluded`, **abort processing for this run**.
 - **Logic**: Start with base formula `throughput ~ heterogeneity * granularity + injected_latency`. Remove any terms involving variables listed in `excluded_terms` (from `reduced_model_config`). **If a non-critical variable is missing, prune ONLY that term and generate a `reduced_formula` string** (e.g. `throughput ~ heterogeneity + granularity + injected_latency`). **Do NOT exclude the run**.
 - **Output**: Configuration object listing included terms and the `reduced_formula` string.
 - **Dependency**: T010a.
- [ ] T051 [US3] Implement `dynamic_formula_builder.py` in `code/analysis/` to construct the final `statsmodels` formula string. **Specifics**:
 - **Input**: Configuration object from T010b.
 - **Action**: Build a formula string, automatically pruning interaction terms for any missing variables.
 - **Statistical Distinction**: **Explicitly treat `injected_latency` as a fixed factor using `C(injected_latency)` notation** and `hardware_class` (derived from CPU model) as an **observational covariate** using continuous/ordinal encoding.
 - **Output**: String ready for `statsmodels` fitting (e.g. `"throughput ~ C(granularity) * heterogeneity + C(injected_latency)"`).
 - **Dependency**: T010b.
- [ ] T030a [US3] Implement `fit_mlr_with_interactions()` in `code/analysis/regression.py` using `statsmodels`. **Specifics**:
 - **Formula**: Use the string generated by T051.
 - **Must include** interaction terms between heterogeneity and granularity.
 - **Output**: Save fitted model to `code/analysis/output/mlr_model.json` containing `coefficients`, `p_values`, `r_squared`, `formula_string`.
 - **Dependency**: T051, T017.
- [ ] T030b [US3] Implement `fit_gam_with_interactions()` in `code/analysis/regression.py` using `pygam`. **Dependency**: T051.
- [ ] T035b [US3] Implement `model_selector.py` in `code/analysis/` to compare MLR and GAM results. **Specifics**: **Enforce Plan's Methodological Update**: **GAM is the default primary model**. Select MLR ONLY if GAM fails to converge or if AIC/BIC delta strongly favors MLR (indicating severe overfitting in GAM). Compute AIC, BIC, and R² for both models; log rationale. **Output**: JSON specifying `selected_model` (`mlr` or `gam`) and the metrics for both. **Critical**: Must NOT suppress the MLR artifact; both model files remain on disk. **Dependency**: T030a, T030b.
- [ ] T031 [US3] Implement `anova_test.py` in `code/analysis/` to determine statistical significance (p < 0.05) of granularity differences. **Specifics**:
 - **Input**: Aggregated dataset from T023.
 - **Method**: Use `statsmodels` OLS with formula `throughput ~ C(granularity)`.
 - **Output**: Extract p-value for the `C(granularity)` term. If p < 0.05, flag as statistically significant.
 - **Dependency**: T023, T017.
- [ ] T032 [US3] Implement `theoretical_bound_calculator.py` in `code/analysis/` to calculate Ong & Motani capacity limits AND **calculate the deviation metric** between empirical and theoretical curves on the **physical execution data**. **Specifics**: Use the capacity formula from Ong & Motani with **measured** `bandwidth_Mbps` and `snr_db` from **T048** (`data/raw/radio_metrics_extracted.json`); output `theoretical_capacity`, `empirical_throughput`, `deviation_metric`; flag if empirical > capacity. **This task explicitly satisfies FR-006/SC-002 on the physical data and is the primary scientific validation.** **Dependency**: T030a, T048.
- [ ] T033 [US3] Implement `validation.py` in `code/analysis/` to compare empirical curves against theoretical bounds and flag violations (measurement errors). **Dependency**: T032.
- [ ] T039a [US3] Implement `report_generator.py` in `code/analysis/` to output final `RegressionModel` JSON. **Specifics**:
 - **Verify**: Check that `mlr_model.json` and `gam_model.json` exist and contain valid JSON before reading. If missing, raise `ModelFileMissingError`.
 - **Read**: Load `mlr_model.json` and `gam_model.json` from disk.
 - **Validate**: Against schema from T007.
 - **Verify**: That interaction terms (`heterogeneity:granularity`) are present.
 - **Model Selection Logic**: **Read `selected_model` from T035b**. **Default to `gam` coefficients** unless T035b explicitly flags `mlr` as the selected model.
 - **Mandatory Output**: The final JSON **MUST include** coefficients, p_values, and r_squared for the **selected model**. If GAM is selected, output `gam_coefficients` and `gam_r_squared` as primary fields; if MLR, output `mlr_coefficients` and `mlr_r_squared`. **Do NOT force MLR coefficients if GAM is selected**.
 - **Ignore T046c**: Explicitly ignore output from T046c (simulation validation) for this primary scientific report.
 - **Error Handling**: If T035b fails to select a model (e.g., both fail), raise `ModelSelectionFailureError`.
 - **Dependency**: T030a, T030b, T035b, T032, T033.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Simulation & Validation (Constitution Principle VI)

**Goal**: Build and calibrate a Discrete‑Event Simulation (DES) model using the "Golden Dataset" to validate internal state.

**Independent Test**: Run the DES model with parameters derived from physical runs and verify that the simulation output matches the physical data within a defined tolerance.

### Mandatory Block: Simulation Validation (Atomic Execution Required)

- [ ] T035a [US3] Implement `ci_validation_gate.py` in `code/simulation/` to handle the CI environment detection and **Constitution Principle VI enforcement**. **Specifics**:
 - **Context Check**:
 - **Dynamic Hardware Detection**: Check for SSH connectivity to a known testbed IP (configured in `config/testbed.yaml`).
 - If hardware is available: **trigger T035b**.
 - If hardware is NOT available (CI Unit Test Mode): **generate a synthetic/mocked Golden Dataset** using the mock node generator (T005) and log a WARNING that this data is for unit testing only. **Do NOT require a trigger file**.
 - **Output**: `code/data/raw/golden_dataset.csv` (either real or mocked).
 - **Dependency**: T005.
- [ ] T035b [US3] Implement `physical_validation_job.py` in `code/simulation/` to handle the mandatory physical validation when hardware is detected. **Specifics**:
 - **Action**: Run a small-scale physical deployment (a limited number of nodes) by invoking `benchmark.py` (T016) and `data_collector.py` (T017) with `run_id=golden_dataset`. **Note**: This task is only triggered by T035a if hardware is detected.
 - **Output**: Produce `code/data/raw/golden_dataset.csv`.
 - **Dependency**: T035a (trigger logic), T017, T016.
- [ ] T036 [P] [US3] Implement `des_model.py` in `code/simulation/` using `simpy` to model task scheduling, network latency, and node heterogeneity. **Specifics**: Create `TaskScheduler` and `Node` processes. **Scope Check**: Before initialization, verify that the estimated state space and event count fit within the 6-hour CI budget. If complexity exceeds limits, raise `SimulationComplexityError`.
- [ ] T037a [US3] Implement `des_parameter_fitter.py` in `code/simulation/` to fit DES parameters against the `code/data/raw/golden_dataset.csv`. **Specifics**:
 - **Input**: Must read `code/data/raw/golden_dataset.csv`; if the file is missing, raise `CalibrationDataMissingError`.
 - **Optimization**: Adjust parameters (e.g. `packet_loss_rate`, `cpu_variance`) to minimize MSE between simulation output and physical data.
 - **Dependency**: T036, `code/data/raw/golden_dataset.csv`.
- [ ] T037b [US3] Implement `des_convergence_checker.py` in `code/simulation/` to check calibration convergence. **Specifics**:
 - **Input**: MSE values from T037a.
 - **Logic**: Maintain a deque of the last several MSE values. After each iteration compute `relative_change = abs(current - value_5_steps_ago) / value_5_steps_ago`. **For the first iterations, skip the relative change check**. Stop when `relative_change < 1e-4` for five consecutive checks or after `max_iterations = 1000`.
 - **Output**: Convergence status and final parameters.
 - **Dependency**: T037a.
- [ ] T037c [US3] Implement `des_timeout_enforcer.py` in `code/simulation/` to enforce the CI limit on calibration. **Specifics**:
 - **Integration**: Invoke `enforce_pipeline_timeout()` from T009 to ensure the calibration phase respects the CI limit.
 - **Dependency**: T037a, T037b.
- [ ] T038 [US3] Implement `internal_state_validator.py` in `code/simulation/` to compare DES outputs against the Golden Dataset. **Specifics**:
 - **Metrics**: Compute **MSE (Mean Squared Error)** and **Pearson correlation** between simulated and physical throughput.
 - **Tolerance**: If `abs(simulated - physical) > tolerance` (tolerance = 0.05 × mean physical), raise `ValidationFailure`.
 - **Output**: `validation_report.json` with metrics and pass/fail status.
 - **Dependency**: T037a, T037b, T037c.
- [ ] T046c [US3] Implement `theoretical_bound_validator_phase6.py` in `code/simulation/` to perform a **sanity check** on the simulation inputs against theoretical bounds. **Specifics**:
 - **Input**: `code/data/raw/golden_dataset.csv` (Golden Dataset) and `data/raw/radio_metrics_extracted.json` (from T048).
 - **Logic**: Calculate the theoretical capacity bound using the Ong & Motani formula with the measured `bandwidth_Mbps` and `snr_db` from the Golden Dataset.
 - **Output**: `theoretical_bound_validation.json` containing `theoretical_capacity`, `empirical_throughput`, `deviation_metric`, and a `pass/fail` flag. **Note: This task is for simulation calibration validation only and its output must NOT be included in the primary scientific report generated by T039a. The primary scientific validation is performed by T032.**
 - **Dependency**: T032, T048.

**Checkpoint**: All user stories should now be independently functional

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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