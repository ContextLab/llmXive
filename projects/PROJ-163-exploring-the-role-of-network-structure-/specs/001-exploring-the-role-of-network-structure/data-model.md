# Data Model: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Entities

### 1. QubitDevice
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Backend identifier (e.g., `ibmq_manila`). |
| `backend_type` | string | `"public"` (all used devices are publicly accessible). |
| `chip_generation` | string | Derived from backend name (e.g., *Eagle*, *Falcon*). |
| `timestamp` | datetime (ISO‑8601) | Calibration snapshot time. |
| `is_fresh` | boolean | `True` iff `timestamp` ≤ 30 days old (FR‑001). |

### 2. GraphMetric
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | FK → QubitDevice. |
| `metric_name` | string | One of `["avg_shortest_path","diameter","clustering_coef","edge_betweenness","degree_assortativity","spectral_gap"]`. |
| `value` | float | Computed metric value. |
| `is_finite` | boolean | `False` if the metric is NaN/Inf (e.g., disconnected graph). |
| `component_size` | integer | Size of the largest connected component (used for path‑length metrics). |
| `edge_type` | enum(`active`,`inactive`) | Present only for tunable‑coupler edges (FR‑007). |

### 3. PerformanceMetric
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | FK → QubitDevice. |
| `timestamp` | datetime (ISO‑8601) | Timestamp of the snapshot (for both `"current"` and `"window"` rows). |
| `t1_mean` | number | Median T₁ (seconds) across qubits. |
| `t2_mean` | number | Median T₂ (seconds) across qubits. |
| `cx_error_mean` | number | Median two‑qubit (CX) gate error. |
| `readout_error_mean` | number | Median readout error across qubits. |
| `entanglement_fidelity_mean` | number | Median entanglement fidelity across qubits. |
| `chip_family` | string | Human‑readable chip family derived from the backend name. |
| `source_window` | enum(`current`,`window`) | `"current"` for the cross‑sectional snapshot; `"window"` for the 30‑day averaged performance window (FR‑004). |

### 4. CorrelationResult
| Field | Type | Description |
|-------|------|-------------|
| `metric_a` | string | Name of the topology descriptor (e.g., `spectral_gap`). |
| `metric_b` | string | Name of the performance metric (e.g., `t1_mean`). |
| `rho` | number | Spearman correlation coefficient. |
| `p_value` | number | Raw p‑value for the correlation test. |
| `adj_p_value` | number | BH‑FDR adjusted p‑value. |
| `partial_rho` | number (optional) | Partial correlation controlling for covariates. |
| `window_delta` | number (optional) | Difference `ρ_window − ρ_cross`. |
| `is_significant` | boolean | `adj_p_value < 0.05`. |
| `exclusion_reason` | string (optional) | Reason for omission (e.g., `missing_data`). |
| `prop_significant` | number (optional) | Proportion of devices with cluster‑adjusted p ≤ 0.05 (FR‑017). |

### 5. PowerAnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `sample_size` | integer | Number of devices included (N). |
| `number_of_tests` | integer | Total topology‑performance hypothesis tests performed. |
| `min_detectable_rho` | number | MDES at 80 % power, α = 0.05. |
| `confidence_interval` | string | 95 % CI for the observed correlation (e.g., `"[0.12, 0.34]"`). |
| `low_power_flag` | string | `"Low Power: MDES > 0.3 (Exploratory)"` or `"Adequate Power"` (FR‑010). |

## Data Flow
1. **Raw ingestion** (`fetcher.py`) → `data/raw/{device}_{ts}.json`.  
2. **Performance extraction** (`fetcher.py`) → `performance_metrics.csv` (conforms to `contracts/performance_metrics.schema.yaml`).  
3. **Graph construction** (`graph_builder.py`) → `graph_metrics.csv` (conforms to `contracts/graph_metrics.schema.yaml`).  
4. **Statistical engine** (`stats_engine.py`) joins on `device_id` → `correlation_results.csv`, `window_comparison.csv`, `power_analysis.csv` (schemas `correlation_results.schema.yaml`, `mdes_report.schema.yaml`).  
5. **Visualization** (`viz.py`) reads `correlation_results.csv` → PNGs in `data/processed/plots/`.  

## Validation Rules
- No `NaN`/`Inf` in numeric fields (`is_finite` must be `True` for finite values).  
- All timestamps are ISO‑8601 strings (never null).  
- Unique `(device_id, metric_name)` pairs in `GraphMetric`; unique `device_id` rows in `PerformanceMetric`.  
- Referential integrity: every `device_id` in derived tables must exist in `QubitDevice`.  

---
