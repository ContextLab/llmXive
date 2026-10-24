# Data Model: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Entity Definitions

### SurveyResponse (cleaned row – only present if a verified dataset passes schema validation)

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| `participant_id` | string | Anonymized unique identifier | non‑null, unique |
| `news_exposure_freq` | number | Frequency of negative news consumption on social media | non‑null, ≥ 0 |
| `anxiety_score` | number | Outcome anxiety score (validated scale or flagged proxy) | non‑null, ≥ 0 |
| `baseline_anxiety` | number | null | Baseline/trait anxiety; may be null if instrument overlaps with outcome; ≥ 0 |
| `age` | integer | Age in years | non‑null, 18 – 100 |
| `gender` | string | Gender category | non‑null, categorical |
| `social_media_engagement` | number | null | Overall social‑media use; required only for robustness check; ≥ 0 |
| `instrument_source` | string | Name of the anxiety instrument (e.g., GAD‑7) | non‑null |
| `measurement_timepoint` | string | Timepoint of measurement (pre, post, trait) | non‑null |
| `proxy_flag` | boolean | True if `anxiety_score` is a proxy for anticipatory anxiety (FR‑008) | non‑null |
| `coupling_risk` | boolean | True if baseline and outcome anxiety may be mathematically coupled | non‑null |

### RegressionResult (analysis output – always a single JSON file)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"OLS"` |
| `data_status` | string | `"OK"` when a verified dataset passed validation; `"HALTED_NO_VALID_DATASET"` when ingestion halted (current expected state). |
| `n_samples` | integer | Rows used after listwise deletion (present only when `data_status = "OK"`). |
| `r_squared` | number | Model R² (present only when `data_status = "OK"`). |
| `adj_r_squared` | number | Adjusted R² (present only when `data_status = "OK"`). |
| `f_statistic` | number | Overall F‑statistic (present only when `data_status = "OK"`). |
| `f_pvalue` | number | P‑value for the overall F‑test (present only when `data_status = "OK"`). |
| `coefficients` | object | Mapping *variable → coefficient* (real estimates only). |
| `std_errors` | object | Mapping *variable → standard error*. |
| `p_values` | object | Mapping *variable → two‑sided p‑value*. |
| `vif_scores` | object | Mapping *variable → VIF*; VIF > 10 triggers a flag. |
| `assumption_checks` | object | `{linearity, homoscedasticity, normality, shapiro_wilk_p_value}` (PASS/FAIL/WARNING). |
| `robustness_result` | object | null | If robustness check runs: `{subset_n, coefficient, p_value, status}`; otherwise null. |
| `flags` | array[string] | Warnings such as `"Low Power"`, `"Proxy Used"`, `"High VIF"`, `"Robustness Skipped (r <= 0.3)"`, `"Associational Only"`. |
| `runtime` | number | Execution time in seconds (SC‑005). |
| `halt_report` | object | null | Present only when `data_status = "HALTED_NO_VALID_DATASET"`; records sources checked, checksums, column inventories, and missing variables. |

### HaltReport (nested inside `RegressionResult` when ingestion fails)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"HALTED_NO_VALID_DATASET"` |
| `sources_checked` | array[object] | Each entry: `{url, sha256, row_count}` for the three verified parquet files. |
| `columns_found` | object | Mapping *url → list of column names* actually present. |
| `missing_variables` | array[string] | Required variables absent from **all** sources. |
| `reason` | string | Human‑readable statement of the mismatch (FR‑001 edge case). |

## Data Flow
1. **Ingestion** (`code/ingest.py`): download verified parquet files → `data/raw/`; compute SHA‑256; validate schema against `contracts/dataset.schema.yaml`.  
2. **If validation fails** (current reality): create `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"` and embed a complete `halt_report`; pipeline stops.  
3. **If validation succeeds** (future scenario): clean data → `data/processed/cleaned_data.csv`.  
4. **Modeling** (`code/model.py`): OLS fit, diagnostics, correlation, robustness → populate all fields of `RegressionResult`.  
5. **Visualization** (`code/viz.py`): generate `output/plots/scatter_regression.png`.  
6. **Success‑criteria validation** (`code/validate_sc.py`): read the JSON, write `outputs/success_criteria_log.txt`.  
7. **Archiving & Sign‑off** (`artifacts/project_artifact.zip`, `outputs/signoff_report.json`).

## Assumptions & Constraints
- No imputation; rows with missing predictor/outcome are dropped (listwise deletion).  
- Gender is one‑hot encoded for OLS; continuous predictors remain on original scale.  
- `baseline_anxiety` is dropped (and `coupling_risk = true`) if the same instrument/timepoint is detected as `anxiety_score`.  
- Robustness check runs only when `social_media_engagement` exists **and** `r_engage > 0.3`.  
- All numeric computations use double precision on CPU; no GPU resources required.

---
