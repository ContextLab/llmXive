# Data Model: Statistical Analysis of Flight Delay Distributions

## Entities

### DelayRecord
Represents a single flight event after pre-processing.
- `flight_id`: string (unique identifier, derived from `FlightNum` + `Date`)
- `total_delay_minutes`: float (sum of `ArrDelay` and `DepDelay`, $\ge 0$)
- `carrier`: string (IATA code)
- `origin`: string (IATA code)
- `destination`: string (IATA code)
- `is_anomaly`: boolean (true if `delay > 1440` minutes)
- `is_data_error`: boolean (true if `delay > 10000` minutes)
- `is_zero`: boolean (true if `total_delay == 0`)

### DistributionModel
Represents a fitted parametric distribution.
- `name`: string (e.g., "Log-Normal", "Pareto")
- `parameters`: object (key-value pairs of MLE estimates, e.g., `{"s": 0.5, "scale": 100}`)
- `metrics`: object
  - `aic`: float
  - `bic`: float
  - `ks_stat`: float
  - `ks_pvalue`: float
  - `ad_stat`: float
  - `tail_ks_stat`: float (KS statistic on tail subset)
  - `tail_ks_p_value`: float (KS p-value on tail subset)
  - `x_min`: float (threshold used)

### TailIndexEstimate
Represents the result of the heavy-tail diagnostic.
- `method`: string (e.g., "Hill")
- `threshold_k`: integer (number of top records used)
- `threshold_x_min`: float (delay value at threshold)
- `estimated_alpha`: float (tail index)
- `confidence_interval`: object (`{"lower": float, "upper": float}`)
- `stability_range`: object (`{"start_k": int, "end_k": int}`)
- `r_squared_log_log`: float (from OLS on log-log survival plot)
- `is_rejected`: boolean (true if $R^2 < 0.95$ or unstable)
- `reason`: string (if rejected)

## Data Flow

1. **Raw Input**: BTS CSV files (streamed from `transtats.bts.gov`).
2. **Pre-Processing**:
   - Calculate `total_delay = ArrDelay + DepDelay`.
   - Treat NaN as 0.
   - Remove negative values.
   - Flag anomalies ($>1440$) and data errors ($>10000$).
   - Output: `data/processed/cleaned_delays.csv`.
3. **Model Fitting**:
   - Fit 5 distributions to `total_delay` (full and tail subsets).
   - Output: `data/results/model_comparison.json`, `data/results/vuong_test.json`.
4. **Diagnostics**:
   - Compute $x_{min}$ via Clauset method.
   - Compute Hill estimator on tail ($x \ge x_{min}$).
   - Generate log-log plot and compute $R^2$.
   - Output: `data/results/tail_index_estimate.json`, `data/results/tail_ks.json`.
5. **Component Comparison**:
   - Compare sum vs components.
   - Output: `data/results/component_comparison.json`.

## File Outputs

| File Path | Format | Description |
|-----------|--------|-------------|
| `data/processed/cleaned_delays.csv` | CSV | Cleaned dataset with flags. |
| `data/results/summary.json` | JSON | Retention rate, runtime, metadata. |
| `data/results/model_comparison.json` | JSON | AIC, BIC, KS, AD for all 5 models (full and tail). |
| `data/results/vuong_test.json` | JSON | Vuong test p-value comparing heavy vs short tail. |
| `data/results/tail_index_estimate.json` | JSON | Hill estimator results, $x_{min}$, $R^2$, stability. |
| `data/results/tail_ks.json` | JSON | KS test p-value on the tail subset. |
| `data/results/component_comparison.json` | JSON | KS test comparing sum vs individual components. |
| `data/results/figures/log_log_survival.png` | PNG | Log-log survival plot. |
| `data/results/figures/qq_plot.png` | PNG | QQ plot for best model. |

