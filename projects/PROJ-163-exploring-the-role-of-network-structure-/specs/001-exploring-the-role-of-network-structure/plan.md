# Implementation Plan: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Branch**: `001-explore-network-structure-superconducting-qubit-coupling` | **Date**: 2024-10-16 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/spec.md`

## Summary
The project will quantitatively assess the **associational** relationship between the physical connectivity topology of superconducting quantum processors (derived from IBM Quantum backend coupling maps) and their contemporaneous performance metrics (T₁, T₂, gate errors, readout error). All analysis is cross‑sectional: topology and performance are extracted from the **same** calibration snapshot. Robustness is evaluated via Leave‑One‑Device‑Out (LODO) and an extended performance‑window comparison. (fulfilling SC‑004). Minimum Detectable Effect Size (MDES) will be computed; if MDES > 0.5 the study is flagged **exploratory** and **no claim of statistical significance** will be made—only effect‑size estimates with permutation‑based confidence intervals are reported.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `qiskit-ibm-runtime`, `networkx`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `pingouin`, `pytest`  
- **Storage**: Files under `data/` (raw JSON snapshots, processed CSVs, PNG figures)  
- **Testing**: `pytest` unit & integration tests; schema validation against contracts in `contracts/`  
- **Target Platform**: Linux (`ubuntu-latest`) GitHub Actions runner (CPU‑only)  
- **Constraints**: Respect IBM API rate limits (C‑001), exclude data older than 30 days (FR‑001), no synthetic data (NFR‑002), reproducibility via fixed seeds (Constitution I).  
- **Scale/Scope**: All publicly accessible IBM back‑ends (≈ tens of devices), total raw JSON < 2 MB.

## Constitution Check
| Principle | Status | Action / Verification |
|---|---|---|
| I. Reproducibility | PASS | Fixed random seeds, deterministic scripts, pinned dependencies. |
| II. Verified Accuracy | PASS | All citations will be validated by the Reference‑Validator Agent. |
| III. Data Hygiene | PASS | Raw JSON saved with SHA‑256 checksums; derived CSVs are new files. |
| IV. Single Source of Truth | PASS | Figures/tables generated directly from processed CSVs. |
| V. Versioning Discipline | PASS | `hygiene.py` updates `state/projects/...yaml` with artifact hashes. |
| VI. Calibration Data Integrity | PASS | Timestamp recorded for each snapshot; freshness filter applied (FR‑001). |
| VII. Topology Representation Fidelity | PASS | Graph built directly from `coupling_map` without abstraction. |

## Project Structure
```text
specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── correlation_results.schema.yaml
│   ├── graph_metrics.schema.yaml
│   ├── performance_metrics.schema.yaml
│   └── mdes_report.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-163-exploring-the-role-of-network-structure-/
├── code/
│   ├── __init__.py
│   ├── fetcher.py           # FR‑001, FR‑002
│   ├── graph_builder.py     # FR‑003
│   ├── stats_engine.py      # FR‑004, MDES, robustness
│   ├── viz.py               # Figure generation (part of Reporting)
│   ├── hygiene.py           # Supports FR‑001 & Constitution I
│   └── main.py              # Orchestration
├── data/
│   ├── raw/                 # JSON snapshots (current + historical)
│   └── processed/           # CSVs, PNGs
├── tests/
│   ├── test_fetcher.py
│   ├── test_graph_builder.py
│   ├── test_stats_engine.py
│   └── test_integration_fetch.py
└── requirements.txt
```

## Implementation Phases (FR/SC Coverage)

