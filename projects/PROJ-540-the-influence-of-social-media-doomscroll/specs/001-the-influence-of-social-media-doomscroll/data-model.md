# Data Model: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Entity Definitions

### SurveyResponse (cleaned row)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | string | Anonymized unique identifier | non‑null, unique |
| `news_exposure_freq` | number | Frequency of negative news consumption on social media (proxy) | non‑null, ≥ 0 |
| `anxiety_score` | number | Outcome anxiety score (validated scale or proxy) | non‑null, ≥ 0 |
| `baseline_anxiety` | number | Baseline/trait anxiety (may be null) | nullable, ≥ 0 |
| `age` | integer | Age in years | non‑null, 18 ≤ age ≤ 100 |
| `gender` | string | Gender category | one of “Male”, “Female”, “Other”, “Non-binary” |
| `social_media_engagement` | number | Hours per day (or equivalent) of overall social‑media use. | nullable, ≥ 0 |
| `instrument_source` | string | Name of the anxiety instrument (e.g., “GAD‑7”). | non‑null |
| `measurement_timepoint` | string | “pre”, “post”, or “trait”. | non‑null |
| `proxy_flag` | boolean | True if `anxiety_score` is a proxy for anticipatory anxiety. | non‑null |
| `coupling_risk` | boolean | True if baseline and outcome anxiety may be mathematically coupled. | non‑null |

### RegressionResult (analysis output)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"OLS"` |
| `n_samples` | integer | Number of rows used after cleaning |
| `r_squared` | number | Coefficient of determination |
| `adj_r_squared` | number | Adjusted R² |
| `f_statistic` | number | Overall model F‑statistic |
| `f_pvalue` | number | P‑value for the F‑statistic |
| `coefficients` | object | Mapping `variable → coefficient` |
| `std_errors` | object | Mapping `variable → standard error` |
| `p_values` | object | Mapping `variable → p‑value` |
| `vif_scores` | object | Mapping `variable → VIF` |
| `assumption_checks` | object | Results of linearity, homoscedasticity, normality, Shapiro‑Wilk p‑value |
| `robustness_result` | object | `null` if skipped, otherwise `{subset_n, coefficient, p_value, status}` |
| `flags` | array[string] | Warnings such as “Low Power”, “Proxy Used”, “High VIF”, “Robustness Skipped (r ≤ 0.3)” |
| `runtime` | number | Total execution time in seconds (SC‑005) |

## Data Flow
1. **Raw download** → `data/raw/` (parquet).  
2. **Streaming schema validation** → `contracts/dataset.schema.yaml`.  
3. **Cleaning & listwise deletion** → `data/processed/cleaned_data.csv` (conforms to `SurveyResponse`).  
4. **Model fitting & diagnostics** → `output/results/regression_results.json` (conforms to `RegressionResult`).  
5. **Visualization** → `output/plots/scatter_regression.png`.  

## Assumptions & Constraints
- No imputation; rows with missing primary predictor/outcome are removed.  
- Categorical `gender` is one‑hot encoded for OLS.  
- All continuous predictors are used in original scale (no standardization required for OLS).  
- If `baseline_anxiety` is not distinct, it is dropped and `coupling_risk` set to `true`.  
- If `social_media_engagement` is absent, robustness check is automatically **skipped** with a warning flag.  

---


