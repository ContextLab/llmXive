# Tasks: Mesh Network Supercomputer Using Pooled Idle Computing Resources  

**Inputs**: `specs/001-build-a-mesh-network-that-forms-the-larg/spec.md`, `plan.md`, data‑model contracts, reviewer feedback, and any existing artifacts.

The checklist below implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006).  Tasks are ordered to respect data flow and to repair the failures reported by the independent verifier.  All boxes are unchecked; once a task is completed and its verification passes, the CI will tick the box.

---  

## Phase 1 – Core infrastructure, instrumentation, and first end‑to‑end run  

- [ ] **T001** Create reproducible configuration, quick‑start guide, contract‑test harness, and evidence of a passing test run  
  *Artifacts*  
  - `config.yaml` – default configuration (random_seed, global_timeout_seconds = 21600, sweep defaults).  
  - `quickstart.md` – usage examples for `calibrate`, `run-single`, `sweep`, `aggregate`, `regression`, `theoretical-bound`, `sweet-spot`.  
  - `code/tests/contract/test_contracts.py` – discovers every `*.schema.yaml` under `specs/**/contracts/` and validates all JSON files in `data/**`.  
  - `logs/pytest_contracts.log` – output of `pytest code/tests/contract/ -q` showing **0 failures**.  

- [ ] **T002** Add the PhysicalNode JSON‑Schema, implement full node‑metadata collection, and validate the output  
  *Artifacts*  
  - `specs/001-build-a-mesh-network-that-forms-the-larg/contracts/physical-node.schema.yaml` (exact schema from the spec).  
  - `code/orchestrator/node_manager.py` – discovers reachable SSH nodes, runs `lscpu`, `free`, `iperf3`, `iwconfig`, `mpstat`, `sensors`; writes one file per node: `data/raw/physical_node_<ip>.json`.  
  - `code/tests/unit/test_node_manager.py` – uses mock‑node fixtures; asserts each JSON file validates against the schema and that missing tools raise a clear `RuntimeError`.  
  - `logs/pytest_node_manager.log` – result of the unit test suite showing **0 failures**.  

- [ ] **T003** Implement dropout‑event generation and coordination‑overhead timestamp recording  
  *Artifacts*  
  - `code/orchestrator/scheduler.py` – assigns `TaskChunk`s, monitors heartbeats, records `handshake_start`, `handshake_end`, `compute_start`, `compute_end` per chunk, detects dropout reasons (`heartbeat_loss`, `oom`, `sleep_mode`, `network_saturation`), re‑assigns the failed chunk, and logs the event.  
  - `code/orchestrator/dropout_logger.py` – aggregates events from the scheduler and writes `data/raw/dropout_events.json`.  
  - `code/tests/unit/test_scheduler.py` – mock nodes trigger each of the four dropout reasons; asserts that an entry appears in `dropout_events.json`, that the entry validates against `dropout-event.schema.yaml`, and that timestamps exist for coordination‑overhead calculation.  
  - `logs/pytest_scheduler.log` – result of the scheduler unit tests showing **0 failures**.  

- [ ] **T004** Run a minimal single‑node benchmark end‑to‑end (sanity‑check) and produce the required raw outputs  
  *Artifacts*  
  - `code/orchestrator/cli.py` – adds sub‑command `run-single` that (a) loads `config.yaml`, (b) discovers nodes via `node_manager`, (c) runs a tiny Monte‑Carlo integration task on **4 mock nodes**, (d) instruments each node via `instrumentor` (real `tcpdump` packet counts, not a counter), (e) writes `TaskChunk`s via `TaskChunkStore`, (f) writes `data/raw/run_001.csv` with columns `node_id,wall_clock_time,cpu_utilization_pct,packet_count,task_id,status`, (g) writes `data/raw/task_chunks/run_001.jsonl`, (h) writes `data/raw/validation_status.json` marking the run as “included”.  
  - `code/tests/integration/test_full_workflow.py` – invokes `run-single`, asserts exit 0, and checks existence/validity of the three output files.  
  - `logs/pytest_full_workflow.log` – output of the integration test showing **0 failures**.  

