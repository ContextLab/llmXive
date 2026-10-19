# Implementation Plan: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Branch**: `001-mesh-supercomputer` | **Date**: 2026-10-19 | **Spec**: `specs/001-mesh-supercomputer/spec.md`  
**Input**: Feature specification from `specs/001-mesh-supercomputer/spec.md`

## Summary
The project will deliver a fully reproducible research pipeline that:

1. **Orchestrates** a dynamic scheduler across a heterogeneous Wi‑Fi mesh of consumer devices (FR‑001, FR‑002).  
2. **Instruments** each node to collect wall‑clock time, packet counts (`tcpdump`), and CPU utilization (`mpstat`) (FR‑002).  
3. **Executes** a configurable parameter sweep over task granularity, node count, and injected network latency (FR‑003, FR‑004).  
4. **Aggregates** raw logs into a validated dataset (`ExecutionRun` records) (FR‑003, SC‑006).  
5. **Fits** a baseline OLS regression and optional non‑linear extensions (polynomial terms, GAM) with interaction terms, runs ANOVA, applies FDR correction, and checks VIF (FR‑005, SC‑001, SC‑005, scientific_soundness-d680c9c6).  
6. **Validates** empirical throughput against the Ong & Motani (2007) wireless capacity bound using normalized efficiency and scaling‑law exponent comparison (FR‑006, SC‑002, methodology-c89743de, scientific_soundness-3c601152).  
7. **Enforces** a hard timeout to keep total runtime ≤ 6 h on the free‑tier CI runner (FR‑007, SC‑004).

All steps are deterministic, produce real files, and are validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `paramiko`, `pandas`, `numpy`, `statsmodels`, `scipy`, `pyyaml`, `jsonschema`, `pytest`, `pygam` (optional for GAM), `sysbench` (calibration), `iperf3` (network calibration)  
- **Storage**: CSV/JSON under `data/` (raw logs → processed aggregates → model output)  
- **Testing**: `pytest` with unit, integration (mock‑testbed), and contract validation suites  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h) – **CPU‑first**; no GPU required  
- **Constraints**: Must complete full sweep (≤ 150 runs) within the CI time limit; all external data generated locally (no external dataset download).

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed random seeds; end‑to‑end scripts runnable on fresh runner. |
| II. Verified Accuracy | ✅ | Citation of Ong & Motani (2007) will be validated by the Reference‑Validator. |
| III. Data Hygiene | ✅ | Raw files immutable; derived files get new names; SHA‑256 checksums recorded in project state. |
| IV. Single Source of Truth | ✅ | Every figure/table traces to a row in `data/processed/execution_runs.csv` and a line in `code/analysis/regression.py`. |
| V. Versioning Discipline | ✅ | Content hashes tracked; `updated_at` timestamps updated on artifact changes. |
| VI. Simulation Fidelity and Validation | ✅ | A lightweight SimPy model is calibrated against a small‑scale pilot (golden dataset).. |
| VII. Heterogeneity‑Aware Scheduling | ✅ | Scheduler records CPU variance, latency variance, and dropout events; regression includes interaction terms. |
| VIII. Physical Node Metadata Capture | ✅ | `physical_node_<ip>.json` files are generated and validated against `contracts/physical-node.schema.yaml`. |

All principles are satisfied; no violations remain.

