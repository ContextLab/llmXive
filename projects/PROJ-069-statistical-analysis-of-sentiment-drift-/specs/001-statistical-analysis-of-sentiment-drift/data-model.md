# Data Model: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## Entities

### TimeSeries (Quarterly Aligned)
| Field | Type | Description |
|-------|------|-------------|
| `quarter` | string (ISO‑format, e.g., `"2020-Q1"`) | Primary key. |
| `sentiment_pos_ratio` | float (0‑1) | Proportion of positive sentiment scores (confidence ≥ 0.7). |
| `sentiment_neg_ratio` | float (0‑1) | Proportion of negative sentiment scores (confidence ≥ 0.7). |
| `sentiment_neu_ratio` | float (0‑1) | Proportion of neutral sentiment scores (confidence ≥ 0.7). |
| `sentiment_ilr_1` | float | First ILR component derived from the three ratios. |
| `sentiment_ilr_2` | float | Second ILR component derived from the three ratios. |
| `media_volume` | integer | Total number of sentiment‑bearing social‑media posts (tweets) observed in the quarter; used as a control variable for omitted‑variable bias. |
| `gdp_growth` | float | Quarterly GDP growth rate (percent). |
| `unemployment_rate` | float | Quarterly unemployment rate (percent). |
| `consumer_confidence` | float | Quarterly Consumer Confidence Index (percent). |
| `low_confidence_flag` | boolean | `true` if the quarter lacked sufficient sentiment sample size. |
| `interpolation_percent_gdp` | float (0‑100) | % of GDP points filled by linear interpolation. |
| `interpolation_percent_unrate` | float (0‑100) | % of UNRATE points filled by linear interpolation. |
| `interpolation_percent_cons_conf` | float (0‑100) | % of Consumer Confidence points filled by linear interpolation. |
| `vif_gdp` | float | VIF for GDP series (collinearity diagnostic). |
| `vif_unrate` | float | VIF for unemployment series. |
| `vif_cons_conf` | float | VIF for consumer confidence series. |

### TimeSeriesMonthly (Intermediate Monthly Alignment)
| Field | Type | Description |
|-------|------|-------------|
| `date` | string (ISO‑format `YYYY‑MM`) | Primary key for monthly aggregation. |
| `sentiment_pos_ratio` | float (0‑1) | Monthly proportion of positive sentiment. |
| `sentiment_neg_ratio` | float (0‑1) | Monthly proportion of negative sentiment. |
| `sentiment_neu_ratio` | float (0‑1) | Monthly proportion of neutral sentiment. |
| `sentiment_ilr_1` | float | ILR component (monthly). |
| `sentiment_ilr_2` | float | ILR component (monthly). |
| `media_volume` | integer | Monthly tweet count. |
| `gdp_growth` | float | Monthly GDP growth (derived from quarterly series). |
| `unemployment_rate` | float | Monthly unemployment rate. |
| `consumer_confidence` | float | Monthly consumer confidence index. |
| `low_confidence_flag` | boolean | `true` if the month has insufficient sentiment volume. |
| `interpolation_percent_gdp` | float (0‑100) | % of GDP points interpolated in this month. |
| `interpolation_percent_unrate` | float (0‑100) | % of UNRATE points interpolated in this month. |
| `interpolation_percent_cons_conf` | float (0‑100) | % of Consumer Confidence points interpolated in this month. |
| `vif_gdp` | float | VIF for GDP (monthly view). |
| `vif_unrate` | float | VIF for unemployment (monthly view). |
| `vif_cons_conf` | float | VIF for consumer confidence (monthly view). |

### ModelResult
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string (`"VAR"` or `"VECM"`) | Model fitted after cointegration decision. |
| `optimal_lag` | integer | Lag order selected via AIC. |
| `cointegration_rank` | integer | Rank from Johansen trace statistic (0 if none). |
| `granger_results` | list of objects | Each object: `direction`, `f_stat`, `p_value`, `p_value_fdr`. |
| `bootstrap_ci` | object | Keys = coefficient names; values = `{ "lower": float, "upper": float }`. |
| `sensitivity_shifts` | list of objects | Each: `masking_proportion`, `p_value_shift`, `direction`. |
| `recession_validation` | object | Contains `masked_periods`, `coeff_shift`, `passed`. |
| `vif` | object | VIF values for macro predictors. |
| `run_timestamp` | string (ISO‑8601) | Execution time. |
| `random_seed` | integer | Seed used for bootstrap & sensitivity sampling. |
| `block_length` | integer | Block length (weeks) used for Moving Block Bootstrap. |

### RecessionPeriod
| Field | Type | Description |
|-------|------|-------------|
| `start_date` | string (ISO‑date) | Start of recession (NBER). |
| `end_date` | string (ISO‑date) | End of recession (NBER). |
| `label` | string | Human‑readable label (e.g., `"2008‑2009 Financial Crisis"`). |

## Relationships
- `TimeSeries` rows are merged on `quarter` to create the modeling matrix.  
- `TimeSeriesMonthly` rows are merged on `date` to produce `aligned_monthly.csv` before quarterly aggregation.  
- `ModelResult` references the set of `RecessionPeriod` used for validation.  
- All entities are persisted as CSV/JSON files under `data/processed/` and `outputs/`.

---



