# Data Model: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Overview
The data model captures simulation parameters, eigenvalue results, and aggregated statistics. All records are validated against the JSON/YAML contracts in `contracts/`. The model satisfies the applicable functional requirements and the constitution’s principles III, IV, VI, VII.

## Entities

### 1. SimulationRun
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `run_id` | string (UUID) | Unique identifier for the run. | `simulation_run.schema.yaml` |
| `timestamp` | iso8601 string | Execution time (UTC). | schema |
| `seed` | integer | Random seed used for reproducibility. | schema |
| `N` | integer | Matrix dimension (100 – 2000). | schema |
| `k` | integer | Perturbation rank (1, 2, 5). | schema |
| `theta` | number | Spectral norm of perturbation (1.0 – 3.0). | schema |
| `pattern_type` | string | `"diagonal"`, `"block-sparse"`, `"random-sparse"`. | schema |
| `support_density` | number | \(p\) for random‑sparse (null otherwise). | schema |
| `computation_time_ms` | number | Solver wall‑clock time. | schema |
| `empirical_bulk_edge` | number | **Diagnostic**: 99th percentile of the full spectrum for this run (used for analysis, **not** for outlier definition). | schema |

### 2. EigenvalueResult
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `run_id` | string | FK to `SimulationRun`. | `eigenvalue_result.schema.yaml` |
| `eigenvalue_index` | integer (1‑10) | Rank of eigenvalue (1 = largest). | schema |
| `value` | number | Eigenvalue \(\lambda\). | schema |
| `is_outlier` | boolean | **True if** \(\lambda > 2.0 + 0.05\) (theoretical semicircle edge plus tolerance). | schema |
| `theoretical_bbp` | number | Expected outlier location \(\theta + 1/\theta\) (if \(\theta>1\)). | schema |
| `deviation` | number | \(\lambda -\) theoretical BBP. | schema |

### 3. AggregatedThreshold
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `config_id` | string | Hash of \((N,k,pattern,\theta)\). | `aggregated_threshold.schema.yaml` |
| `N` | integer | Matrix dimension. | schema |
| `k` | integer | Perturbation rank. | schema |
| `pattern_type` | string | Sparsity pattern. | schema |
| `theta` | number | Perturbation norm. | schema |
| `total_runs` | integer | Number of simulation repeats (≥ 1). | schema |
| `outlier_count` | integer | Runs with ≥ 1 outlier. | schema |
| `outlier_probability` | number (0‑1) | Empirical probability of outlier emergence. | schema |
| `mean_deviation` | number | Mean deviation of outliers from theoretical BBP. | schema |
| `std_deviation` | number (≥ 0) | Std. dev. of deviation. | schema |
| `theta_c_estimate` | number | Critical threshold from sigmoid fit. | schema |
| `theta_c_confidence` | number | Half‑width of 95 % CI. | schema |

## Data Flow
1. **Generation** – `src/simulation/wigner.py` + `perturbation.py` → `SimulationRun` record.  
2. **Eigenvalue Computation** – `src/simulation/eigen_solver.py` → ten `EigenvalueResult` records linked by `run_id`.  
3. **Aggregation** – `src/analysis/aggregation.py` reads all records for a given config, computes summary statistics, fits sigmoid, writes `AggregatedThreshold`.  

All files are stored under `data/processed/` as Parquet (fast columnar I/O) and accompanied by a cryptographic SHA checksum recorded in `data/checksums.yaml` (Constitution Principle III).

## Validation Pipeline
- **Schema Validation** – `tests/contract/test_schemas.py` loads each output file and validates against the corresponding schema using `jsonschema`.  
- **Checksum Verification** – `src/utils/checksum.py` ensures file integrity before downstream analysis.  

---


