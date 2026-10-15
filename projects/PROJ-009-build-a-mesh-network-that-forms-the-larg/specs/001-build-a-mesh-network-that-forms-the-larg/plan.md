# Implementation Plan: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Branch**: `001-mesh-supercomputer` | **Date**: 2026-10-14 | **Spec**: `specs/001-mesh-supercomputer/spec.md`  
**Input**: Feature specification from `specs/001-mesh-supercomputer/spec.md`

## Summary
The project will deliver a reproducible research pipeline that (1) orchestrates a dynamic scheduler across a heterogeneous Wi‑Fi mesh of consumer devices, (2) instruments each node to capture wall‑clock time, packet counts, and CPU utilization, (3) performs a systematic parameter sweep over task granularity, node count, and injected network impairments, (4) aggregates the raw logs into a structured dataset, (5) fits a **multiple linear regression** with polynomial and interaction terms and runs **ANOVA** to quantify interaction effects, (6) validates the empirical scaling curve against the information‑theoretic capacity bound of Ong & Motani (2007) using a proper unit‑consistent conversion, and (7) records per‑node metadata for schema validation. All steps are designed to run on the free‑tier GitHub Actions runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h) with optional GPU off‑load (none required).

The plan explicitly addresses **every** functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006) and adds verifiable unit‑test and data‑generation tasks to remediate the previous verification failures (T001‑T004).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `paramiko` (SSH orchestration)  
  - `pandas` (data handling)  
  - `numpy` (numeric ops)  
  - `statsmodels` (OLS regression & ANOVA)  
  - `scipy` (multiple‑comparison correction)  
  - `pyyaml` (configuration)  
  - `pytest` (testing)  
  - `jsonschema` (contract validation)  
- **Storage**: CSV/JSON files under `data/` (raw logs, processed aggregates, model output).  
- **Testing**: `pytest` with contract tests (`jsonschema`) and extensive **mock‑node** unit tests covering all instrumentation functions.  
- **Target Platform**: Linux CI runner (GitHub Actions); remote Linux/ARM devices for the physical mesh.  
- **Performance Goals**: Complete full sweep (≤ 150 runs) and analysis within ≤ 6 h on the CI runner.  
- **Constraints**: No GPU, strict 6‑hour wall‑clock limit, all external data must be generated locally (self‑contained).  

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| **I. Reproducibility** | ✅ | Random seeds pinned; all code runnable from a fresh runner; no manual steps. |
| **II. Verified Accuracy** | ✅ | Ong & Motani (2007) citation will be validated by the Reference‑Validator Agent. |
| **III. Data Hygiene** | ✅ | Raw logs are immutable; derived files receive new filenames; checksums recorded in `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml`. |
| **IV. Single Source of Truth** | ✅ | Every figure/table traces back to a row in `data/processed/execution_runs.csv` and a line in `code/analysis/regression.py`. |
| **V. Versioning Discipline** | ✅ | Content hashes tracked; `updated_at` timestamps updated on artifact changes. |
| **VI. Simulation Fidelity and Validation** | ✅ | A lightweight **discrete‑event simulation** (SimPy) will be calibrated against the physical “golden dataset” (10‑node pilot) to satisfy the validation requirement. |
| **VII. Heterogeneity‑Aware Scheduling** | ✅ | Scheduler models CPU variance, latency variance, and dropout; regression includes interaction terms. |
| **VIII. Physical Node Metadata Capture** | ✅ | Instrumentation step writes `physical_node_<ip>.json` per node and validates against `contracts/physical-node.schema.yaml`. |

All principles are satisfied; no violations remain.

## Project Structure
```text
code/
├── orchestrator/
│   ├── __init__.py
│   ├── scheduler.py          # Dynamic granularity logic, fault handling
│   ├── node_manager.py       # SSH discovery, heartbeat, metric collection
│   ├── instrumentor.py       # tcpdump, mpstat wrappers, parsing utilities
│   └── cli.py                # Argparse entry‑point
├── analysis/
│   ├── __init__.py
│   ├── regression.py         # OLS regression with polynomial/interaction terms, ANOVA, residual diagnostics
│   └── theoretical_bound.py  # Ong & Motani bound calculation with bits‑per‑task conversion
├── simulation/
│   ├── __init__.py
│   └── des_model.py          # SimPy mesh model, calibration routine
├── data/
│   ├── raw/                  # Raw CSV logs per run + `physical_node_*.json`
│   └── processed/            # Aggregated CSV, JSON model, validation report
├── tests/
│   ├── unit/
│   │   ├── test_node_manager.py
│   │   ├── test_scheduler.py
│   │   └── test_instrumentor.py
│   ├── integration/
│   │   └── test_full_workflow.py   # Uses mock‑testbed
│   └── contract/
│       └── test_contracts.py
└── requirements.txt
```
**Structure Decision**: A single‑module repository under `code/` keeps the CI footprint small and aligns with the “research‑CLI” assumption (no UI needed).

