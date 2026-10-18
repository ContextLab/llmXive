# Data Model: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Overview
Simulation parameters, eigenvalue results, aggregated statistics, and convergence/validation reports. All records are validated against contracts in `contracts/` **at write time** by the shared artifact writer, and again by contract tests.

## Entities

### 1. SimulationRun
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string (UUID) | Unique run identifier. |
| `timestamp` | iso8601 string | Execution time (UTC). |
| `seed` | integer | Random seed. |
| `N` | integer | Matrix dimension (100–2000). |
| `k` | integer | Perturbation rank (1, 2, 5). |
| `theta` | number | Spectral norm of perturbation (allowed range 0.5 – 3.0). |
| `pattern_type` | string | `diagonal`, `block-sparse`, `random-sparse`. |
| `support_density` | number or null | \(p\) for random‑sparse; null otherwise (nullable). |
| `computation_time_ms` | number | Solver wall‑clock time. |
| `empirical_bulk_edge` | number | Diagnostic 99th‑percentile bulk edge (not used for outlier definition). |

### 2. EigenvalueResult
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | FK to SimulationRun. |
| `eigenvalue_index` | integer (1–10) | Rank (1 = largest). |
| `value` | number | The computed eigenvalue. |
| `is_outlier` | boolean | True iff \(\lambda > 2 + \tau(N)\) where \(\tau(N)=\max(0.05,2N^{-2/3})\). |
| `theoretical_bbp` | number | \(\theta + 1/\theta\) (defined for all \(\theta\)). |
| `deviation` | number | \(\lambda -\) theoretical BBP. |

### 3. AggregatedThreshold
| Field | Type | Description |
|-------|------|-------------|
| `config_id` | string | Hash of \((N,k,pattern,\theta)\). |
| `N` | integer | Matrix dimension. |
| `k` | integer | Perturbation rank. |
| `pattern_type` | string | Sparsity pattern. |
| `theta` | number | Perturbation norm (0.5 – 3.0). |
| `total_runs` | integer | Repetitions actually executed (≥1). |
| `outlier_count` | integer | Runs with ≥1 outlier. |
| `outlier_probability` | number (0–1) | Empirical outlier probability. |
| `mean_deviation` | number | Mean deviation of outliers from theoretical BBP. |
| `std_deviation` | number (≥0) | Standard deviation of outliers from theoretical BBP. |
| **Note**: `theta_c_estimate` and `theta_c_confidence` are **not** part of this entity; they belong to the separate *ThresholdFit* artifact (see below).

### 4. ConvergenceReport (NEW)
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | FK to SimulationRun. |
| `solver` | string | `"ARPACK-eigsh"`. |
| `tol` | number | Convergence tolerance used (1e-10). |
| `maxiter` | integer | Maximum iterations (1000). |
| `converged` | boolean | ARPACK convergence status. |
| `n_iterations` | integer | Iterations used. |
| `bulk_edge_check` | string | `"pass"` if unperturbed bulk edge within tolerance of theoretical 2, else `"fail"`. |
| `matrix_checksum` | string | SHA‑256 of the raw Wigner matrix bytes. |
| `schema_validation` | string | `"pass"` — result of validating the companion results file against its contract. |

### 5. ThresholdFit (NEW)
| Field | Type | Description |
|-------|------|-------------|
| `config_id` | string | Identifier for the \((N,k,pattern)\) configuration. |
| `N` | integer | Matrix dimension. |
| `k` | integer | Perturbation rank. |
| `pattern_type` | string | Sparsity pattern. |
| `theta_c_estimate` | number or null | Estimated critical threshold (null if fit failed). |
| `theta_c_confidence` | number or null | 95 % CI half‑width (null if fit failed). |
| `fit_status` | string | `"converged"` or `"failed"` indicating fit success. |
| `a` | number or null | Sigmoid slope parameter (null if fit failed). |
| `b` | number or null | Sigmoid intercept parameter (null if fit failed). |

## Data Flow
1. `wigner.py` + `perturbation.py` → `SimulationRun` record; matrix bytes checksummed into `data/checksums.yaml`.
2. `eigen_solver.py` → ten `EigenvalueResult` records + `ConvergenceReport`, all linked by `run_id`.
3. `aggregate_thresholds.py` → array of `AggregatedThreshold` records **without** any `theta_c` fields.
4. `threshold_fit.py` → `ThresholdFit` record (validated against `threshold_fit.schema.yaml`).  
5. `sweep.py` / `sensitivity.py` / `finite_size.py` → Parquet files of raw run and eigenvalue records.

All writes pass through `utils/artifacts.py`, which validates against the contract before writing and appends a SHA‑256 checksum to `data/checksums.yaml` (Constitution III). File‑to‑schema mapping is fixed and enforced by the contract tests:

| File | Schema |
|------|--------|
| `data/processed/single_run_results.json` | `simulation_run.schema.yaml` (run record) + `eigenvalue_result.schema.yaml` (each element of `eigenvalue_results`) |
| `data/processed/convergence_report.json` | `convergence_report.schema.yaml` |
| `data/processed/aggregated_thresholds.json` | `aggregated_threshold.schema.yaml` |
| `data/processed/threshold_fit.json` | `threshold_fit.schema.yaml` |
| `data/processed/*.parquet` | column‑level validation in contract tests against the entity field definitions |

## PerturbationConfig Mapping (Spec Clarification)
The spec defines a `PerturbationConfig` entity, but this implementation inlines those fields into the `SimulationRun` record (`k`, `support_density`, and `pattern_type`). This satisfies the spec while keeping the data model simple.

---


