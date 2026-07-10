# Data Model: Statistical Properties of Integer Partitions

## 1. Entity Definitions

### 1.1 PartitionRecord
Represents the ground truth data for a single integer $n$.
*   **n**: Integer. The integer being partitioned.
*   **count**: Integer. The exact value of $p_{\mathcal{P}}(n)$.
*   **asymptotic**: Float. The predicted value $Q_{as}(n)$ based on the leading-order Roth & Szekeres term.
*   **log_residual**: Float. $\log(\text{count}) - \log(\text{asymptotic})$. Null if count is 0.

### 1.2 DensityFeatureSet
Represents the predictor variables for a single integer $n$.
*   **n**: Integer.
*   **inv_log_n_sq**: Float. $1 / (\ln(n))^2$.
*   **log_log_n_over_log_n**: Float. $\ln \ln(n) / \ln(n)$.
*   **prime_density**: Float. $\pi(n) / n$.
*   **dist_nearest_prime**: Integer. Distance to the closest prime.
*   **sin_log_n**: Float. $\sin(\ln(n))$.
*   **cos_log_n**: Float. $\cos(\ln(n))$.

### 1.3 RegressionOutput
Represents the results of the statistical model.
*   **coefficients**: Dict mapping feature names to float values (or smooth term statistics for GAM).
*   **p_values**: Dict mapping feature names to float values.
*   **r_squared**: Float.
*   **mse_cv**: Float. Mean Squared Error from cross-validation.
*   **adjusted_p_values**: Dict mapping feature names to float values (Bonferroni corrected).
*   **vif_scores**: Dict mapping feature names to VIF values.

## 2. Data Flow

1.  **Input**: None (Primes generated internally).
2.  **Step 1 (Generation)**: `generate_partitions.py` -> `data/raw/partitions_raw.csv`. **Checksum generated and recorded in state file.**
3.  **Step 2 (Features)**: `feature_engineering.py` reads `partitions_raw.csv`, computes features, writes `data/processed/features.csv`.
4.  **Step 3 (Modeling)**: `regression_model.py` reads `features.csv`, fits GAM model, calculates VIF, writes `data/processed/model_results.json`.
5.  **Step 4 (Visualization)**: `visualize_results.py` reads `features.csv` and `model_results.json`, writes plots.

## 3. Constraints

*   **Integrity**: `count` must be $\ge 0$. `asymptotic` must be $> 0$.
*   **Precision**: `count` must fit in `int64`. `log_residual` must be `float64`.
*   **Filtering**: Rows with `count == 0` are excluded from the regression dataset.