## Complexity Tracking & Verification Remediation
| Issue | Original Failure | Revised Approach |
|-------|------------------|------------------|
| **T001** – test suite exit code 2 | Missing/incorrect test files; some modules lacked tests. | Add **complete unit‑test suites** for `node_manager`, `scheduler`, and `instrumentor` covering: SSH verification, CPU profiling (`mpstat` parsing), radio metrics (`iwconfig` parsing), packet counting (`tcpdump`), dropout detection, thermal metric extraction, and task re‑assignment logic. All tests run under `pytest -q`. |
| **T002** – insufficient unit tests | Only discovery tests existed. | Expand `test_node_manager.py` to include mock‑node generators with recorded `tcpdump`/`mpstat` samples; assert correct parsing and metric extraction. |
| **T003** – missing `data/raw/dropout_events.json` | Scheduler never emitted dropout file; `TaskAssignment` lacked `end_time`. | Introduce **explicit dropout logging** in `scheduler.py` that writes a JSON array of events (`node_id`, `timestamp`, `reason`, `reassigned_task_id`). Update `TaskAssignment` dataclass to include `end_time`. Unit tests verify file creation and schema compliance (`contracts/dropout-event.schema.yaml`). |
| **T004** – CLI crash | CLI argument handling incomplete. | Refactor `code/orchestrator/cli.py` to use `argparse` with sub‑commands (`run`, `sweep`, `validate`). Add defensive checks and informative error messages. Integration test (`test_full_workflow.py`) runs the CLI in mock mode and asserts successful exit. |
| **Physical Node Metadata** | No contract validation for `PhysicalNode`. | **Instrumentation stage** now writes `physical_node_<ip>.json` per discovered node and `tests/contract/test_contracts.py` validates these files against `contracts/physical-node.schema.yaml`. |

All revised tasks produce **deterministic artefacts** (CSV, JSON, model files) that are validated against schemas in `contracts/` before commit.

## Execution Strategy & CI Constraints
1. **Mock‑Testbed Generation** (`tests/integration/test_full_workflow.py`):  
   - Creates 15 virtual nodes with synthetic but realistic metric streams (latency, CPU, packet loss, temperature, OS noise).  
   - Runs the full sweep on the mock mesh; outputs `data/raw/mock_run_*.csv`, `data/raw/dropout_events.json`, and `data/raw/physical_node_*.json`.  
   - Guarantees CI can execute the entire pipeline without real hardware, satisfying verification while the *Physical Validation* job (manual) will later replace the mock data with real logs.

2. **Physical Validation (manual step)**:  
   - When a researcher has a real mesh, they invoke `python code/orchestrator/cli.py run --config config.yaml`.  
   - The same code path is used; only the data source changes from mock to real.  
   - Results are stored under `data/raw/real_*.csv`, `data/raw/dropout_events.json`, and `data/raw/physical_node_<ip>.json`.

3. **Data Aggregation** (`analysis/regression.py`):  
   - Reads all `data/raw/*.csv` and `physical_node_*.json`, computes per‑run metrics, writes `data/processed/execution_runs.csv`.  
   - Generates `data/processed/regression_model.json` (coefficients, p‑values, R², residuals, theoretical bound deviation).  
   - Writes `data/processed/theoretical_bound_validation.json`.

4. **Contract Validation** (`tests/contract/test_contracts.py`):  
   - Loads all JSON/CSV artefacts—specifically `physical_node_<ip>.json`, `dropout_events.json`, `execution_runs.csv`, and `regression_model.json`—and validates each against its corresponding schema in `contracts/` (e.g., `physical-node.schema.yaml`, `dropout-event.schema.yaml`, `execution-run.schema.yaml`, and `regression-model.schema.yaml`) using `jsonschema`.  
   - Fails the CI if any schema mismatch occurs.

5. **Time Budget**:  
 - Mock sweep (~several runs) [deferred].
   - Full sweep (≤ 150 runs) ≈ 4 h (benchmark duration per run calibrated to stay within the 6‑h CI limit).  
   - Analysis & validation ≤ 30 min.  

All steps are CPU‑tractable; no GPU escape hatch required.