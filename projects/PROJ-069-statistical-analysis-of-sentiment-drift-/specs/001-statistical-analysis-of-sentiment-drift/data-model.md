# Data Model: Statistical Analysis of Sentiment Drift

## 1. Entity Definitions

### TimeSeries
Represents the aligned quarterly data points.

*Fields*:
- `date` (string): ISO 8601 quarter‑end date (e.g., `"2008-12-31"`).
- `sentiment_positive` (float): Ratio of positive sentiment (0.0 – 1.0).
- `sentiment_negative` (float): Ratio of negative sentiment (0.0 – 1.0).
- `sentiment_neutral` (float): Ratio of neutral sentiment (0.0 – 1.0).
- `sentiment_confidence` (float): Mean confidence of sentiment predictions (0.0 – 1.0).
- `gdp_growth` (float): Quarterly GDP growth rate (%).
- `unemployment_rate` (float): Unemployment rate (%).
- `consumer_confidence` (float): Consumer Confidence Index (standardized).
- `sample_size` (integer): Number of tweets aggregated in the quarter.
- `is_low_confidence` (boolean): True if `sample_size` < 100 or `sentiment_confidence` < 0.7.
- `is_recession` (boolean): True if the date falls within an NBER recession period.
- `missing_rate` (float): Proportion of imputed values for this row (≤ 0.05).

### ModelResult
Represents statistical test outputs.

*Fields*:
- `test_type` (string): `"ADF"`, `"Johansen"`, `"Granger"`, `"MBB"`.
- `variable_pair` (string): e.g., `"Sentiment → GDP"`.
- `statistic` (float): Test statistic (ADF, F‑stat, etc.).
- `p_value` (float).
- `optimal_lag` (integer, optional): Lag order selected by AIC (VAR only).
- `cointegration_rank` (integer, optional): Rank from Johansen test.
- `confidence_interval` (list[float]): `[lower, upper]` for MBB estimates.
- `block_length` (integer, optional): Block length used in MBB (quarters).
- `masking_proportion` (float, optional): Proportion of data masked in sensitivity analysis.
- `is_significant` (boolean): `p_value < 0.05`.

### RecessionPeriod
Represents known economic downturns.

*Fields*:
- `start_date` (string): ISO 8601.
- `end_date` (string): ISO 8601.
- `source` (string): `"NBER"`.

## 2. Data Flow

1. **Raw Ingestion** (`data/raw/`):
   - `fred_gdp.csv`, `fred_unrate.csv`, `fred_consumer_confidence.csv`
   - `sentiment_daily.json`, `nber_recessions.csv`
2. **Preprocessing** (`data/processed/`):
   - `sentiment_monthly.csv` (intermediate)
   - `aligned_quarterly.csv` (final merged file)
3. **Modeling** (`results/`):
   - `model_stats.json`
4. **Validation** (`results/`):
   - `validation_stats.json`
5. **Reporting** (`docs/paper/` & `plots/`).

## 3. Schema Constraints (mirrored in contracts)

- **Date Format**: `YYYY-MM-DD`.
- **Polarity Sum**: `sentiment_positive + sentiment_negative + sentiment_neutral ≈ 1.0`.
- **Missing Rate**: `missing_rate ≤ 0.05`.
- **No NaNs** in `aligned_quarterly.csv`; any missing value must be interpolated and logged.
- **Sample Size**: Rows with `sample_size < 100` are flagged but retained for diagnostics.
