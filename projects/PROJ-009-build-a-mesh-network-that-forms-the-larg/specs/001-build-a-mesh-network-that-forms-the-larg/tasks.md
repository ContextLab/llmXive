# Tasks: Mesh Network Supercomputer Using Pooled Idle Computing Resources  

**Inputs**: `specs/001-build-a-mesh-network-that-forms-the-larg/spec.md`, `plan.md`, data‑model contracts, and reviewer feedback.

The checklist below implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006). Tasks are ordered to respect data flow and to repair the failures reported by the independent verifier. All boxes are unchecked; once a task is completed and its verification passes, the CI will tick the box.

---  

## Phase 1 – Core infrastructure, instrumentation, and first end‑to‑end run  

- [ ] **T001** Create reproducible configuration, quick‑start guide, and contract‑test harness  
  *Artifacts*  
  - `config.yaml` – default configuration (random_seed, global timeout = 21600 s, sweep defaults).  
  - `quickstart.md` – usage examples for `calibrate`, `run-single`, `sweep`, `aggregate`, `regression`, `theoretical-bound`, `sweet-spot`.  
  - `code/tests/contract/test_contracts.py` – iterates over every schema in `specs/**/contracts/` and runs `jsonschema.validate`.  
  - `code/orchestrator/cli.py` – exposes `--help` and sub‑commands (`calibrate`, `run-single`, `sweep`). Implements `get_config()` that loads `config.yaml`.  
  *Verification* – run `pytest code/tests/contract/ -q`; the command must exit 0 and the test `test_random_seed_is_integer_and_matches_sweep_config` must pass.  

- [ ] **T002** Add PhysicalNode schema and implement full node‑metadata collection  
  *Artifacts*  
  - `specs/001-build-a-mesh-network-that-forms-the-larg/contracts/physical-node.schema.yaml` (exact schema from the spec).  
  - `code/orchestrator/node_manager.py` – discovers reachable SSH nodes, runs `lscpu`, `free`, `iperf3`, `iwconfig`, `mpstat`, `sensors`; writes `data/raw/physical_node_<ip>.json`.  
  - `code/tests/unit/test_node_manager.py` – uses mock‑node fixtures; asserts each JSON file validates against the schema and that missing tools raise `RuntimeError`.  
  *Verification* – after running the unit test a set of `physical_node_*.json` files exist and all pass schema validation.  

- [ ] **T003** Create realistic instrumentor log fixtures and parsing utilities  
  *Artifacts*  
  - `data/raw/sample_tcpdump.log` – e.g. “123 packets captured”.  
  - `data/raw/sample_mpstat.log` – typical `mpstat` output containing a CPU % line.  
  - `data/raw/sample_iwconfig.log` – Signal level = ‑40 dBm, SNR = 50.  
  - `data/raw/sample_sensors.log` – CPU Temp +42.0 °C.  
  - `data/raw/sample_ping.log` – avg rtt 0.030 ms.  
  - `code/orchestrator/instrumentor.py` – thin wrappers for `tcpdump`, `mpstat`, `iwconfig`, `sensors`, `ping`; each returns a numeric metric.  
  - `code/tests/unit/test_instrumentor.py` – parses the above fixtures and asserts the expected numbers; missing tools raise `RuntimeError`.  
  *Verification* – `pytest code/tests/unit/test_instrumentor.py -q` exits 0; each parser returns the documented numeric value.  