- [ ] **T005** Refactor `ProjectPaths`/`TaskChunkStore` so the test suite can monkey‑patch the storage location, and integrate the store with the scheduler  
  *Artifacts*  
  - `code/runtime/paths.py` – exposes a mutable attribute `TaskChunkStore.base_dir` (no setter on `ProjectPaths`).  
  - `code/orchestrator/task_chunk_store.py` – writes each `TaskChunk` as a JSON line to `TaskChunkStore.base_dir / task_chunks/<run_id>.jsonl` and validates each line against `task-chunk.schema.yaml`.  
  - Updated `scheduler.py` to call `TaskChunkStore.append(chunk)` for every created chunk.  
  - `code/tests/unit/test_task_chunk_store.py` – monkey‑patches `TaskChunkStore.base_dir` to a temporary directory, runs a mock scheduler, and asserts that `run_001.jsonl` exists and all lines validate.  
  - `logs/pytest_task_chunk_store.log` – output of the unit test suite showing **0 failures**.  

- [ ] **T006** Enforce a hard pipeline timeout and record runtime metrics for both normal and over‑run cases  
  *Artifacts*  
  - `code/orchestrator/runtime_tracker.py` – provides `@enforce_pipeline_timeout(max_seconds)` decorator; on entry records start time, on exit writes `data/runtime/pipeline_runtime.json` (`total_seconds`, `within_limit`), and if the limit is exceeded also writes `data/runtime/timeout_enforced.log` with a clear error message.  
  - `code/tests/integration/test_watchdog_overrun.py` – launches a dummy function that sleeps longer than the configured limit, expects a non‑zero exit, and checks that both JSON and log files are created with `"within_limit": false`.  
  - `logs/pytest_watchdog.log` – result of the integration test showing **0 failures**.  

- [ ] **T007** Add a calibration sub‑command that produces verified conversion factors for network packets ↔ Mbps and CPU % ↔ operations  
  *Artifacts*  
  - `code/orchestrator/calibration.py` – runs a local `iperf3` server/client, captures a short `tcpdump` capture, fits a linear model between packet count and measured Mbps, writes `data/raw/network_calibration.json` (`packet_to_mbps_factor`, `r_squared`); runs `sysbench cpu` + `mpstat`, fits a linear model between `% util` and known CPU load, writes `data/raw/cpu_calibration.json` (`percent_to_ops_factor`, `r_squared`).  
  - `code/tests/unit/test_calibration.py` – asserts both JSON files exist, contain numeric factors, and that `r_squared ≥ 0.9`.  
  - `logs/pytest_calibration.log` – output of the calibration unit tests showing **0 failures**.  

- [ ] **T008** Provide realistic instrument‑log fixtures and implement parsers with unit‑test verification  
  *Artifacts*  
  - `data/raw/sample_tcpdump.log` – e.g. “123 packets captured”.  
  - `data/raw/sample_mpstat.log` – typical `mpstat` output containing a line with “CPU % = 42.3”.  
  - `data/raw/sample_iwconfig.log` – contains “Signal level = ‑40 dBm”, “SNR = 50”.  
  - `data/raw/sample_sensors.log` – contains “CPU Temperature +42.0 °C”.  
  - `data/raw/sample_ping.log` – contains “rtt min/avg/max/mdev = 0.030/0.030/0.030/0.000 ms”.  
  - `code/orchestrator/instrumentor.py` – thin wrappers (`parse_tcpdump`, `parse_mpstat`, `parse_iwconfig`, `parse_sensors`, `parse_ping`) that return the numeric metric.  
  - `code/tests/unit/test_instrumentor.py` – reads the fixture files and asserts the returned numbers match the known values.  
  - `logs/pytest_instrumentor.log` – output of the unit tests showing **0 failures**.  

