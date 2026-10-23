# Tasks: Mesh Network Supercomputer Using Pooled Idle Computing Resources  

**Inputs**: `specs/001-build-a-mesh-network-that-forms-the-larg/spec.md`, `plan.md`, data‑model contracts, and reviewer feedback.

The checklist below implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006). Tasks are ordered to respect data flow and to repair the failures reported by the independent verifier. All unchecked boxes (`[ ]`) indicate work that still needs to be completed; once a task is completed and its verification passes, the CI will tick the box.

---

## Phase 1 – Project setup, instrumentation, and first end‑to‑end run  

- [ ] **T001** Create reproducible configuration, quick‑start guide, and contract‑test harness  
  *Artifacts*  
  - `config.yaml` – default configuration (random_seed, timeout = 21600 s, sweep defaults).  
  - `quickstart.md` – usage examples for `calibrate`, `run-single`, `sweep`, `aggregate`, `regression`, `theoretical-bound`, `sweet-spot`.  
  - `code/orchestrator/cli.py` – exposes `--help` and sub‑commands (`calibrate`, `run-single`, `sweep`). Implements `get_config()` that loads `config.yaml`.  
  - `code/tests/contract/test_contracts.py` – iterates over every schema in `specs/**/contracts/` and runs `jsonschema.validate`.  
  *Verification* – `pytest code/tests/contract/ -q` exits 0; the test `test_random_seed_is_integer_and_matches_sweep_config` passes (seed integer matches `config.yaml`).  

- [ ] **T002** Add PhysicalNode schema and implement full node‑metadata collection  
  *Artifacts*  
  - `specs/001-build-a-mesh-network-that-forms-the-larg/contracts/physical-node.schema.yaml` (as defined in the spec).  
  - `code/orchestrator/node_manager.py` – discovers reachable SSH nodes, runs `lscpu`, `free`, `iperf3`, `iwconfig`, `mpstat`, `sensors`; writes `data/raw/physical_node_<ip>.json`.  
  - `code/tests/unit/test_node_manager.py` – uses mock‑node fixtures; asserts each JSON file validates against the schema and that missing tools raise `RuntimeError`.  
  *Verification* – after test run a set of `physical_node_*.json` files exist and all pass schema validation.  

- [ ] **T003** Create realistic instrumentor log fixtures and parsing utilities  
  *Artifacts*  
  - `data/raw/sample_tcpdump.log` – e.g. “123 packets captured”.  
  - `data/raw/sample_mpstat.log` – typical `mpstat` output containing CPU % lines.  
  - `data/raw/sample_iwconfig.log` – Signal level = ‑40 dBm, SNR = 50.  
  - `data/raw/sample_sensors.log` – CPU Temp +42.0 °C.  
  - `data/raw/sample_ping.log` – avg rtt 0.030 ms.  
  - `code/orchestrator/instrumentor.py` – thin wrappers for `tcpdump`, `mpstat`, `iwconfig`, `sensors`, `ping`; each returns a numeric metric.  
  - `code/tests/unit/test_instrumentor.py` – parses the above fixtures and asserts the expected numbers; missing tools raise `RuntimeError`.  
  *Verification* – `pytest code/tests/unit/test_instrumentor.py -q` exits 0; each parser returns the documented numeric value.  

- [ ] **T004** Implement dynamic scheduler with dropout handling and coordination‑overhead timestamps  
  *Artifacts*  
  - `code/orchestrator/scheduler.py` – assigns `TaskChunk`s, monitors heartbeats, detects dropout reasons (`heartbeat_loss`, `oom`, `sleep_mode`, `network_saturation`), re‑assigns tasks, records `handshake_start`, `handshake_end`, `compute_start`, `compute_end` per chunk.  
  - `code/orchestrator/task_chunk_store.py` – writes one JSON line per chunk to `data/raw/task_chunks/<run_id>.jsonl` and validates each line against `task-chunk.schema.yaml`.  
  - `code/orchestrator/dropout_logger.py` – aggregates dropout events and writes `data/raw/dropout_events.json`.  
  - `code/tests/unit/test_scheduler.py` – mock nodes trigger each dropout scenario; asserts a `dropout_events.json` entry is written, conforms to `dropout-event.schema.yaml`, and that timestamps exist for coordination‑overhead calculation.  
  *Verification* – scheduler unit tests pass; `dropout_events.json` validates; each task record contains the four timestamps enabling coordination‑overhead calculation.  