- [ ] **T004** Implement dynamic scheduler with dropout handling, coordination‑overhead timestamps, and write `dropout_events.json`  
  *Artifacts*  
  - `code/orchestrator/scheduler.py` – assigns `TaskChunk`s, monitors heartbeats, detects dropout reasons (`heartbeat_loss`, `oom`, `sleep_mode`, `network_saturation`), re‑assigns tasks, records `handshake_start`, `handshake_end`, `compute_start`, `compute_end` per chunk.  
  - `code/orchestrator/task_chunk_store.py` – writes one JSON line per chunk to `data/raw/task_chunks/<run_id>.jsonl` and validates each line against `task-chunk.schema.yaml`.  
  - `code/orchestrator/dropout_logger.py` – aggregates dropout events and writes `data/raw/dropout_events.json`.  
  - `code/tests/unit/test_scheduler.py` – mock nodes trigger each dropout scenario; asserts a `dropout_events.json` entry is written, conforms to `dropout-event.schema.yaml`, and that timestamps exist for coordination‑overhead calculation.  
  *Verification* – scheduler unit tests pass; `dropout_events.json` validates; every task record contains the four timestamps needed for overhead computation.  

- [ ] **T005** Fix `ProjectPaths` test failure, integrate `TaskChunkStore` with the scheduler, and validate chunk files  
  *Artifacts*  
  - Updated `code/runtime/paths.py` (or equivalent) so the test suite can monkey‑patch the base directory via `TaskChunkStore.base_dir` (no setter on `ProjectPaths`).  
  - `code/tests/unit/test_task_chunk_store.py` – verifies that after a mock run `data/raw/task_chunks/run_001.jsonl` exists and each line validates against `task-chunk.schema.yaml`.  
  - Scheduler now calls `TaskChunkStore.append(chunk)` for every created `TaskChunk`.  
  *Verification* – `pytest tests/unit/test_task_chunk_store.py -q` passes; no `AttributeError` remains.  

- [ ] **T006** Enforce hard pipeline timeout and record runtime metrics  
  *Artifacts*  
  - `code/orchestrator/runtime_tracker.py` – `@enforce_pipeline_timeout` decorator; writes `data/runtime/pipeline_runtime.json` (`total_seconds`, `within_limit`) and `data/runtime/timeout_enforced.log` when the limit is exceeded.  
  - `code/tests/integration/test_watchdog_overrun.py` – runs a dummy long‑running command, expects non‑zero exit, and checks that both JSON and log files are created.  
  *Verification* – integration test passes; when the timeout fires the runner aborts with exit 1 and the JSON shows `"within_limit": false`.  

- [ ] **T007** Add calibration sub‑command and produce verified conversion factors  
  *Artifacts*  
  - `code/orchestrator/calibration.py` –  
    * `calibrate_network()` starts a local `iperf3` server (`iperf3 -s`) in a background thread, runs a client (`iperf3 -c 127.0.0.1 -t 5`), maps `tcpdump` packet counts to Mbps; writes `data/raw/network_calibration.json` (`packet_to_mbps_factor`, `r_squared`).  
    * `calibrate_cpu()` runs `sysbench cpu --threads=1 run`, fits a linear model between `mpstat` % util and known CPU load; writes `data/raw/cpu_calibration.json` (`percent_to_ops_factor`, `r_squared`).  
  - `code/tests/unit/test_calibration.py` – asserts both JSON files exist, contain numeric factors, and have `r_squared ≥ 0.9`.  
  *Verification* – `python -m code.orchestrator.cli calibrate` creates both JSON files; unit tests pass; the sweep runner aborts if either file is missing or has low R².  

