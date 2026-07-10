# Data Model: Statistical Analysis of Sentiment Drift

## Key Entities

### 1. TimeSeries (Aligned)
Represents the merged, **monthly** dataset.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `date` | `string` | ISO 8601 Month (e.g., "2020-03") | Unique, sorted ascending |
| `sentiment_positive` | `float` | Mean ratio of positive sentiment | [0.0, 1.0] |
| `sentiment_negative` | `float` | Mean ratio of negative sentiment | [0.0, 1.0] |
| `sentiment_neutral` | `float` | Mean ratio of neutral sentiment | [0.0, 1.0] |
| `sentiment_confidence` | `float` | Mean confidence of predictions | [0.0, 1.0] |
| `sentiment_n` | `integer` | Number of items in month | ≥0 |
| `sentiment_low_confidence` | `boolean` | True if `sentiment_n` < threshold OR `sentiment_confidence` < 0.7 | Enforced by logic |
| `gdp_growth` | `float` | Monthly GDP growth rate (%) | - |
| `unemployment_rate` | `float` | Monthly average unemployment rate (%) | - |
| `consumer_confidence` | `float` | Monthly Consumer Confidence Index | - |
| `is_recession` | `boolean` | True if date falls within NBER recession period | - |
| `gdp_missing` | `boolean` | True if original value was missing and interpolated | - |
| `unrate_missing` | `boolean` | True if original value was missing and interpolated | - |
| `missing_rate` | `float` | Proportion of imputed values for this row (≤ 0.05) | - |

### 2. ModelResult
Represents the output of the Granger Causality and VAR tests.

| Field | Type | Description |
|-------|------|-------------|
| `test_type` | `string` | "Granger", "ADF", "Johansen", "VAR" |
| `variable_pair` | `string` | e.g., "Sentiment_Pos -> GDP" |
| `lag_order` | `integer` | Optimal lag selected |
| `statistic` | `float` | F-statistic or ADF statistic |
| `p_value` | `float` | P-value of the test |
| `is_significant` | `boolean` | True if p < 0.05 (after correction) |
| `method` | `string` | "VAR", "VECM", "ADF" |
| `stationary` | `boolean` | Result of stationarity test |

### 3. RecessionPeriod
Represents NBER recession dates for visualization.

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | `string` | ISO 8601 Date (YYYY-MM-DD) |
| `end_date` | `string` | ISO 8601 Date (YYYY-MM-DD) |
| `source` | `string` | "NBER Business Cycle Dating Committee" |

### 4. BootstrapResult
Represents Moving Block Bootstrap validation metrics.

| Field | Type | Description |
|-------|------|-------------|
| `metric` | `string` | e.g., "Granger_F_stat", "Coefficient" |
| `original_value` | `float` | Value from baseline model |
| `ci_lower` | `float` | 95% CI lower bound |
| `ci_upper` | `float` | 95% CI upper bound |
| `ci_width` | `float` | `ci_upper - ci_lower` |
| `standard_error` | `float` | Standard error of the estimate |
| `consistency_pass` | `boolean` | True if `ci_width` ≤ 20% of `original_value` AND CV < 0.1 |
| `convergence_achieved` | `boolean` | True if CI width stabilized |

## Data Flow

1.  **Ingestion**: Raw GDELT/FRED data → `data/raw/` (checksummed).
2.  **Alignment**: Raw data → `data/processed/aligned_monthly.csv` (TimeSeries).
3.  **Modeling**: Aligned data → `data/processed/model_results.json` (ModelResult).
4.  **Validation**: Model results → `data/processed/bootstrap_metrics.json` (BootstrapResult).
5.  **Reporting**: All processed data → `notebooks/analysis_master.ipynb` → Final PDF/HTML.