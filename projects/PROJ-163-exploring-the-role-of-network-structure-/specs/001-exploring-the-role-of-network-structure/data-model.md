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
| `timestamp` | datetime | Timestamp of the snapshot the metric originates from (for `current` window) or `null` for aggregated window metrics. |

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

