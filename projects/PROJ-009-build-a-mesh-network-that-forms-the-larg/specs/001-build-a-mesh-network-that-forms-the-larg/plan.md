# Implementation Plan: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Branch**: `001-mesh-supercomputer` | **Date**: 2026-10-21 | **Spec**: `specs/001-mesh-supercomputer/spec.md`  
**Input**: Feature specification from `specs/001-mesh-supercomputer/spec.md`

## Summary
The project delivers a fully reproducible research pipeline that:

1. **Orchestrates** a dynamic scheduler across a heterogeneous Wi‑Fi mesh of consumer devices (FR‑001, FR‑002).  
2. **Instruments** each node to collect wall‑clock time, network packet counts (`tcpdump`), and CPU utilization (`mpstat`) (FR‑002).  
3. **Executes** a configurable parameter sweep over task granularity, node count, and injected network latency (FR‑003, FR‑004).  
4. **Generates** deterministic mock data (synthetic logs, JSON metadata) for CI verification, while supporting a manual *real‑hardware* run for final scientific results.  
5. **Aggregates** raw logs into `ExecutionRun` records, validates them against JSON‑Schema contracts, and stores them under `data/processed/`.  
6. **Fits** OLS regression, optional polynomial/GAM extensions, runs ANOVA, applies Benjamini‑Hochberg FDR correction, checks VIF for collinearity, and uses a mixed‑effects model with node as a random effect (FR‑005, SC‑001, SC‑005).  
7. **Validates** empirical throughput against the Ong & Motani (2007) wireless capacity bound (FR‑006, SC‑002).  
8. **Enforces** a hard timeout for the entire pipeline (FR‑007, SC‑004).  
9. **Performs** a Variable‑Fit Verification step to ensure every required predictor and outcome is present before regression (SC‑006).

All artifacts are deterministically generated, schema‑validated, and can be re‑run on a fresh GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤ 6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `paramiko`, `pandas`, `numpy`, `statsmodels`, `scipy`, `pyyaml`, `jsonschema`, `pytest`, `pygam` (optional), `sysbench`, `iperf3`, `tc`, `mpstat`, `tcpdump`, `sensors`, `iwconfig`  
- **Storage**: CSV/JSON under `data/` (raw → processed)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑first; no GPU required)  
- **Constraints**: Entire pipeline ≤ 6 h on free‑tier CI; all external data generated locally.  

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds; end‑to‑end scripts runnable on fresh runner. |
| II. Verified Accuracy | ✅ | All citations (Ong & Motani 2007) will be validated by the Reference‑Validator. |
| III. Data Hygiene | ✅ | Raw files immutable; derived files get new names; SHA‑256 checksums recorded. |
| IV. Single Source of Truth | ✅ | Every figure/table traces to a row in `data/processed/execution_runs.csv` and a line in `code/analysis/*.py`. |
| V. Versioning Discipline | ✅ | Content hashes tracked; `updated_at` timestamps updated on changes. |
| VI. Simulation Fidelity and Validation | ✅ | Mock testbed runs (synthetic but statistically realistic) are validated against a small real pilot (of modest size) before final analysis. |
| VII. Heterogeneity‑Aware Scheduling | ✅ | Scheduler records CPU variance, latency variance, and dropout events; regression includes interaction terms (associational). |
| VIII. Physical Node Metadata Capture | ✅ | `physical_node_<ip>.json` files generated and validated against `contracts/physical-node.schema.yaml`. |

All principles are satisfied; no violations remain.