- [ ] **T009** Execute a full parameter sweep on the CI‑friendly mock testbed, respecting network impairments and the global timeout  
  *Artifacts*  
  - `config/sweep_config.yaml` – grid definition: `granularity` ∈ {fine,medium,coarse} × `node_count` ∈ {10,15,20} × `injected_latency_ms` ∈ {0,50,100,150} × `replicates` = 4 (144 runs) plus 6 reserved dropout‑recovery runs → **150 runs** total. Includes `random_seed`, `sweet_spot_threshold`, and `global_timeout_seconds`.  
  - `code/orchestrator/network_impairment.py` – applies latency and packet‑loss via `tc netem`; aborts a run if packet‑loss > 20 % and logs reason `"NETWORK_SATURATION"` in `dropout_events.json`.  
  - `code/orchestrator/sweep_runner.py` – iterates over the grid, validates that calibration files exist before each run, wraps each run with `@enforce_pipeline_timeout`, writes per‑run CSV `data/raw/run_<run_id>.csv` and `data/raw/task_chunks/<run_id>.jsonl`.  
  - `logs/pytest_sweep.log` – result of a quick sanity‑check that the sweep runner launches at least one run and respects the timeout (0 failures).  

- [ ] **T010** Aggregate raw logs into a schema‑conforming `execution_runs.csv` and produce a run‑inclusion report  
  *Artifacts*  
  - `code/analysis/aggregate.py` – reads all `run_*.csv`, merges node metadata, dropout events, calibration factors, and computes per‑run metrics required by `execution-run.schema.yaml`.  
  - `data/processed/execution_runs.csv` – one row per **included** run, validated against `execution-run.schema.yaml`.  
  - `code/analysis/data_validator.py` – scans `execution_runs.csv` for missing required columns; writes `data/raw/validation_status.json` mapping each `run_id` → `included` / `excluded` with a short reason.  
  - `logs/pytest_aggregate.log` – output of the aggregation script validation (0 failures).  

- [ ] **T012** Variable‑Fit verification (must run before any regression)  
  *Artifacts*  
  - `code/analysis/validation.py` – invoked by `aggregate.py`; confirms that every required predictor (`cpu_variance`, `dropout_rate`, `node_count`, `granularity_setting`, `injected_latency`) and outcome (`total_throughput`) is present for each run; writes an updated `data/raw/validation_status.json` with per‑run `included` / `excluded` flags and reasons.  
  - Updated `code/tests/integration/test_full_workflow.py` – asserts that after both `run-single` and the full sweep, `validation_status.json` exists and only runs with all critical variables are marked “included”.  
  - `logs/pytest_variable_fit.log` – result of the integration test (0 failures).  

- [ ] **T018** Physical‑pilot validation of the mock testbed (Principle VI)  
  *Artifacts*  
  - `code/orchestrator/pilot_validation.py` – runs the full scheduler on a small real mesh of **12** heterogeneous devices, records the same metrics as the mock run, and compares key aggregates (throughput, coordination‑overhead) against the mock baseline.  
  - `data/raw/pilot_validation_report.json` – JSON summary of the comparison, must show ≤ 10 % deviation.  
  - `logs/pytest_pilot_validation.log` – unit‑test log confirming the pilot script executes without error on the test harness.  

- [ ] **T019** Timing benchmark for the full sweep (CI budget evidence)  
  *Artifacts*  
  - `code/analysis/benchmark_runtime.py` – runs a reduced‑size sweep (2 granularity settings × 2 node counts × 1 latency × 2 replicates) on CI, records total wall‑clock time, and asserts it is ≤ 1800 seconds.  
  - `logs/benchmark_runtime.log` – contains the measured runtime and the assertion result.  

- [ ] **T020** Optional `pygam` dependency handling  
  *Artifacts*  
  - `code/analysis/optional_gam.py` – attempts to import `pygam`; if unavailable, falls back to a plain polynomial OLS model and logs the fallback.  
  - `logs/optional_gam.log` – shows whether `pygam` was used or the fallback was taken.  

## Phase 2 – Detailed statistical analysis (split from original T011)  

- [ ] **T011‑a** Fit OLS regression with interaction terms and write `regression_model.json`  
  *Artifacts*  
  - `code/analysis/regression.py` – loads only **included** rows, fits OLS with interaction terms, computes VIF, applies Benjamini‑Hochberg FDR, writes `data/processed/regression_model.json` (conforms to `regression-model.schema.yaml`).  

