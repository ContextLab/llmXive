# Data Model: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Entity Definitions

### SurveyResponse (cleaned row – only present if a verified dataset passes schema validation)

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| `participant_id` | string | Anonymized unique identifier | non‑null, unique |
| `news_exposure_freq` | number | Frequency of negative news consumption on social media | non‑null, ≥ 0 |
| `anxiety_score` | number | Outcome anxiety score (validated scale or flagged proxy) | non‑null, ≥ 0 |
| `baseline_anxiety` | number \| null | Baseline/trait anxiety; may be null if instrument overlaps with outcome | ≥ 0 |
| `age` | integer | Age in years | non‑null, 18 – 100 |
| `gender` | string | Gender category | non‑null, categorical |
| `social_media_engagement` | number \| null | Overall social‑media use; required only for robustness check | ≥ 0 |
| `instrument_source` | string | Name of the anxiety instrument (e.g., GAD‑7) | non‑null |
| `measurement_timepoint` | string | Timepoint of measurement (`pre`, `post`, `trait`) | non‑null |
| `proxy_flag` | boolean | True if `anxiety_score` is a proxy for anticipatory anxiety (FR‑008) | non‑null |
| `coupling_risk` | boolean | True if baseline and outcome anxiety may be mathematically coupled | non‑null |
| `proxy_validated` | boolean | True if the proxy anxiety instrument is on the validated whitelist | non‑null |
| `missingness_indicator_<var>` | boolean \| null | Indicator for non‑MCAR missingness for each predictor (added when MCAR test fails) | optional |
| `vif_score` | number \| null | VIF for the variable after model fit (added for diagnostics) | optional |

### VariableMetadata (metadata for anxiety measures)

| Field | Type | Description |
|-------|------|-------------|
| `variable_name` | string | Name of the variable (e.g., `anxiety_score`, `baseline_anxiety`) |
| `instrument_identifier` | string | Identifier of the measurement instrument (e.g., `STAI‑Y`) |
| `measurement_timepoint` | string | Timepoint of measurement (`pre`, `post`, `trait`) |

### RegressionResult (analysis output – always a single JSON file)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"OLS"` |
| `data_status` | string | `"OK"` when a verified dataset passed schema validation; `"HALTED_NO_VALID_DATASET"` when ingestion halted (FR‑001 edge case). |
| `n_samples` | integer | Rows used after listwise deletion or imputation (present only when `data_status = "OK"`). |
| `r_squared` | number | Model R² (present only when `data_status = "OK"`). |
| `adj_r_squared` | number | Adjusted R² (present only when `data_status = "OK"`). |
| `f_statistic` | number | Overall F‑statistic (present only when `data_status = "OK"`). |
| `f_pvalue` | number | P‑value for the overall F‑test (present only when `data_status = "OK"`). |
| `coefficients` | object | Mapping *variable → coefficient* (real estimates only). |
| `std_errors` | object | Mapping *variable → standard error*. |
| `p_values` | object | Mapping *variable → p‑value*. |
| `vif_scores` | object | Mapping *variable → VIF* (added after model fit). |
| `assumption_checks` | object | `{linearity, homoscedasticity, normality, shapiro_wilk_p_value}` (PASS/FAIL/WARNING). |
| `robustness_result` | object \| null | If robustness runs: `{subset_n, coefficient, p_value, status, bootstrap}`; otherwise null. |
| `flags` | array[string] | Warnings such as `"Low Power"`, `"Proxy Used (unvalidated)"`, `"Proxy Used (validated)"`, `"High VIF"`, `"Robustness Skipped (r <= 0.3)"`, `"Associational Only"`. |
| `runtime` | number | Execution time in seconds (SC‑005). |
| `halt_report` | object \| null | Present only when `data_status = "HALTED_NO_VALID_DATASET"`; records sources checked, checksums, real column inventories, and missing variables. |
| `proxy_validated` | boolean | Mirrors dataset‑level `proxy_validated` flag when a proxy is used. |
| `associational_only` | boolean | Always `true` for observational data. |

### HaltReport (nested inside `RegressionResult` when ingestion fails)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"HALTED_NO_VALID_DATASET"` |
| `sources_checked` | array[object] | Each entry: `{url, cryptographic hash, row_count}` for the three verified parquet files. |
| `columns_found` | object | Mapping *url → list of column names* actually present. |
| `missing_variables` | array[string] | Required variables absent from **all** sources. |
| `reason` | string | Human‑readable statement of the mismatch (FR‑001 edge case). |

## Data Flow
1. **Ingestion** (`code/ingest.py`): download verified parquet files → `data/raw/`; compute SHA‑256; validate schema against `contracts/dataset.schema.yaml`.  
2. **If validation fails** (current reality): create `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"` and embed a complete `halt_report`; pipeline stops.  
3. **If validation succeeds** (future scenario): clean data → `SurveyResponse` entities (in‑memory); perform missingness assessment, factor‑analysis proxy validation, VIF‑based collinearity check; fit OLS; produce results.  
4. **Modeling** (`code/model.py`): OLS fit, diagnostics, correlation, robustness (high‑engagement, alternative covariates, robust regression) → populate `RegressionResult`.  
5. **Visualization** (`code/viz.py`): generate `output/plots/scatter_news_anxiety.png`.  
6. **Success‑criteria validation** (`code/validate_sc.py`): read the JSON, write `outputs/success_criteria_log.txt`.  
7. **Documentation** (`code/generate_readme.py`) and **archiving** (`code/archive.py`) run after validation.  

## Assumptions & Constraints
- No imputation is performed unless MCAR fails; in that case, `IterativeImputer` is the primary analysis (see plan).  
- Gender is one‑hot encoded for OLS; continuous predictors remain on original scale.  
- `baseline_anxiety` is retained; high VIF triggers a warning but does not force removal.  
- Robustness includes three complementary strategies (high‑engagement, alternative covariates, robust regression).  
- All numeric computations use double precision on CPU; no GPU required.  

---