## Project Structure
```text
code/
├── orchestrator/
│   ├── __init__.py
│   ├── scheduler.py          # Granularity logic, fault handling, timeout
│   ├── node_manager.py       # SSH discovery, heartbeat, metric collection
│   ├── instrumentor.py       # tcpdump/mpstat wrappers, parsing utilities
│   ├── calibration.py        # Network & CPU calibration utilities
│   └── cli.py                # Argparse entry‑point (sub‑commands: run, sweep, calibrate, mock)
├── analysis/
│   ├── __init__.py
│   ├── regression.py         # OLS, polynomial, GAM, mixed‑effects, ANOVA, VIF, FDR
│   └── theoretical_bound.py  # Ong & Motani capacity calculation + scaling‑law comparison
├── simulation/
│   └── des_model.py          # Simple SimPy model for pilot validation
├── data/
│   ├── raw/
│   │   ├── run_*.csv
│   │   ├── physical_node_*.json
│   │   ├── dropout_events.json
│   │   ├── task_chunks/
│   │   │   └── *.jsonl
│   │   ├── network_calibration.json
│   │   └── cpu_calibration.json
│   └── processed/
│       ├── execution_runs.csv
│       ├── regression_model.json
│       └── theoretical_bound_validation.json
├── tests/
│   ├── unit/
│   │   ├── test_node_manager.py
│   │   ├── test_scheduler.py
│   │   ├── test_instrumentor.py
│   │   └── test_calibration.py
│   ├── integration/
│   │   └── test_full_workflow.py   # Runs mock pipeline end‑to‑end
│   └── contract/
│       └── test_contracts.py       # JSON‑Schema validation
├── contracts/
│   ├── dropout-event.schema.yaml
│   ├── execution-run.schema.yaml
│   ├── physical-node.schema.yaml
│   ├── regression-model.schema.yaml
│   └── task-chunk.schema.yaml
└── requirements.txt
```
**Structure Decision**: A single‑module repository under `code/` keeps the CI footprint minimal and matches the “research‑CLI” assumption (no UI).

## Mapping of Functional Requirements & Success Criteria
| FR | Implemented By | SC Addressed |
|----|----------------|--------------|
| FR‑001 | `orchestrator/scheduler.py` & `node_manager.py` (SSH discovery, heartbeat) | — |
| FR‑002 | `instrumentor.py` (tcpdump, mpstat) → raw CSVs | — |
| FR‑003 | `cli.py sweep` (grid over granularity, node counts, latency) | SC‑003 (sweet‑spot detection) |
| FR‑004 | `scheduler.py` computes coordination vs. compute time per run | SC‑003 |
| FR‑005 | `analysis/regression.py` (OLS, polynomial, optional GAM, ANOVA, VIF, FDR, mixed‑effects) | SC‑001, SC‑005 |
| FR‑006 | `analysis/theoretical_bound.py` (capacity bound, scaling‑law comparison) | SC‑002 |
| FR‑007 | `cli.py` enforces `--max-runtime-hours`; `runtime_tracker.py` logs total runtime and aborts if exceeded | SC‑004 |
| FR‑008 (new) | Variable‑Fit Verification script (`verification.py`) that checks required columns before regression | SC‑006 |
| SC‑001 | Regression model output includes R², p‑values (generated in `regression_model.json`) | — |
| SC‑002 | Theoretical bound deviation stored in `theoretical_bound_validation.json` | — |
| SC‑003 | Coordination overhead ratio computed per run; sweet‑spot identified in analysis script | — |
| SC‑004 | Timeout enforcement tested in integration suite (`test_watchdog_overrun.py`) | — |
| SC‑005 | ANOVA p‑value < 0.05 flagged; FDR applied to all coefficients | — |
| SC‑006 | Full variable‑fit check performed in `verification.py`; runs missing critical variables are logged WARN and excluded from regression | — |

## Execution Strategy & CI Constraints
The pipeline is split into **CI‑verified mock stages** and an **optional manual physical stage**.

### Phase 0 – Environment & Configuration (Deterministic)
1. **Create `config.yaml`** (sample provided in `quickstart.md`).  
2. **Run `pytest -q`** to confirm all unit, integration, and contract tests pass on the CI runner.  
3. **Generate synthetic fixture logs** (`tests/fixtures/sample_tcpdump.log`, `sample_mpstat.log`, `sample_iwconfig.log`, `sample_sensors.log`, `sample_ping.log`) matching real‑tool output formats. These are used by `test_instrumentor.py`.  
4. **Validate contracts** with `pytest tests/contract/` – ensures schemas are syntactically correct and files exist.

### Phase 1 – Calibration (CPU‑first)
- `python -m code.orchestrator.calibration --config config.yaml`  
  - **Network calibration**: runs `iperf3` between two local mock endpoints, writes `data/raw/network_calibration.json`. Linear regression between packet count and known throughput is stored; a lack‑of‑linearity warning is emitted.  
  - **CPU calibration**: runs `sysbench cpu --threads=1 run`, writes `data/raw/cpu_calibration.json`. Linear fit between `mpstat` % and known CPU load is stored.  