- [ ] **T011‑b** Run ANOVA on granularity factor and write `anova.json` (granularity p < 0.05)  
  *Artifacts*  
  - `code/analysis/anova.py` – runs `anova_lm` on the selected model, writes `data/processed/anova.json`.  

- [ ] **T011‑c** Validate empirical throughput against Ong & Motani capacity bound  
  *Artifacts*  
  - `code/analysis/theoretical_bound.py` – computes Shannon capacity from average baseline bandwidth and SNR, derives `normalized_efficiency` and `theoretical_bound_deviation`, writes `data/processed/theoretical_bound_validation.json`.  

- [ ] **T011‑d** Detect the “sweet‑spot” granularity setting  
  *Artifacts*  
  - `code/analysis/sweet_spot.py` – scans regression results to find where marginal throughput gain falls below the configured `sweet_spot_threshold`, writes `data/processed/sweet_spot.json`.  

- [ ] **T011‑e** Generate all figures (PNG) for the paper  
  *Artifacts*  
  - `code/analysis/figures.py` – produces `figures/throughput_vs_nodes.png`, `figures/coordination_overhead.png`, `figures/bound_comparison.png`, updates `data/figures_manifest.yaml`.  

- [ ] **T011‑f** Create methods summary and reproducibility log  
  *Artifacts*  
  - `data/processed/methods_summary.md` – narrative linking artifacts, stating associational nature of heterogeneity effects.  
  - `data/processed/reproducibility_log.txt` – fresh run of the entire pipeline with SHA‑256 hashes of all generated artifacts; ends with “All tests passed”.  

- [ ] **T013** Capture full test‑suite execution logs proving that **all** contract, unit, and integration tests pass on a fresh checkout  
  *Artifacts*  
  - `logs/test_suite_execution.log` – concatenated stdout/stderr of `pytest -q` covering `code/tests/contract/`, `code/tests/unit/`, and `code/tests/integration/`. Must end with “=== 0 failed, X passed in … ===”.  
  - Updated `quickstart.md` – adds a snippet `pytest -q > logs/test_suite_execution.log` for reproducibility.  

---  

### Dependency matrix (quick reference)

| Spec requirement | Tasks that satisfy it | Key artifact |
|------------------|-----------------------|--------------|
| FR‑001 (dynamic scheduler, heartbeats) | T003, T005 | `scheduler.py`, `dropout_events.json` |
| FR‑002 (tcpdump & mpstat instrumentation) | T008, T004 | `instrumentor.py`, `run_001.csv` |
| FR‑003 (parameter sweep, injected latency) | T009 | `sweep_runner.py`, `run_*.csv` |
| FR‑004 (coordination‑overhead metric) | T003, T009, T010 | timestamps in task records, `execution_runs.csv` |
| FR‑005 (regression & ANOVA) | T011‑a, T011‑b | `regression_model.json`, `anova.json` |
| FR‑006 (theoretical bound) | T011‑c | `theoretical_bound_validation.json` |
| FR‑007 (hard CI timeout) | T006, T009 | `pipeline_runtime.json`, `timeout_enforced.log` |
| SC‑001 (R²) | T011‑a | `regression_model.json.r_squared` |
| SC‑002 (bound deviation) | T011‑c | `theoretical_bound_validation.json` |
| SC‑003 (sweet‑spot detection) | T011‑d | `sweet_spot.json` |
| SC‑004 (pipeline wall‑clock) | T006, T009 | `pipeline_runtime.json` |
| SC‑005 (ANOVA significance) | T011‑b | `anova.json` (granularity p < 0.05) |
| SC‑006 (variable completeness) | T012, T010 | `validation_status.json` |

**Execution order** (respecting data flow):  
T001 → T002 → T008 → T003 → T005 → T006 → T007 → T004 → T009 → T010 → T012 → T011‑a → T011‑b → T011‑c → T011‑d → T011‑e → T011‑f → T018 → T019 → T020 → T013.  

All tasks remain unchecked until their respective artifacts are produced and the verification steps succeed. This plan now satisfies every functional requirement, success criterion, and reviewer concern while remaining executable within the free‑tier CI budget.  
