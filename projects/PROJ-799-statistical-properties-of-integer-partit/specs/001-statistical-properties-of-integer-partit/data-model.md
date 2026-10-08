# Data Model: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Entity Definitions

### 1.1. PartitionRecord
Represents a single data point in the analysis.
-   **n**: Integer, the number being partitioned.
-   **p_P_n**: Integer, the exact count of partitions into distinct primes.
-   **Q_as_n**: Float, the asymptotic baseline prediction.
-   **R_n**: Float, the log-residual ($\log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$).

### 1.2. DensityFeatureSet
Represents the independent variables for a given $n$.
-   **n**: Integer, the number being partitioned.
-   **pi_n**: Integer, the prime-counting function $\pi(n)$.
-   **inv_log_n**: Float, the inverse logarithm $1/\ln(n)$.
-   **cum_density**: Float, the cumulative sum of $1/p$ for all $p \le n$.

### 1.3. RegressionModel
Represents the fitted model state.
-   **coefficients**: Dictionary of predictor name $\to$ coefficient value.
-   **intercept**: Float.
-   **r_squared**: Float, $R^2$ score.
-   **p_values**: Dictionary of predictor name $\to$ p-value.
-   **mse_cv**: Float, Mean Squared Error from cross-validation.
-   **null_model_R2**: Float, $R^2$ of the null (intercept-only) model.
-   **null_model_MSE**: Float, MSE of the null model.

### 1.4. ReferenceData
Represents the pre-computed reference values for validation.
-   **n**: Integer.
-   **p_P_n**: Integer (reference value).

## 2. Data Flow

1.  **Input**: `primes_up_to_50000.csv` (Raw).
2.  **Process 1**: `generate_partitions.py` $\to$ `partition_counts.csv` (n, p_P_n) (Batched).
3.  **Process 2**: `compute_baseline.py` $\to$ `baseline_values.csv` (n, Q_as_n).
4.  **Process 3**: `feature_engineering.py` $\to$ `features.csv` (Merged data with R_n and density features).
5.  **Process 4**: `fit_model.py` $\to$ `model_results.json` (Regression stats).
6.  **Output**: `visualization.png` (Plot of residuals).

## 3. File Formats

### 3.1. partition_counts.csv
-   **Delimiter**: `,`
-   **Header**: `n,p_P_n`
-   **Encoding**: UTF-8

### 3.2. features.csv
-   **Delimiter**: `,`
-   **Header**: `n,p_P_n,Q_as_n,R_n,pi_n,inv_log_n,cum_density`
-   **Encoding**: UTF-8
-   **Constraints**:
    -   `n` must be integer $> 0$.
    -   `p_P_n` must be integer $\ge 0$.
    -   `Q_as_n` must be float $> 0$ (clamped).
    -   `R_n` must be float (NaN if `p_P_n` or `Q_as_n` invalid; rows with NaN are excluded from regression).
    -   `pi_n` must be integer $\ge 0$.
    -   `inv_log_n` must be float $> 0$.
    -   `cum_density` must be float $> 0$.

### 3.3. model_results.json
-   **Format**: JSON
-   **Structure**:
    ```json
    {
      "coefficients": { "pi_n": 0.0, "inv_log_n": 0.0, ... },
      "intercept": 0.0,
      "r_squared": 0.0,
      "p_values": { "pi_n": 0.0, ... },
      "mse_cv": 0.0,
      "fdr_corrected_p_values": { ... },
      "null_model_R2": 0.0,
      "null_model_MSE": 0.0
    }
    ```

### 3.4. reference_data.csv
-   **Delimiter**: `,`
-   **Header**: `n,p_P_n`
-   **Content**: Reference values for $n \le 100$.

## 4. Validation Rules

-   **Monotonicity**: $p_{\mathcal{P}}(n)$ should generally be non-decreasing (though local fluctuations exist, the cumulative count grows).
-   **Log-Domain**: $R(n)$ is only computed where $p_{\mathcal{P}}(n) > 0$ and $Q_{as}(n) > 0$.
-   **Density Check**: $\pi(n)$ must match the count of primes $\le n$ in the precomputed list.
-   **No NaN**: Final `features.csv` used for regression must exclude rows where `R_n` is NaN.
-   **Reference Match**: Computed values for $n \le 100$ must match `reference_data.csv` exactly.
