# Data Model: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## Entities

### TimeSeries
| Field | Type | Description |
|-------|------|-------------|
| `quarter` | string (ISO‑format, e.g., `"2020-Q1"`) | Quarterly timestamp, primary key. |
| `sentiment_pos_ratio` | float | Ratio of positive sentiment scores (confidence ≥ 0.7) within the quarter. |
| `sentiment_neg_ratio` | float | Ratio of negative sentiment scores (confidence ≥ 0.7) within the quarter. |
| `sentiment_neu_ratio` | float | Ratio of neutral sentiment scores (confidence ≥ 0.7) within the quarter. |
| `sentiment_ilr_1` | float | First ILR component derived from the three sentiment ratios (log‑ratio transformation). |
| `sentiment_ilr_2` | float | Second ILR component derived from the three sentiment ratios. |
| `gdp_growth` | float | Quarterly GDP growth rate (percent). |
| `unemployment_rate` | float | Quarterly unemployment rate (percent). |
| `consumer_confidence` | float | Quarterly Consumer Confidence Index (percent). |
| `low_confidence_flag` | boolean | `true` if the quarter had insufficient sentiment sample size (< 30 tweets). |
| `interpolation_percent_gdp` | float | Percentage of GDP points filled by linear interpolation. |
| `interpolation_percent_unrate` | float | Percentage of UNRATE points filled by linear interpolation. |
| `interpolation_percent_cons_conf` | float | Percentage of Consumer Confidence points filled by linear interpolation. |
| `vif_gdp` | float | VIF for GDP series (for collinearity diagnostics). |
| `vif_unrate` | float | VIF for Unemployment series. |
| `vif_cons_conf` | float | VIF for Consumer Confidence series. |

### ModelResult
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string (`"VAR"` or `"VECM"`) | Model fitted after cointegration decision. |
| `optimal_lag` | integer | Lag order selected by AIC. |
| `cointegration_rank` | integer | Rank from Johansen trace statistic (0 if none). |
| `granger_results` | list of objects | Each object contains `direction` (`"sentiment→gdp"` etc.), `f_stat`, `p_value`, `p_value_fdr`. |
| `bootstrap_ci` | object | Keys are coefficient names; values are `{ "lower": float, "upper": float }`. |
| `sensitivity_shifts` | list of objects | Each entry records `masking_proportion`, `p_value_shift`, `direction`. |
| `recession_validation` | object | Contains `masked_periods`, `coeff_shift`, `passed`. |
| `vif` | object | VIF values for macro predictors. |
| `run_timestamp` | string (ISO‑8601) | When the analysis was executed. |
| `random_seed` | integer | Seed used for bootstrap and sensitivity sampling. |
| `block_length` | integer | Block length (weeks) used for Moving Block Bootstrap. |

### RecessionPeriod
| Field | Type | Description |
|-------|------|-------------|
| `start_date` | string (ISO‑date) | Start of recession (NBER). |
| `end_date` | string (ISO‑date) | End of recession (NBER). |
| `label` | string | Human‑readable label (e.g., `"2008‑2009 Financial Crisis"`). |

## Relationships
- `TimeSeries` rows are merged on `quarter` to build the modeling matrix.
- `ModelResult` references the set of `RecessionPeriod` used for validation.
- All entities are stored as CSV/JSON files under `data/processed/` and `outputs/`.

---