| Phase | Description | FR(s) / SC(s) Addressed |
|---|---|---|
| **Data Ingestion** | Fetch current and up‑to‑30‑day historical calibration snapshots; filter by freshness; store raw JSON. | FR‑001, FR‑002 |
| **Metric Extraction** | Parse JSON → `performance_metrics.csv` (includes `source_window` column “current”); compute per‑device aggregates (mean T₁, T₂, CX error, readout error). | FR‑002 |
| **Graph Construction** | Build undirected `networkx.Graph` from coupling map; compute metrics (average shortest‑path length, diameter, global clustering coefficient, mean edge betweenness, **degree assortativity**, **spectral gap**). For disconnected graphs, path‑length metrics are computed on the largest component; `is_finite` flag and `component_size` are recorded to handle NaN/Inf cases. | FR‑003 |
| **Statistical Analysis** | **Primary Test**: Spearman rank correlation (ρ) between each graph metric and each performance metric. <br> **Exact/Permutation p‑values**: If N < 30, use a permutation test (10 000 permutations) to obtain p‑values and 95 % CI; otherwise use the exact Spearman p‑value. <br> **Partial Correlation**: Control for `chip_generation`, `qubit_count`, `device_age_days`, `readout_architecture`, **timestamp**, and (if available) `temperature` via `pingouin.partial_corr`. <br> **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR (α = 0.05). <br> **Robustness Checks**: LODO, chip‑family exclusion, 30‑day performance‑window comparison (using rows with `source_window="window"`), longitudinal stability assessment. <br> **Power / MDES**: Compute MDES for Spearman ρ given N and number of tests; write results to `power_analysis.csv` per `contracts/mdes_report.schema.yaml`. <br> **Exploratory Flag**: If `min_detectable_rho` > 0.5, label the study exploratory and **do not claim statistical significance**; report only effect sizes with permutation‑CI. | FR‑004, SC‑004 |
| **Reporting** | Generate `correlation_results.csv` (`contracts/correlation_results.schema.yaml`), `power_analysis.csv` (`contracts/mdes_report.schema.yaml`), and PNG figures (scatter plots, heatmaps, MDES summary) saved under `data/processed/plots/`. | FR‑004 |
| **Contract Alignment** | Ensure all CSV outputs conform to their respective schemas: `graph_metrics.csv` (`contracts/graph_metrics.schema.yaml`), `performance_metrics.csv` (`contracts/performance_metrics.schema.yaml`). | FR‑001, FR‑002, FR‑003, FR‑004 |

All functional requirements (FR‑001‑FR‑004) and the robustness check (SC‑004) are explicitly covered. No extra constraints are introduced.

---



## projects/PROJ-163-exploring-the-role-of-network-structure-/specs/001-exploring-the-role-of-network-structure/research.md
# Research: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Problem Statement
We investigate the **associational** relationship between the physical connectivity (graph topology) of superconducting qubits within a processor and its performance metrics (T₁, T₂, CX gate error, readout error). The hypothesis is that certain topological descriptors (e.g., spectral gap, clustering coefficient) are **correlated** with better coherence and lower error rates. All statements remain associational; no causal inference is claimed.

## Dataset Strategy

### Primary Data Source – IBM Quantum API
- **Endpoint**: IBM Quantum Experience “backend properties” accessed via `qiskit-ibm-runtime`.  
- **Variables Retrieved**:
  - `coupling_map` (list of qubit‑pair edges)  
  - `t1`, `t2` (µs)  
  - `gate_error` (average CX error)  
  - `readout_error` (average measurement error)  
  - `timestamp` (ISO‑8601)  
  - `backend_name` (device identifier)  
  - `chip_generation` (derived from backend name, e.g., *Eagle*, *Falcon*)  
  - `qubit_count` (total number of qubits)  
  - `device_age_days` (days since last firmware release, derived)  
  - `readout_architecture` (categorical, if available)  
  - **Optional**: `temperature` or other environmental metadata (used as covariate when present).

All devices with `timestamp` older than **30 days** are excluded (FR‑001). No static dataset is used; the API is queried at runtime to satisfy reproducibility (Constitution VI).

### Coverage & Missing Data
- If a device lacks a particular metric (e.g., `entanglement_fidelity`), that metric is omitted from correlation tests for that device.  
- Rate‑limit handling: exponential backoff with up to 3 retries for HTTP 429/503 responses (C‑001).

### Longitudinal Performance Window (SC‑004 Robustness)
- For each device we also fetch up to **30 prior calibration snapshots** (≤ 30 days old).  
- The **same** `performance_metrics.csv` file stores both the **current** snapshot (`source_window = "current"`) and the **30‑day averaged** rows (`source_window = "window"`).  
- The primary analysis uses the “current” rows; robustness checks compare results obtained with the “window” rows, satisfying SC‑004.  
- Temporal drift is assessed by the variance of performance metrics across the window; devices with high drift are flagged.

## Methodology

