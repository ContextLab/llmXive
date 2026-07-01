# Data Model: Statistical Analysis of Flight Delay Distributions

## Entity Definitions

### DelayRecord
Represents a single flight event after cleaning.
-   `flight_id`: string (unique identifier, e.g., "2022-1010-12345")
-   `carrier`: string (airline code)
-   `origin`: string (airport code)
-   `destination`: string (airport code)
-   `arr_delay`: float (minutes, may be 0 or NaN treated as 0)
-   `dep_delay`: float (minutes, may be 0 or NaN treated as 0)
-   `total_delay_minutes`: float (computed: `arr_delay + dep_delay`)
-   `is_anomaly`: boolean (true if `1440 < total_delay <= 10000`)
-   `is_data_error`: boolean (true if `total_delay > 10000`)
-   `is_zero`: boolean (true if `total_delay == 0`)

### DistributionModel
Represents a fitted parametric distribution.
-   `name`: string (e.g., "Log-Normal", "Pareto")
-   `parameters`: object (key-value pairs of MLE estimates, e.g., `{"loc": 0, "scale": 15.2, "shape": 0.5}`)
-   `metrics`: object
    -   `aic`: float (calculated on tail subset for Vuong comparison)
    -   `bic`: float
    -   `ks_statistic`: float
    -   `ks_pvalue`: float
    -   `ad_statistic`: float
-   `tail_fit`: object (only for Pareto)
    -   `x_min`: float
    -   `alpha`: float
-   `converged`: boolean
-   `is_valid_tail`: boolean (True if Bootstrap GoF p-value >= 0.1)
-   `causality_disclaimer`: string ("Associational only")

### TailIndexEstimate
Represents the heavy-tail diagnostic result.
-   `method`: string ("Hill")
-   `threshold_k`: integer (number of records used)
-   `estimated_alpha`: float (tail index)
-   `confidence_interval`: object (`{"lower": float, "upper": float}`)
-   `stability_range`: object (`{"min_k": int, "max_k": int, "variance_min": float}`)
-   `log_log_r_squared`: float (visualization only)
-   `tail_ks_pvalue`: float (bootstrapped)
-   `log_normal_discrimination`: object (`{"curvature_stat": float, "p_value": float}`)

### ComponentComparison
Represents the comparison between total delay and component delays.
-   `sum_vs_arr_ks_stat`: float
-   `sum_vs_arr_ks_pvalue`: float
-   `sum_vs_dep_ks_stat`: float
-   `sum_vs_dep_ks_pvalue`: float
-   `histogram_file`: string (path to saved plot)

## Data Flow

1.  **Raw Input**: BTS CSV/Parquet (columns: `ArrDelay`, `DepDelay`, `Carrier`, etc.).
2.  **Cleaned Dataset**: `DelayRecord` list (filtered, flags added).
    -   *Primary Subset*: `is_data_error == False`.
    -   *Tail Subset*: `total_delay_minutes >= x_min` AND `is_zero == False`.
3.  **Model Outputs**: `DistributionModel` list.
4.  **Diagnostic Outputs**: `TailIndexEstimate` object, `ComponentComparison` object.

## Constraints
-   `total_delay_minutes` >= 0.
-   `estimated_alpha` > 0 (for heavy tail).
-   `log_log_r_squared` >= 0 (visualization only, not a gate).