- Unit test `test_calibration.py` confirms both files contain numeric conversion factors and that linearity R² ≥ 0.9; otherwise the pipeline aborts.

### Phase 2 – Mock Testbed Execution (Core CI‑verified workflow)
- **Command**: `python -m code.orchestrator.cli mock --config config.yaml`  
  - Generates a synthetic mesh of *N* virtual nodes (default 15) with realistic heterogeneity distributions (CPU speed, latency, packet loss).  
  - Dispatches `TaskChunk`s, records `dropout_events.json` (including heartbeat loss, OOM, sleep, network saturation).  
  - Writes per‑node metadata `physical_node_<id>.json`.  
  - Emits raw CSV `data/raw/run_<id>.csv` and `task_chunks/<run_id>.jsonl`.  
  - **Variable‑Fit Verification**: after each run, `verification.py` checks that all required columns (`throughput`, `cpu_variance`, `latency_variance`, `injected_latency`, `node_count`) are present; missing critical columns cause a WARN and the run is excluded from downstream regression.  
  - All files are validated against the five contracts immediately after creation.  
  - The mock run also produces `data/runtime/pipeline_runtime.json` and `data/runtime/timeout_enforced.log` via `runtime_tracker.py`.

### Phase 3 – Full Parameter Sweep (research‑scale, CI‑verified)
```bash
python -m code.orchestrator.cli sweep --config config.yaml
```
- Executes every combination of granularity, node count, and injected latency (default 4 replicates each).  
- After each run, the same calibration factors are applied, and aggregated metrics are stored under `data/processed/`.  
- **Power & Sample‑Size Justification** (see below) ensures ≥ 80 % power after accounting for clustering.

### Phase 4 – Physical Testbed (Manual, not part of CI)
- Researchers run the same CLI with `run` sub‑command on their real mesh.  
- Because the CI runner cannot reach the physical devices, this stage is **optional for CI**; the pipeline code path is identical, guaranteeing reproducibility.  
- The same analysis scripts (Phase 5) are applied to the real logs, producing the final scientific results.

### Phase 5 – Analysis (runs on either real or mock data)
```bash
# Aggregate and fit regression
python -m code.analysis.regression \
  --input data/raw/ \
  --output data/processed/

# Theoretical bound validation
python -m code.analysis.theoretical_bound \
  --input data/processed/execution_runs.csv \
  --output data/processed/
```
*Outputs*:  
- `data/processed/execution_runs.csv` (one row per configuration).  
- `data/processed/regression_model.json` (coefficients, p‑values, R², VIF, FDR‑adjusted p‑values, mixed‑effects variance components).  
- `data/processed/theoretical_bound_validation.json` (normalized efficiency, scaling‑law exponent comparison, deviation flags).  

### Phase 6 – Variable‑Fit Verification (new)
- `python -m code.analysis.verification --input data/raw/ --output data/processed/validation_status.json`  
- Confirms that every predictor required by the regression (CPU variance, latency variance, injected latency, node count, granularity) and the outcome (throughput) are present.  
- If a run lacks a *critical* variable (throughput, latency, or CPU variance), it is logged as WARN and excluded from the regression dataset. Optional covariates may be missing without causing exclusion.

### Phase 7 – Testing
```bash
# Unit tests
pytest tests/unit/ -v

# Contract (schema) tests
pytest tests/contract/ -v

# Integration test (mock pipeline end‑to‑end)
pytest tests/integration/ -v --mock-testbed
```
All tests must exit with status 0; CI will fail otherwise.

## Power & Sample‑Size Justification (updated)
- Desired **≥ 80 % power**, α = 0.05, medium effect size f² = 0.15 (G*Power convention).  
- Required **N ≈ 82** independent runs for detecting interaction effects.  
- **Clustering adjustment**: runs share nodes, inducing intra‑class correlation (ICC ≈ 0.05). Design effect ≈ 1 + (m − 1)·ICC, where *m* ≈ 4 (average runs per node). Design effect ≈ 1.15, so effective N = total / 1.15.  
- **Planned design**: 3 granularity × 3 node counts × 4 latency levels × 4 replicates = 144 runs.  
- **Extra dropout‑recovery runs**: 36 runs (one extra per configuration) → **total 180 runs**. Effective N ≈ 180 / 1.15 ≈ 156 > 82, satisfying the power requirement even after accounting for clustering.  
- The mixed‑effects model (node as random effect) further protects against residual intra‑node correlation.

