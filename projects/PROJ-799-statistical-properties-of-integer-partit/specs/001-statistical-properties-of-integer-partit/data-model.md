# Data Model: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Overview

This document defines the data structures, schemas, and transformations used in the project. All data flows from `generate_partitions.py` to `feature_engineering.py` and finally to `regression_analysis.py`.

## Entities

### PartitionRecord

Represents a single data point containing $n$, $p_{\mathcal{P}}(n)$, $Q_{as}(n)$, and the calculated $R(n)$.

**Fields**:
- `n`: Integer, the integer being partitioned.
- `p_P_n`: Integer, exact count of partitions into distinct primes (arbitrary precision).
- `Q_as_n`: Float, asymptotic prediction from Meinardus' theorem.
- `R_n`: Float, log-residual $\log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$.

**Constraints**:
- `n` $\ge 1$.
- `p_P_n` $\ge 0$.
- `Q_as_n` $> 0$ (clamped if necessary).
- `R_n` is `NaN` if `p_P_n` = 0 or `Q_as_n` $\le 0$.

### DensityFeatureSet

Represents the independent variables for a given $n$.

**Fields**:
- `n`: Integer, the integer.
- `pi_n`: Integer, prime-counting function $\pi(n)$.
- `inv_sq_ln_n`: Float, $1/(\ln n)^2$ (to avoid direct coupling with $Q_{as}(n)$).
- `dist_nearest_prime`: Integer, distance to nearest prime (absolute difference to the closest prime, either smaller or larger).
- `sin_log_n`: Float, $\sin(\log n)$.
- `cos_log_n`: Float, $\cos(\log n)$.
- `gap_variance`: Float, variance of prime gaps up to $n$.

**Constraints**:
- All fields derived from `n`.
- `inv_sq_ln_n` $\neq 0$ (for $n \ge 2$).

### RegressionModel

Represents the fitted statistical model.

**Fields**:
- `coefficients`: Dictionary mapping feature names to coefficients.
- `intercept`: Float, model intercept.
- `r_squared`: Float, coefficient of determination.
- `mse`: Float, mean squared error (training).
- `cv_mse`: Float, mean squared error (cross-validation).
- `p_values`: Dictionary mapping feature names to p-values (corrected for autocorrelation).

**Constraints**:
- `r_squared` $\in [0, 1]$.
- `mse` $\ge 0$.

## Data Files

### `data/raw/partitions.csv`

**Description**: Raw output from `generate_partitions.py`.

**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| n | int | Integer being partitioned |
| p_P_n | int | Exact partition count (arbitrary precision) |
| Q_as_n | float | Asymptotic prediction |

**Constraints**:
- No header row (or header row with column names).
- No missing values for `n`, `p_P_n`, `Q_as_n`.
- `p_P_n` $\ge 0$, `Q_as_n` $> 0$.

**Example**:
```csv
1,0,0.001
2,1,0.002
3,1,0.003
...
```

### `data/processed/features.csv`

**Description**: Processed data with residuals and density features.

**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| n | int | Integer |
| R_n | float | Log-residual |
| pi_n | int | Prime count |
| inv_sq_ln_n | float | Inverse squared log density |
| dist_nearest_prime | int | Distance to nearest prime (absolute difference) |
| sin_log_n | float | Sin(log n) |
| cos_log_n | float | Cos(log n) |
| gap_variance | float | Variance of prime gaps |

**Constraints**:
- `R_n` not `NaN`.
- All features derived from valid `n`.

**Example**:
```csv
5,0.123,3,0.385,0,0.987,0.159,0.5
6,0.456,3,0.310,1,0.912,0.410,0.4
...
```

### `output/regression_summary.json`

**Description**: Regression model results.

**Schema**:
```yaml
type: object
properties:
  coefficients:
    type: object
    additionalProperties:
      type: number
  intercept:
    type: number
  r_squared:
    type: number
  mse:
    type: number
  cv_mse:
    type: number
  p_values:
    type: object
    additionalProperties:
      type: number
required:
  - coefficients
  - intercept
  - r_squared
  - mse
  - cv_mse
  - p_values
```

## Transformations

### `generate_partitions.py` → `data/raw/partitions.csv`

- **Input**: `n_max` (default [deferred]).
- **Output**: CSV with `n`, `p_P_n`, `Q_as_n`.
- **Logic**:
  1. Generate primes up to `n_max`.
  2. Run DP to compute `p_P_n` (arbitrary precision).
  3. Compute `Q_as_n` using asymptotic formula.
  4. Write to CSV.

### `data/raw/partitions.csv` → `data/processed/features.csv`

- **Input**: `data/raw/partitions.csv`.
- **Output**: CSV with `R_n` and density features.
- **Logic**:
  1. Filter rows where `p_P_n` = 0 or `Q_as_n` $\le 0$.
  2. Compute `R_n = log(p_P_n) - log(Q_as_n)`.
  3. Compute density features (`pi_n`, `inv_sq_ln_n`, `dist_nearest_prime`, etc.).
  4. Write to CSV.

### `data/processed/features.csv` → `output/regression_summary.json`

- **Input**: `data/processed/features.csv`.
- **Output**: JSON with regression results.
- **Logic**:
  1. Fit linear regression/GAM.
  2. Compute cross-validation MSE.
  3. Extract coefficients, p-values (corrected), $R^2$.
  4. Write to JSON.

## Data Hygiene

- **Checksums**: All data files checksummed in `state/`.
- **Immutability**: Raw data never modified; derivations produce new files.
- **Validation**: Tests ensure no `NaN` in `R_n` and all features are non-null.
