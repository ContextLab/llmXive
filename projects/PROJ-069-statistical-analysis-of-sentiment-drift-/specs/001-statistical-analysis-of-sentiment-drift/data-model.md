# Data Model: Statistical Analysis of Sentiment Drift

## 1. Entity Definitions

### TimeSeries
Represents the aligned weekly data points.
- **Attributes**:
  - `date`: `YYYY-MM-DD` (ISO 8601, weekly frequency, Monday start).
  - `sentiment_positive`: `float` (0.0 - 1.0, ratio).
  - `sentiment_negative`: `float` (0.0 - 1.0, ratio).
  - `sentiment_neutral`: `float` (0.0 - 1.0, ratio).
  - `gdp_growth_qoq`: `float` (Quarterly growth rate, forward-filled to weekly).
  - `unemployment_rate`: `float` (Percentage).
  - `vix_index`: `float` (Market volatility index).
  - `confidence_score`: `float` (Average prediction confidence for that week).
  - `sample_size`: `int` (Number of posts in the week).
  - `is_low_confidence`: `bool` (True if `sample_size` < 100 or `confidence_score` < 0.7).
  - `is_recession`: `bool` (True if date falls within NBER recession dates).
  - `release_dummy`: `bool` (True if week contains a quarterly GDP release).

### ModelResult
Represents statistical output.
- **Attributes**:
  - `test_type`: `string` (e.g., "ADF", "Granger", "VAR", "VECM", "Johansen").
  - `variable_pair`: `string` (e.g., "Sentiment->GDP").
  - `statistic`: `float` (Test statistic value).
  - `p_value`: `float`.
  - `lag_order`: `int` (For VAR/Granger).
  - `stationary`: `bool`.
  - `transformation`: `string` (e.g., "1st_diff", "log", "none", "vecm").
  - `cointegrated`: `bool` (Result of Johansen test).

### ImputationLog
Records the specific imputation method and percentage of data affected.
- **Attributes**:
  - `variable`: `string` (e.g., "GDP", "Sentiment").
  - `method`: `string` (e.g., "forward_fill", "linear", "none").
  - `percentage_affected`: `float` (0.0 - 1.0).
  - `flagged_periods`: `list` (List of dates where missing > threshold).

### ValidationSplit
Represents the train/test split for out-of-sample validation.
- **Attributes**:
  - `split_type`: `string` (e.g., "recession_holdout").
  - `train_start`: `YYYY-MM-DD`.
  - `train_end`: `YYYY-MM-DD`.
  - `test_start`: `YYYY-MM-DD`.
  - `test_end`: `YYYY-MM-DD`.
  - `purpose`: `string` (e.g., "Validate Granger Causality on 2020 Recession").

### RecessionPeriod
- **Attributes**:
  - `start_date`: `YYYY-MM-DD`.
  - `end_date`: `YYYY-MM-DD`.
  - `source`: `string` (e.g., "NBER").

## 2. Data Flow

1.  **Ingestion**: Raw JSON/Parquet from FRED/HF $\to$ `data/raw/`.
2.  **Preprocessing**:
    - Frequency conversion (Daily $\to$ Weekly).
    - Interpolation (Forward-fill GDP, Linear Sentiment).
    - Filtering (Low confidence flagging).
    - Output: `data/processed/merged_timeseries.csv`, `data/processed/imputation_log.json`.
3.  **Analysis**:
    - ADF Test $\to$ Stationarity Log.
    - Johansen Test $\to$ Cointegration Log.
    - VAR/VECM Fit $\to$ Model Parameters.
    - Granger Test $\to$ P-values.
    - MBB $\to$ Confidence Intervals.
    - Out-of-Sample Test $\to$ Holdout Results.
4.  **Visualization**: `data/processed/merged_timeseries.csv` + `ModelResult` $\to$ Plots (PNG/SVG).

## 3. Constraints & Rules

- **Alignment**: All rows must have a valid `date`. No missing dates in the final merged CSV.
- **Missing Data**:
 - GDP/Unemployment: Max [deferred] missing (forward-filled).
 - Sentiment: Max [deferred] missing (linearly interpolated).
  - If missing > 5%, the period is flagged and excluded from primary analysis.
- **Stationarity**: All series used in VAR must be I(0) (stationary). If not, differencing is applied and logged.
- **Cointegration**: If variables are cointegrated, VECM is used instead of VAR.
- **Reproducibility**: All random seeds for MBB and data generation (if synthetic) must be set to a fixed integer (e.g., 42).
- **Data Source Flag**: All output artifacts must include a `data_source` flag (`real` or `synthetic`).

## 4. Schema Validation Rules

- `date`: Must be unique and sorted ascending.
- `sentiment_*`: Must sum to $\approx 1.0$ (within tolerance 0.01).
- `gdp_growth_qoq`: Can be negative.
- `unemployment_rate`: Must be between 0 and 100.
- `is_low_confidence`: Derived field, must be consistent with `sample_size` and `confidence_score`.
- `imputation_log`: Must exist for every variable in the dataset.