## Measurement Validity (new)
- **Network calibration**: `iperf3` between a pair of nodes maps `tcpdump` packet counts to known throughput; linear regression is performed and R² ≥ 0.9 is required.  
- **CPU calibration**: `sysbench cpu --threads=1 run` provides known CPU loads; linear regression between `mpstat` % and load is performed; R² ≥ 0.9 required.  
- **Throughput derivation**: Primary outcome is computed from *task‑completion timestamps* (wall‑clock time per chunk) rather than raw packet counts alone. Packet‑count data are used only as a secondary consistency check against the calibrated conversion factor.  
- **Validation checks**: Both calibrations are rerun on each CI execution; failures abort the pipeline with a clear error message.

## Statistical Analysis Plan (updated)
1. **Baseline OLS** (`statsmodels.api.OLS`) with predictors: `node_count`, `granularity` (categorical), `injected_latency`, `cpu_variance`, `latency_variance`, and interaction terms `granularity:cpu_variance`, `granularity:latency_variance`.  
2. **Mixed‑effects extension** (`statsmodels.regression.mixed_linear_model.MixedLM`) adding a random intercept for `node_id` to account for within‑node correlation.  
3. **Non‑Linear Extensions** (selected by AIC/BIC):  
   - **Polynomial**: quadratic terms for `granularity` (encoded numerically) and `injected_latency`.  
   - **GAM**: if `pygam` is installed, spline bases for continuous predictors.  
4. **Model Selection**: lowest AIC/BIC retains the final model.  
5. **ANOVA** (`statsmodels.stats.anova.anova_lm`) on the selected model to test overall granularity effect.  
6. **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied to all coefficient p‑values (`statsmodels.stats.multitest.multipletests`).  
7. **Collinearity Check**: VIF computed for all continuous predictors; any VIF > 5 reported and the corresponding coefficient is not claimed as an independent effect.  
8. **Associational Framing**: Heterogeneity metrics are treated as observational covariates; injected latency is the only experimental factor. All effect statements are explicitly labeled as *associational*.

## Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Split pipeline into **mock CI‑verified** and **manual physical** stages | Resolves the structural contradiction highlighted by reviewers: CI can verify deterministic artefacts while the real testbed provides the scientific data. |
| Use **Monte Carlo integration** as benchmark | Embarrassingly parallel, isolates coordination overhead, matches scope. |
| Include **calibration** (network & CPU) | Guarantees construct validity of packet‑count and CPU‑util metrics (required by SC‑006). |
| Apply **Benjamini‑Hochberg** FDR correction | Controls false discoveries across many coefficients without excessive conservatism. |
| Add **VIF** check | Prevents over‑interpretation of collinear predictors (Principle VII). |
| Generate **dropout_events.json** and **task_chunks/*.jsonl** | Satisfies T003, T001, and provides the dropout covariate required by regression. |
| Provide **sample fixture logs** (tcpdump, mpstat, iwconfig, sensors, ping) | Satisfies T014 and enables unit tests without real hardware. |
| Implement **runtime_tracker** producing JSON and log files | Satisfies T011 (timeout enforcement evidence). |
| Create **network & CPU calibration JSON** files | Satisfies T015 and supplies conversion factors for analysis. |
| Ensure **config.yaml** exists and is version‑controlled | Satisfies T001 (test suite expects it). |
| Adjust contract tests to use `TaskChunkStore.base_dir` instead of `ProjectPaths.root` | Fixes T016 failure. |
| Produce **run_001.csv**, **task_chunks/run_001.jsonl**, **validation_status.json** via mock run | Satisfies T004. |
| Add **Variable‑Fit Verification** phase | Directly addresses SC‑006 and ensures dataset‑variable fit. |
| Reconcile power‑analysis totals to **180 runs** and account for clustering | Guarantees the claimed ≥ 80 % power under realistic correlation structure. |
| Clarify **associational** interpretation of heterogeneity effects | Removes unsupported causal claims per methodology‑8ff4adb8. |
| Add explicit **measurement‑validity** steps | Addresses methodology‑a05aa0de concerns about construct validity. |

## Complexity Tracking
No additional complexity beyond what is required by the spec; all new steps are deterministic, unit‑tested, and scoped to the free‑tier CI limits.

---