### 1. Data Ingestion & Pre‑processing (FR‑001, FR‑002)
1. Query all public backends via `IBMQBackendService().backend_properties()` for the **current** snapshot and for the past 30 days (if available).  
2. Filter by freshness (`timestamp` ≤ 30 days).  
3. Parse JSON into a `pandas.DataFrame` of devices × metrics (including covariates).  
4. Save raw JSON snapshots to `data/raw/{device}_{ts}.json` (checksum recorded).  
5. Write `performance_metrics.csv` to `data/processed/` conforming to `contracts/performance_metrics.schema.yaml`. The file contains a `source_window` column (`"current"` or `"window"`).  

### 2. Graph Construction & Metric Computation (FR‑003)
1. Build an undirected `networkx.Graph` per device from `coupling_map`.  
2. Compute the following metrics (store in `graph_metrics.csv`):
   - Average shortest‑path length (largest connected component)  
   - Diameter (largest connected component)  
   - Global clustering coefficient  
   - Mean edge betweenness  
   - **Degree assortativity** (custom implementation that yields –1.0 for a 3‑node path)  
   - **Spectral gap** (second smallest Laplacian eigenvalue; set to 0 for disconnected graphs – per C‑002).  
3. For disconnected graphs, path‑length metrics are computed on the largest component; `is_finite` records whether a metric value is finite, and `component_size` stores the size of the largest component.  

### 3. Statistical Analysis (FR‑004)
- **Primary Test**: Spearman rank correlation (ρ) between each graph metric and each performance metric.  
- **Exact/Permutation p‑values**: If the number of devices **N < 30**, compute permutation‑test p‑values (10 000 permutations) and permutation‑based 95 % confidence intervals; otherwise use the exact Spearman p‑value.  
- **Partial Correlation**: Controlling for `chip_generation`, `qubit_count`, `device_age_days`, `readout_architecture`, **timestamp**, and (if available) `temperature` via `pingouin.partial_corr`.  
- **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR (α = 0.05).  
- **Robustness Checks**:
  - **Leave‑One‑Device‑Out (LODO)** – recompute correlations omitting each device.  
  - **Chip‑Family Exclusion** – repeat analysis after removing each chip generation.  
  - **Time‑Window Robustness (SC‑004)** – repeat analysis using the `"window"` rows from `performance_metrics.csv` and compare effect sizes.  
  - **Longitudinal Stability** – assess variance of performance metrics across the historical window; flag devices with high drift.  
- **Power / MDES**: Compute Minimum Detectable Effect Size for Spearman ρ given N and number of tests; write results to `power_analysis.csv` per `contracts/mdes_report.schema.yaml`.  
  - **Exploratory Flag**: If `min_detectable_rho` > 0.5, label the study exploratory and **do not claim statistical significance**; report only effect sizes with permutation‑CI.  

All results are written to `correlation_results.csv` (`contracts/correlation_results.schema.yaml`) and `power_analysis.csv` (`contracts/mdes_report.schema.yaml`). Figures generated in the next step are saved alongside these outputs.

### 4. Visualization (part of Reporting)
- Scatter plots for each **significant** (adj p < 0.05) metric pair, with permutation‑CI error bands when applicable.  
- Heatmap of the full correlation matrix (including covariates).  
- MDES summary figure.  
Figures are saved under `data/processed/plots/`.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: BH‑FDR applied across all metric pairs.  
- **Sample Size / Power**: MDES calculation; if MDES > 0.5 the study is flagged exploratory and no significance claims are made.  
- **Collinearity**: Graph metrics are partially correlated; partial correlation mitigates inflated univariate claims.  
- **Measurement Validity**: T₁/T₂ and gate/readout errors are standard IBM‑reported metrics; graph metrics are canonical network‑science descriptors with a theoretical link to connectivity‑driven decoherence (spectral gap rationale).  
- **Causal Framing**: All statements remain associational; no causal inference is claimed.

## Compute Feasibility
- **Hardware**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM).  
- **Data Size**: < 2 MB total JSON (current + historical).  
- **Runtime**: Expected < 10 min; all libraries are CPU‑compatible.

---



## projects/PROJ-163-exploring-the-role-of-network-structure-/specs/001-exploring-the-role-of-network-structure/data-model.md
# Data Model: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Overview
Defines every entity that flows through the pipeline, from raw API JSON to final correlation results. All artifacts are version‑hashed and recorded in `state/projects/...yaml`.