- [ ] **T005** Fix ProjectPaths test failure and ensure TaskChunkStore integration  
  *Artifacts*  
  - Updated `code/runtime/paths.py` (or equivalent) so `ProjectPaths.root` can be monkey‑patched via `TaskChunkStore.base_dir` in the test suite (no setter needed on `ProjectPaths`).  
  - Integration of `TaskChunkStore` into `scheduler.py` – every chunk created by the scheduler is persisted through the store.  
  - `tests/unit/test_task_chunk_store.py` – verifies that after a mock run `data/raw/task_chunks/run_001.jsonl` exists and each line validates against `task-chunk.schema.yaml`.  
  *Verification* – `pytest tests/unit/test_task_chunk_store.py -q` passes; no `AttributeError` remains.  

- [ ] **T006** Enforce hard pipeline timeout and record runtime metrics  
  *Artifacts*  
  - `code/orchestrator/runtime_tracker.py` – `@enforce_pipeline_timeout` decorator; writes `data/runtime/pipeline_runtime.json` (`total_seconds`, `within_limit`) and `data/runtime/timeout_enforced.log` when the limit is exceeded.  
  - `code/tests/integration/test_watchdog_overrun.py` – imports `sys`, runs a dummy long‑running command, expects non‑zero exit and the presence of the JSON and log files.  
  *Verification* – integration test passes; when the timeout fires the runner aborts with exit 1 and the JSON shows `"within_limit": false`.  

- [ ] **T007** Add calibration sub‑command and produce verified conversion factors  
  *Artifacts*  
  - `code/orchestrator/calibration.py` –  
    * `calibrate_network()` starts a local `iperf3` server (`iperf3 -s`) in a background thread, runs a client (`iperf3 -c 127.0.0.1 -t 5`), maps `tcpdump` packet counts to Mbps; writes `data/raw/network_calibration.json` (`packet_to_mbps_factor`, `r_squared`).  
    * `calibrate_cpu()` runs `sysbench cpu --threads=1 run`, fits a linear model between `mpstat` % util and known CPU load; writes `data/raw/cpu_calibration.json` (`percent_to_ops_factor`, `r_squared`).  
  - `code/tests/unit/test_calibration.py` – asserts both JSON files exist, contain numeric factors, and have `r_squared ≥ 0.9`.  
  *Verification* – `python -m code.orchestrator.cli calibrate` creates both JSON files; unit tests pass; the sweep runner aborts if either file is missing or has low R².  

