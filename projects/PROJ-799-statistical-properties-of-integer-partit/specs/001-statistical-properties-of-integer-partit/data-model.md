# Data Model: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Entity Definitions

### 1.1. PartitionRecord
| Field | Type | Description |
|-------|------|-------------|
| `n` | integer (≥ 1) | Integer being partitioned |
| `p_P_n` | integer (≥ 0) | Exact count of partitions of `n` into distinct primes |
| `Q_as_n` | number (> 0) | Asymptotic baseline prediction from calibrated Meinardus' theorem (or fallback) |
| `R_n` | number (nullable) | Log‑residual $\log(p_P_n)-\log(Q_as_n)$; `null` if $p_P_n$ or $Q_as_n$ is non‑positive |

### 1.2. DensityFeatureSet
| Field | Type | Description |
|-------|------|-------------|
| `n` | integer (≥ 1) | Same as above |
| `pi_n` | integer (≥ 0) | Prime‑counting function $\pi(n)$ |
| `inv_log_n` | number (> 0) | Inverse natural log $1/\ln(n)$ |
| `cum_density` | number (> 0) | $\displaystyle\sum_{p\le n}\frac{1}{p}$ (justified via Mertens’ theorem) |

### 1.3. RegressionModel
| Field | Type | Description |
|-------|------|-------------|
| `coefficients` | object (name → number) | Regression coefficients for each predictor |
| `intercept` | number | Intercept term |
| `r_squared` | number ∈[0,1] | $R^{2}$ on the full data |
| `p_values` | object (name → number) | Raw $p$‑values (HAC‑adjusted) |
| `fdr_corrected_p_values` | object (name → number) | Benjamini‑Hochberg corrected $p$‑values |
| `mse_cv` | number ≥ 0 | Mean Squared Error averaged over 10‑fold time‑series CV |
| `null_model_R2` | number ∈[0,1] | $R^{2}$ of intercept‑only model |
| `null_model_MSE` | number ≥ 0 | MSE of the null model |

### 1.4. ReferenceData
| Field | Type | Description |
|-------|------|-------------|
| `n` | integer (≤ 100) | Small $n$ for verification |
| `p_P_n` | integer | Known exact count from literature |

## 2. Data Flow

1. **Raw primes** (`primes_up_to_50000.csv`) → `generate_partitions.py` → `partition_counts.csv`.  
2. `compute_baseline.py` → `baseline_values.csv`.  
3. `feature_engineering.py` merges the two, computes `R_n` and density features → `features.csv`.  
4. `fit_model.py` reads `features.csv` → `model_results.json` (conforms to `RegressionModel`).  
5. `visualize.py` consumes `features.csv` and model predictions → `residuals_plot.png`.

## 3. File Formats & Constraints

- **CSV files**: UTF‑8, comma delimiter, header row.  
- `partition_counts.csv`: columns `n,p_P_n`.  
- `baseline_values.csv`: columns `n,Q_as_n`.  
- `features.csv`: columns `n,p_P_n,Q_as_n,R_n,pi_n,inv_log_n,cum_density`.  
  - `R_n` is omitted for rows where `p_P_n=0` or `Q_as_n≤0`.  
- `model_results.json`: JSON object matching `RegressionModel` schema.  
- **Checksums**: All files under `data/` have a SHA‑2 hash recorded in the project state file.

## 4. Validation Rules

- `p_P_n` must be integer ≥ 0; for $n\le100$ it must match `reference_data.csv` exactly (SC‑003).  
- `Q_as_n` must be > 0; values < $10^{-10}$ are clamped before log.  
- `R_n` is computed only when both inputs are positive.  
- Density features must be consistent with the prime list (`pi_n` equals the count of primes ≤ `n`).  
- No missing values are allowed in `features.csv` for rows used in regression (enforced by `test_features_non_null.py`).  

---