## Entities

### 1. QubitDevice
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Unique backend identifier (e.g., `ibmq_manila`). |
| `backend_type` | string | `"public"` (all used devices are public). |
| `chip_generation` | string | Derived generation label (`Eagle`, `Falcon`, …). |
| `timestamp` | datetime | Calibration snapshot time (ISO‑8601). |
| `is_fresh` | boolean | True if `timestamp` ≤ 30 days old. |

### 2. GraphMetric
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | FK → QubitDevice. |
| `chip_generation` | string | Redundant for easy filtering. |
| `metric_name` | string | One of `["avg_shortest_path","diameter","clustering_coef","edge_betweenness","degree_assortativity","spectral_gap"]`. |
| `value` | float | Computed metric value. |
| `is_finite` | boolean | True if `value` is not NaN/Inf (populated during graph construction). |
| `component_size` | integer | Size of the largest connected component (used for path‑length metrics; populated during graph construction). |

### 3. PerformanceMetric
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | FK → QubitDevice. |
| `metric_name` | string | One of `["T1","T2","gate_error","readout_error","entanglement_fidelity"]`. |
| `value` | float | Measured value (raw or normalized). |
| `unit` | string | Units (`us`, `1e-3`, `percent`). |
| `source_window` | string | `"current"` – performance extracted from the same calibration snapshot as topology; `"window"` – 30‑day averaged performance metrics used for robustness checks. |
| `timestamp` | datetime | Timestamp of the snapshot the metric originates from (for `current` rows) or `null` for aggregated `window` rows. |

### 4. CorrelationResult
| Field | Type | Description |
|-------|------|-------------|
| `graph_metric` | string | Name of the topological descriptor. |
| `performance_metric` | string | Name of the performance indicator. |
| `spearman_rho` | float | Spearman correlation coefficient (ρ). |
| `p_value` | float | Raw p‑value for the correlation test. |
| `adj_p_value` | float | BH‑FDR adjusted p‑value. |
| `partial_rho` | float (optional) | Partial correlation controlling for covariates. |
| `is_significant` | boolean | `adj_p_value < 0.05`. |
| `exclusion_reason` | string (optional) | Reason for omission (e.g., `missing_data`, `disconnected_graph`). |

### 5. PowerAnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `sample_size` | integer | Number of devices (N) included in the analysis. |
| `number_of_tests` | integer | Total metric‑pair hypothesis tests performed. |
| `min_detectable_rho` | float | MDES at 80 % power, α = 0.05. |
| `confidence_interval` | string | 95 % CI for the observed correlations (e.g., `"[0.12, 0.34]"`). |
| `low_power_flag` | string | `"Low Power: MDES > 0.5 (Large Effect Required)"` or `"Adequate Power"`.|

## Data Flow
1. **Raw Ingestion** – `fetcher.py` → `data/raw/{device}_{ts}.json`.  
2. **Transformation** – `graph_builder.py` → `graph_metrics.csv`; `fetcher.py` → `performance_metrics.csv` (including `source_window`).  
3. **Analysis** – `stats_engine.py` joins on `device_id`, produces `correlation_results.csv` and `power_analysis.csv`.  
4. **Visualization** – `viz.py` reads `correlation_results.csv` → PNGs.  

## Validation Rules
- No `NaN`/`Inf` in numeric fields.  
- All timestamps ISO‑8601.  
- Unique `(device_id, metric_name)` pairs in `GraphMetric` and `PerformanceMetric`.  
- Referential integrity: every `device_id` in derived tables must exist in `QubitDevice`.  

---



## projects/PROJ-163-exploring-the-role-of-network-structure-/specs/001-exploring-the-role-of-network-structure/quickstart.md
# Quickstart: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Prerequisites
- Python 3.11+  
- Internet access (to call the IBM Quantum API)  
- (Optional) IBM Quantum API token for higher rate limits (`QISKIT_IBM_TOKEN` environment variable).

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-163-exploring-the-role-of-network-structure-/
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify dependencies:

```bash
python -c "import networkx, pandas, qiskit_ibm_runtime, sklearn, scipy, matplotlib; print('All good')"
```

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the following steps in order:

1. **Fetch** calibration data (`fetcher.py`) – current snapshot + up to 30‑day historical window.  
2. **Build** graphs & compute metrics (`graph_builder.py`).  
3. **Analyze** correlations, partial correlations (covariates: `chip_generation`, `qubit_count`, `device_age_days`, `readout_architecture`, `timestamp`, `temperature`), permutation‑test confidence intervals (used when N < 30), FDR correction, and robustness checks (LODO, chip‑family exclusion, time‑window performance comparison, longitudinal stability).  
4. **Generate** power‑analysis/MDES report (`stats_engine.py`).  
5. **Visualize** results (`viz.py`) – scatter plots, heatmaps, and MDES summary figures are saved automatically as part of the reporting step (FR‑004).  
6. **Record** checksums & update project state (`hygiene.py`).

### Expected Outputs
- `data/raw/*.json` – raw API snapshots (current and historical).  
- `data/processed/performance_metrics.csv` (includes `source_window` column)  
- `data/processed/graph_metrics.csv`  
- `data/processed/correlation_results.csv`  
- `data/processed/power_analysis.csv` (MDES report)  
- `data/processed/plots/*.png` – scatter plots & heatmaps.  
- Updated `state/projects/PROJ-163-...yaml` with artifact hashes.

## Testing

```bash
pytest tests/test_fetcher.py -v
pytest tests/test_graph_builder.py -v
pytest tests/test_stats_engine.py -v
pytest tests/test_integration_fetch.py -v   # live API (rate‑limited)
```

All tests must pass; schema validation is performed automatically against the files in `contracts/`.

## CLI Usage (graph_builder)

The graph‑building CLI accepts both the new `--out` flag and the legacy `--output` flag for backward compatibility:

```bash
python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv
# or
python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv
```

The CLI implements a **custom degree assortativity** calculation that yields –1.0 for a 3‑node path, matching the unit‑test expectation.

## Inspection Commands

```bash
head data/processed/performance_metrics.csv
head data/processed/graph_metrics.csv
grep True data/processed/correlation_results.csv   # show significant pairs
cat data/processed/power_analysis.csv
```

## Troubleshooting
- **Rate‑limit errors** – the fetcher retries with exponential backoff; add a token to `QISKIT_IBM_TOKEN` if needed.  
- **Disconnected graphs** – `spectral_gap` will be set to 0; path‑length metrics are computed on the largest component only.  
- **Missing metrics** – devices lacking a metric are simply omitted from that specific correlation test.  
- **Low statistical power** – if `N < 30`, the MDES report will flag the study as exploratory; permutation‑CI are used and no significance claims are made.  

---



## projects/PROJ-163-exploring-the-role-of-network-structure-/specs/001-exploring-the-role-of-network-structure/contracts/correlation_results.schema.yaml
$schema: "http://yaml.org/draft-07/schema#"
type: "object"
description: "Schema for the correlation results CSV generated by the statistical analysis pipeline."
properties:
  metric_a:
    type: "string"
    description: "Name of the first metric in the correlation pair (e.g., 'diameter', 't1_mean')."
  metric_b:
    type: "string"
    description: "Name of the second metric in the correlation pair."
  rho:
    type: "number"
    description: "Spearman correlation coefficient (rho)."
  p_value:
    type: "number"
    description: "Raw p-value for the correlation test."
  adj_p_value:
    type: "number"
    description: "Benjamini-Hochberg FDR-adjusted p-value."
  partial_rho:
    type: "number"
    description: "Partial correlation coefficient controlling for covariates (optional)."
required:
  - metric_a
  - metric_b
  - rho
  - p_value
  - adj_p_value===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-163-exploring-the-role-of-network-structure-/specs/001-exploring-the-role-of-network-structure/contracts/graph_metrics.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "GraphMetrics"
description: "Schema for the processed graph metrics CSV data."
type: "object"
additionalProperties: false
required:
  - device_id
  - metric_name
  - value
  - is_finite
properties:
  device_id:
    type: "string"
    description: "Unique identifier of the quantum device."
  metric_name:
    type: "string"
    description: "Name of the graph metric (e.g., 'average_shortest_path', 'clustering_coefficient')."
  value:
    type: "number"
    description: "The computed value of the metric."
  is_finite:
    type: "boolean"
    description: "Whether the value is a finite number (handles NaN/Inf)."
  component_size:
    type: "integer"
    description: "Size of the largest connected component (used for filtering)."