- [ ] **T008** Run a minimal single‑node benchmark end‑to‑end (run‑single sanity check)  
  *Artifacts*  
  - `code/orchestrator/cli.py` – sub‑command `run-single` that (a) loads `config.yaml`, (b) discovers nodes via `node_manager`, (c) runs a tiny Monte‑Carlo integration task on 4 mock nodes, (d) instruments each node via `instrumentor` (real `tcpdump` packet counts, not just iteration counters), (e) stores `TaskChunk`s through `TaskChunkStore`, (f) writes `data/raw/run_001.csv` (columns: `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `task_id`, `status`), (g) writes `data/raw/task_chunks/run_001.jsonl`, (h) writes `data/raw/validation_status.json` (run passes variable‑fit check).  
  - `code/tests/integration/test_full_workflow.py` – invokes `run-single` and asserts exit 0 and presence/validity of the three output files.  
  *Verification* – integration test passes; `run_001.csv` contains a non‑zero packet count for every node; `validation_status.json` marks the run as “included”.  

---

## Phase 2 – Complete parameter sweep, aggregation, validation, and statistical analysis  

- [ ] **T009** Update ExecutionRun schema to capture heterogeneity covariates and add contract tests  
  *Artifacts*  
  - Updated `specs/001-build-a-mesh-network-that-forms-the-larg/contracts/execution-run.schema.yaml` – adds required `cpu_variance` (number) and `dropout_rate` (number 0‑1).  
  - Updated `specs/001-build-a-mesh-network-that-forms-the-larg/data-model.md` – reflects the new fields.  
  - `code/tests/contract/test_execution_run_schema.py` – validates a sample record with the new fields and rejects a record missing them.  
  *Verification* – all contract tests pass; the schema now enforces SC‑006 (variable‑fit) for these fields.  

- [ ] **T010** Execute full parameter sweep on the CI‑friendly mock testbed  
  *Artifacts*  
  - `config/sweep_config.yaml` – grid: granularity {fine,medium,coarse} × node_count {10,15,20} × injected_latency {0,50,100,150 ms} × replicates = 4 (total 144 runs) plus 6 reserved dropout‑recovery runs (150 runs total). Includes `random_seed`, `sweet_spot_threshold`, and the global timeout.  
  - `code/orchestrator/network_impairment.py` – applies latency and packet‑loss via `tc netem`; aborts runs with packet‑loss > 20 % and logs reason `NETWORK_SATURATION`.  
  - `code/orchestrator/sweep_runner.py` – orchestrates the grid, checks that `network_calibration.json` and `cpu_calibration.json` exist, wraps each run with the `@enforce_pipeline_timeout` decorator, writes `data/raw/run_<run_id>.csv` and `data/raw/task_chunks/<run_id>.jsonl`.  
  *Verification* – after execution exactly 150 CSV files (or aborted‑run entries in `validation_status.json`) exist; each CSV validates against a minimal per‑run schema; total wall‑clock time recorded in `pipeline_runtime.json` ≤ 6 h.  

- [ ] **T011** Aggregate raw logs into a schema‑conforming ExecutionRun table and produce a run‑inclusion report  
  *Artifacts*  
  - `code/analysis/aggregate.py` – reads all `run_*.csv`, merges node metadata, dropout events, computes per‑run metrics (throughput, coordination‑overhead ratio, straggler count, baseline/runtime bandwidth & SNR, `cpu_variance`, `dropout_rate`, optional temperature/os‑noise).  
  - `data/processed/execution_runs.csv` – one row per successful run, conforms to the amended `execution-run.schema.yaml`.  
  - `code/analysis/data_validator.py` – scans `execution_runs.csv` for missing required columns; produces `data/raw/validation_status.json` mapping each `run_id` to `included`/`excluded` with reason (critical variable missing).  
  *Verification* – `python -m code.analysis.aggregate` finishes without error; a schema validator confirms every row passes; `validation_status.json` correctly flags any excluded runs.  

- [ ] **T012** Fit regression model, run ANOVA, and apply statistical safeguards  
  *Artifacts*  
  - `code/analysis/regression.py` – loads only “included” rows from `execution_runs.csv`, fits an OLS model with interaction terms (`granularity × cpu_variance`, `granularity × dropout_rate`, `injected_latency × node_count`), optionally adds quadratic terms, selects best model by AIC/BIC, computes VIF (reports any > 5), applies Benjamini‑Hochberg FDR to all p‑values, runs `anova_lm` for `throughput ~ C(granularity)`.  
  - `data/processed/regression_model.json` – conforms to `regression-model.schema.yaml` (coefficients, p_values, r_squared, residuals, placeholder `theoretical_bound_deviation` = 0.0).  
  - `data/processed/anova.json` – contains the granularity ANOVA table; p‑value must be < 0.05 to satisfy SC‑005.  
  *Verification* – both JSON files validate; `regression_model.json` includes `r_squared ≥ 0.0`; `anova.json` reports granularity p‑value < 0.05; any VIF > 5 appears in a logged warning but does not cause failure.  

- [ ] **T013** Compute Ong & Motani wireless capacity bound and integrate deviation into regression output  
  *Artifacts*  
  - `code/analysis/theoretical_bound.py` – for each run, uses measured `baseline_bandwidth_Mbps` and `baseline_snr_db` to compute Shannon capacity, derives `normalized_efficiency = throughput / capacity`, stores `theoretical_bound_deviation = throughput / capacity`. Flags any run with efficiency > 1.0 as a measurement‑error warning.  
  - `data/processed/theoretical_bound_validation.json` – per‑run capacity, efficiency, deviation, and any warnings.  
  - Updated `data/processed/regression_model.json` – `theoretical_bound_deviation` field filled with the mean deviation across runs.  
  *Verification* – JSON parses; at least one run shows efficiency ≤ 1.0; any efficiency > 1.0 appears under a `warnings` array.  

- [ ] **T014** Detect granularity “sweet spot” and generate study figures  
  *Artifacts*  
  - `code/analysis/sweet_spot.py` – reads `execution_runs.csv`, computes marginal throughput gain between successive granularity settings, compares to `sweet_spot_threshold` from `sweep_config.yaml`, writes `data/processed/sweet_spot.json` (`optimal_granularity`, `marginal_gain_curve`, `threshold`, `threshold_source`).  
  - `code/analysis/figures.py` – creates PNGs in `figures/`:  
    - `throughput_vs_nodes.png` (throughput curves per granularity).  
    - `coordination_overhead.png` (overhead ratio vs. granularity).  
    - `bound_comparison.png` (empirical throughput vs. theoretical capacity).  
  - `data/figures_manifest.yaml` – maps each figure file to the source CSV/JSON rows that produced it.  
  *Verification* – each PNG exists; the manifest references existing data rows; `pytest code/tests/test_figure_manifest.py` passes.  

- [ ] **T015** Write concise methods & results summary and verify full reproducibility  
  *Artifacts*  
  - `data/processed/methods_summary.md` – links to all primary artifacts, describes test‑bed size, hardware heterogeneity, calibration factors, regression equation, R², ANOVA significance, sweet‑spot granularity, bound deviation, excluded runs and reasons, and honest limitations (e.g., mock‑node environment, unmodeled confounders).  
  - `data/processed/reproducibility_log.txt` – output of a fresh run of the workflow exactly as described in `quickstart.md` (steps: `calibrate`, `run-single`, `sweep`, `aggregate`, `regression`, `theoretical-bound`, `sweet-spot`, `figures`). Shows that all tests pass and that SHA‑256 hashes of generated artifacts match those committed to the repository.  
  *Verification* – re‑run the workflow from a clean checkout; all tests pass; the reproducibility log records successful completion and the artifact hashes are identical to the repository versions.  

- [ ] **T016** Variable‑fit verification (SC‑006) integrated into aggregation pipeline  
  *Artifacts*  
  - `code/analysis/validation.py` – invoked by `aggregate.py`; ensures every required predictor (`cpu_variance`, `dropout_rate`, `node_count`, `granularity_setting`, `injected_latency`) and outcome (`total_throughput`) is present for each run; writes `data/raw/validation_status.json` with per‑run inclusion flags and reasons for exclusion.  
  - Updated `code/tests/integration/test_full_workflow.py` to assert that after `run-single` and after the sweep, `validation_status.json` exists and marks runs as “included” only when all critical variables are present.  
  *Verification* – validation step runs without error; `validation_status.json` correctly reflects SC‑006 requirements; integration test passes.  

---

## Dependency matrix (quick reference)

| Spec requirement | Tasks that satisfy it | Key artifact |
|------------------|-----------------------|--------------|
| FR‑001 (dynamic scheduler, heartbeats) | T004, T005 | `scheduler.py`, `dropout_events.json` |
| FR‑002 (tcpdump & mpstat instrumentation) | T003, T004, T008 | `instrumentor.py`, `run_001.csv` |
| FR‑003 (parameter sweep, injected latency) | T010 | `sweep_runner.py`, `run_*.csv` |
| FR‑004 (coordination‑overhead metric) | T004, T010, T011 | timestamps in task records, `execution_runs.csv` |
| FR‑005 (regression & ANOVA) | T012, T013, T014 | `regression_model.json`, `anova.json` |
| FR‑006 (theoretical bound) | T013 | `theoretical_bound_validation.json` |
| FR‑007 (hard CI timeout) | T006, T010 | `pipeline_runtime.json`, `timeout_enforced.log` |
| SC‑001 (R²) | T012 | `regression_model.json.r_squared` |
| SC‑002 (bound deviation) | T013 | `theoretical_bound_validation.json` |
| SC‑003 (sweet‑spot detection) | T014 | `sweet_spot.json` |
| SC‑004 (pipeline wall‑clock) | T006 | `pipeline_runtime.json` |
| SC‑005 (ANOVA significance) | T012 | `anova.json` |
| SC‑006 (variable completeness) | T011, T016 | `validation_status.json` |

**Execution order** (respecting data flow):  
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016.  

All tasks are unchecked (`[ ]`). Once a task is completed and its verification passes, the CI run can tick the box. This plan now satisfies every functional requirement, success criterion, and reviewer concern while remaining executable within the free‑tier CI budget.