- [ ] **T008** Run a minimal single‑node benchmark end‑to‑end (sanity‑check)  
  *Artifacts*  
  - `code/orchestrator/cli.py` – sub‑command `run-single` that (a) loads `config.yaml`, (b) discovers nodes via `node_manager`, (c) runs a tiny Monte‑Carlo integration task on 4 mock nodes, (d) instruments each node via `instrumentor` (real `tcpdump` packet counts, not just iteration counters), (e) stores `TaskChunk`s through `TaskChunkStore`, (f) writes `data/raw/run_001.csv` (columns: `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `task_id`, `status`), (g) writes `data/raw/task_chunks/run_001.jsonl`, (h) writes `data/raw/validation_status.json` (run passes variable‑fit check).  
  - `code/tests/integration/test_full_workflow.py` – invokes `run-single` and asserts exit 0 and presence/validity of the three output files.  
  *Verification* – integration test passes; `run_001.csv` contains a non‑zero packet count for every node; `validation_status.json` marks the run as “included”.  

## Phase 2 – Full sweep, aggregation, analysis, and reproducibility  

- [ ] **T009** Execute full parameter sweep on the CI‑friendly mock testbed  
  *Artifacts*  
  - `config/sweep_config.yaml` – grid: granularity {fine,medium,coarse} × node_count {10,15,20} × injected_latency {0,50,100,150 ms} × replicates = 4 (total 144 runs) plus 6 reserved dropout‑recovery runs (150 runs total). Includes `random_seed`, `sweet_spot_threshold`, and the global timeout.  
  - `code/orchestrator/network_impairment.py` – applies latency and packet‑loss via `tc netem`; aborts runs with packet‑loss > 20 % and logs reason `NETWORK_SATURATION`.  
  - `code/orchestrator/sweep_runner.py` – orchestrates the grid, checks that `network_calibration.json` and `cpu_calibration.json` exist, wraps each run with the `@enforce_pipeline_timeout` decorator, writes `data/raw/run_<run_id>.csv` and `data/raw/task_chunks/<run_id>.jsonl`.  
  *Verification* – after execution exactly 150 CSV files (or aborted‑run entries in `validation_status.json`) exist; each CSV validates against a minimal per‑run schema; total wall‑clock time recorded in `pipeline_runtime.json` ≤ 6 h.  

- [ ] **T010** Aggregate raw logs into a schema‑conforming ExecutionRun table and produce a run‑inclusion report  
  *Artifacts*  
  - `code/analysis/aggregate.py` – reads all `run_*.csv`, merges node metadata, dropout events, computes per‑run metrics (throughput, coordination‑overhead ratio, straggler count, baseline/runtime bandwidth & SNR, `cpu_variance`, `dropout_rate`, optional temperature/os‑noise).  
  - `data/processed/execution_runs.csv` – one row per successful run, conforms to `execution-run.schema.yaml`.  
  - `code/analysis/data_validator.py` – scans `execution_runs.csv` for missing required columns; produces `data/raw/validation_status.json` mapping each `run_id` to `included`/`excluded` with reason (critical variable missing).  
  *Verification* – `python -m code.analysis.aggregate` finishes without error; a schema validator confirms every row passes; `validation_status.json` correctly flags any excluded runs.  

- [ ] **T011** Statistical analysis, theoretical‑bound validation, sweet‑spot detection, figures, and methods hand‑off  
  *Artifacts*  
  - `code/analysis/regression.py` – loads only “included” rows, fits OLS with interaction terms (`granularity × cpu_variance`, `granularity × dropout_rate`, `injected_latency × node_count`), optionally adds quadratic terms, selects best model by AIC/BIC, computes VIF (warns if > 5), applies Benjamini‑Hochberg FDR to all p‑values, runs `anova_lm` for `throughput ~ C(granularity)`.  
  - `data/processed/regression_model.json` – conforms to `regression-model.schema.yaml` (coefficients, p_values, r_squared, residuals, placeholder `theoretical_bound_deviation`).  
  - `data/processed/anova.json` – contains ANOVA table; granularity p‑value must be < 0.05 (SC‑005).  
  - `code/analysis/theoretical_bound.py` – computes Shannon capacity from `baseline_bandwidth_Mbps` and `baseline_snr_db`, derives `normalized_efficiency` and `theoretical_bound_deviation`; writes `data/processed/theoretical_bound_validation.json`.  
  - `code/analysis/sweet_spot.py` – determines the granularity setting with maximal marginal throughput gain above the `sweet_spot_threshold`; writes `data/processed/sweet_spot.json`.  
  - `code/analysis/figures.py` – creates PNGs in `figures/`: `throughput_vs_nodes.png`, `coordination_overhead.png`, `bound_comparison.png`; updates `data/figures_manifest.yaml`.  
  - `data/processed/methods_summary.md` – concise methods & results narrative linking to all primary artifacts, honest discussion of limitations, and explicit statement of associational nature of heterogeneity effects.  
  - `data/processed/reproducibility_log.txt` – output of a fresh run of the entire workflow (steps listed in `quickstart.md`); includes SHA‑256 hashes of generated artifacts and confirms all tests pass.  
  *Verification* – all JSON files validate against their schemas; ANOVA granularity p‑value < 0.05; at least one run shows `normalized_efficiency ≤ 1.0`; figures exist and are referenced in the manifest; `reproducibility_log.txt` shows a clean end‑to‑end execution on a fresh checkout.  

- [ ] **T012** Integrate variable‑fit verification into the aggregation pipeline and ensure SC‑006 compliance  
  *Artifacts*  
  - `code/analysis/validation.py` – invoked by `aggregate.py`; guarantees that every required predictor (`cpu_variance`, `dropout_rate`, `node_count`, `granularity_setting`, `injected_latency`) and outcome (`total_throughput`) is present for each run; writes `data/raw/validation_status.json` with per‑run inclusion flags and reasons for exclusion.  
  - Updated `code/tests/integration/test_full_workflow.py` – asserts that after both `run-single` and the full sweep, `validation_status.json` exists and marks runs as “included” only when all critical variables are present.  
  *Verification* – validation step runs without error; `validation_status.json` reflects SC‑006 requirements; integration test passes.  

- [ ] **T013** Provide full test‑suite execution logs proving all contract, unit, and integration tests pass  
  *Artifacts*  
  - `logs/test_suite_execution.log` – concatenated stdout/stderr of `pytest -q` covering `code/tests/contract/`, `code/tests/unit/`, and `code/tests/integration/`. The log must end with “=== 0 failed, X passed in Ys ===”.  
  - Updated `quickstart.md` includes a command snippet `pytest -q > logs/test_suite_execution.log` for reproducibility.  
  *Verification* – the log file is present, parsable, and shows zero failures; the CI step that uploads the log succeeds.  

---  

### Dependency matrix (quick reference)

| Spec requirement | Tasks that satisfy it | Key artifact |
|------------------|-----------------------|--------------|
| FR‑001 (dynamic scheduler, heartbeats) | T004, T005 | `scheduler.py`, `dropout_events.json` |
| FR‑002 (tcpdump & mpstat instrumentation) | T003, T004, T008 | `instrumentor.py`, `run_001.csv` |
| FR‑003 (parameter sweep, injected latency) | T009 | `sweep_runner.py`, `run_*.csv` |
| FR‑004 (coordination‑overhead metric) | T004, T009, T010 | timestamps in task records, `execution_runs.csv` |
| FR‑005 (regression & ANOVA) | T011 | `regression_model.json`, `anova.json` |
| FR‑006 (theoretical bound) | T011 | `theoretical_bound_validation.json` |
| FR‑007 (hard CI timeout) | T006, T009 | `pipeline_runtime.json`, `timeout_enforced.log` |
| SC‑001 (R²) | T011 | `regression_model.json.r_squared` |
| SC‑002 (bound deviation) | T011 | `theoretical_bound_validation.json` |
| SC‑003 (sweet‑spot detection) | T011 | `sweet_spot.json` |
| SC‑004 (pipeline wall‑clock) | T006, T009 | `pipeline_runtime.json` |
| SC‑005 (ANOVA significance) | T011 | `anova.json` (granularity p < 0.05) |
| SC‑006 (variable completeness) | T010, T012 | `validation_status.json` |

**Execution order** (respecting data flow):  
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013.  

All tasks remain unchecked until their respective artifacts are produced and the verification steps succeed. This plan now satisfies every functional requirement, success criterion, and reviewer concern while remaining executable within the free‑tier CI budget.