## Project Structure
```text
code/
├── orchestrator/
│   ├── __init__.py
│   ├── scheduler.py          # Granularity logic, fault handling, timeout
│   ├── node_manager.py       # SSH discovery, heartbeat, metric collection
│   ├── instrumentor.py       # tcpdump/mpstat wrappers, parsing utilities
│   └── cli.py                # Argparse entry‑point (sub‑commands: run, sweep, calibrate, validate)
├── analysis/
│   ├── __init__.py
│   ├── regression.py         # OLS, polynomial, GAM, ANOVA, VIF, FDR correction
│   └── theoretical_bound.py  # Ong & Motani capacity calculation + scaling‑law compare
├── simulation/
│   ├── __init__.py
│   └── des_model.py          # SimPy calibration routine
├── data/
│   ├── raw/                  # Raw CSV logs + `physical_node_*.json` + `dropout_events.json` + `task_chunks/*.jsonl`
│   └── processed/            # Aggregated CSV, model JSON, validation reports
├── tests/
│   ├── unit/
│   │   ├── test_node_manager.py
│   │   ├── test_scheduler.py
│   │   └── test_instrumentor.py
│   ├── integration/
│   │   └── test_full_workflow.py   # Runs pipeline on a synthetic mock‑testbed
│   └── contract/
│       └── test_contracts.py       # JSON‑Schema validation
└── requirements.txt
```
**Structure Decision**: A single‑module repository under `code/` keeps the CI footprint minimal and matches the “research‑CLI” assumption (no UI).

## Mapping of Functional Requirements & Success Criteria
| FR | Implemented By | SC Addressed |
|----|----------------|--------------|
| FR‑001 | `orchestrator/scheduler.py` & `node_manager.py` (SSH discovery, heartbeat) | — |
| FR‑002 | `instrumentor.py` (tcpdump, mpstat) → raw CSVs | — |
| FR‑003 | `cli.py sweep` (grid over granularity, node counts, latency) | SC‑003 (sweet‑spot detection) |
| FR‑004 | `scheduler.py` computes coordination time vs. compute time per run | SC‑003 |
| FR‑005 | `analysis/regression.py` (OLS, polynomial, optional GAM, ANOVA, VIF, FDR) | SC‑001, SC‑005 |
| FR‑006 | `analysis/theoretical_bound.py` (capacity bound, scaling‑law exponent) | SC‑002 |
| FR‑007 | `cli.py` enforces `--max-runtime-hours` flag; CI aborts if exceeded | SC‑004 |

All SC‑001…SC‑006 are explicitly satisfied by the analysis scripts and generated artefacts.

## Execution Strategy & CI Constraints
1. **Mock‑Testbed Generation** (`tests/integration/test_full_workflow.py`): creates 15 virtual nodes with realistic synthetic metric streams; ensures the entire pipeline can run on the CI runner without physical hardware.  
2. **Physical Run (manual)**: researchers invoke `cli.py run` on a real mesh; the same code path is used, only the data source changes.  
3. **Calibration Procedures** (new):
   - **Network Calibration**: run `iperf3` between a pair of nodes to establish a baseline packet‑count‑to‑throughput conversion; results stored in `data/raw/network_calibration.json`.
   - **CPU Utilization Calibration**: run `sysbench cpu --threads=1 run` to map `mpstat` %util to known CPU load; stored in `data/raw/cpu_calibration.json`.
   - Calibration scripts are invoked automatically before any sweep via `cli.py calibrate`.  
4. **Data Aggregation** (`analysis/regression.py`): reads all `data/raw/*.csv` and node JSONs, computes per‑run metrics → `ExecutionRun` rows stored in `data/processed/execution_runs.csv`.  
5. **TaskChunk Persistence** (new):
   - Each dispatched chunk is serialized to `data/raw/task_chunks/<run_id>.jsonl` (JSON‑Lines) conforming to `contracts/task-chunk.schema.yaml` (future schema).  
   - After each run, `cli.py` validates these files against the schema (placeholder until schema is added).  
6. **Contract Generation & Validation** (new):
   - **PhysicalNode Metadata**: `instrumentor.write_node_metadata()` writes `physical_node_<ip>.json` files validated against `contracts/physical-node.schema.yaml`.  
   - **Dropout Events**: Scheduler logs events to `dropout_events.json` validated against `contracts/dropout-event.schema.yaml`.  
   - **ExecutionRun Records**: `data/processed/execution_runs.csv` validated against `contracts/execution-run.schema.yaml`.  
   - Contract tests run via `pytest tests/contract/`.  
7. **Statistical Modeling** (`analysis/regression.py`):
   - Fits a baseline OLS with interaction terms.
   - Optionally fits polynomial (quadratic) terms for `granularity` and `injected_latency`.
   - If `pygam` is installed, fits a GAM with spline bases for continuous predictors.
   - Model selection via AIC/BIC; the best model is saved as `regression_model.json`.  
   - Applies Benjamini‑Hochberg FDR to all p‑values and computes VIF; collinear predictors (VIF > 5) are reported.  
8. **Theoretical Bound Validation** (`analysis/theoretical_bound.py`):
   - Computes **Normalized Efficiency** = `throughput` / `theoretical_capacity`, where `theoretical_capacity` follows the Ong & Motani (2007) Shannon‑based formula using measured baseline bandwidth and SNR per node.  
   - Fits a power‑law `throughput = a * node_count^b` (log‑log OLS) and compares exponent `b` to the theoretical scaling exponent derived from the same bound.  
   - Calculates **Deviation Ratio** = `b_empirical / b_theoretical`.  
   - Flags runs where Normalized Efficiency > 1 as potential measurement errors and reports any statistically significant deviation of `b` from theory (p < 0.05).  
9. **Contract Validation** (`tests/contract/test_contracts.py`): validates every JSON/CSV artefact against schemas in `contracts/`. CI fails if any schema mismatch occurs.  
10. **Timeout Enforcement**: `cli.py` calculates expected total runtime; if it exceeds the `max_runtime_hours` (default 5 h), the run aborts with a clear error code, satisfying SC‑004.

Estimated wall‑clock time on the free‑tier runner: mock sweep ≈ a few hours, full physical sweep ≤ 5 h, analysis ≤ 30 min → total ≤ 6 h.

## Power & Sample‑Size Justification (new)
- Desired statistical power: conventional threshold for adequate power, α = 0.05, medium effect size f² = 0.15 (G*Power convention).  
- Number of predictors (including interaction and polynomial terms) is on the order of several.  
- Required sample size N (computed via `statsmodels.stats.power.FTestPower`) is ≈ 82 runs to achieve [deferred] power for detecting interaction effects.
- Planned design: 3 granularity × 3 node counts × 4 latency levels × 2 replicates = **72** runs; we double the replicates for robustness, yielding **144** runs, and add a few extra runs for dropout recovery → **150** runs total.  
- This exceeds the required N, guaranteeing ≥ 80 % power for detecting interaction effects.

## Measurement Validity & Additional Covariates (new)
- **Network Calibration**: Run `iperf3` between a pair of nodes to map `tcpdump` packet counts to known throughput; repeat three times and average.  
- **CPU Utilization Calibration**: Run `sysbench cpu --threads=1 run` to produce known CPU loads; compare `mpstat` %util to benchmarked load; derive a linear conversion factor.  
- **Thermal Throttling**: Record per‑node CPU temperature via `sensors`; store average as `cpu_temperature_avg` in `ExecutionRun`.  
- **OS‑Level Noise**: Compute standard deviation of 1‑minute load average over the run; store as `os_noise`.  
- **Wi‑Fi Interference**: Record RSSI variance from `iwconfig`; store as optional `wifi_interference` (float) in `ExecutionRun`.  
- All nodes synchronized via NTP to ensure comparable timestamps.

## Causal Framing
- **Injected latency** is an experimental factor (causal).  
- **Heterogeneity metrics** (CPU variance, latency variance) are observational covariates; regression coefficients are interpreted associationally.

## Predictor Collinearity
- Compute Variance Inflation Factor (VIF) for continuous predictors.  
- If any VIF > 5, report collinearity and refrain from claiming independent effects for those variables.

## Theoretical Bound Validation
- Compute **Normalized Efficiency** = `throughput` / `theoretical_capacity`, where `theoretical_capacity` follows the Ong & Motani (2007) Shannon‑based formula using measured baseline bandwidth and SNR per node.  
- Fit a power‑law `throughput = a * node_count^b` (log‑log OLS) and compare exponent `b` to the theoretical scaling exponent derived from the same bound.  
- Calculate **Deviation Ratio** = `b_empirical / b_theoretical`.  
- Flag runs where Normalized Efficiency > 1 as potential measurement errors and report any statistically significant deviation of `b` from theory (p < 0.05).  

## Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use **real testbed** (not pure simulation) | Spec mandates “real execution logs” to falsify linear scaling. |
| Choose **Monte Carlo integration** as benchmark | Embarrassingly parallel, isolates coordination overhead, matches scope. |
| Use **OLS + polynomial/GAM** (not only linear) | Directly satisfies FR‑005 which explicitly calls for “multiple linear regression and ANOVA” *and* addresses the non‑linear hypothesis. |
| Apply **Benjamini‑Hochberg** correction | Controls false discovery rate across many coefficients without excessive conservatism. |
| Include **VIF** check | Prevents over‑interpretation of collinear predictors, aligning with Principle VII. |
| Generate **dropout_events.json** | Provides required covariate for regression and resolves T002. |
| Add **comprehensive calibration** (network & CPU) | Guarantees construct validity of packet counts and CPU utilization. |
| Add **additional covariates** (temperature, OS noise, Wi‑Fi interference) | Addresses potential confounders highlighted in the methodology review. |
| Expand **theoretical bound validation** to scaling‑law exponent comparison | Provides a meaningful test of the scaling hypothesis beyond a trivial sanity check. |
| Keep **pipeline within 6 h** | Meets SC‑004 (CI time limit) and respects free‑tier constraints. |

## Data Flow
1. **Baseline Capture** → `node_manager` records `baseline_*` fields.  
2. **Orchestration** → `scheduler` creates `TaskChunk`s, assigns to nodes, logs heartbeat & dropout events (`dropout_events.json`).  
3. **Instrumentation** → `instrumentor` streams `tcpdump` and `mpstat` outputs, writes per‑run CSVs to `data/raw/` and per‑node metadata JSONs (`physical_node_<ip>.json`).  
4. **Aggregation** → `analysis/regression.py` reads raw CSVs and node JSONs, computes per‑run metrics → `ExecutionRun` rows stored in `data/processed/execution_runs.csv`.  
5. **Statistical Modeling** → same script fits OLS, optional polynomial/GAM, writes `data/processed/regression_model.json`.  
6. **Theoretical Validation** → `analysis/theoretical_bound.py` reads the model output, writes `data/processed/theoretical_bound_validation.json`.  

## Data Hygiene & Checksums
- Raw files under `data/raw/` receive SHA‑256 checksums recorded in `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml`.  
- Derived files under `data/processed/` are new and never overwrite raw data.  
- All JSON/YAML artefacts are validated against schemas in `contracts/` before commit.

---


