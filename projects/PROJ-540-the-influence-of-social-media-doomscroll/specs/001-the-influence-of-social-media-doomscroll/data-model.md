# Data Model: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Entity Definitions

### SurveyResponse (cleaned row — populated only if a verified dataset passes schema validation)

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| `participant_id` | string | Anonymized unique identifier | non-null, unique |
| `news_exposure_freq` | number | Frequency of negative news consumption | non-null, ≥ 0 |
| `anxiety_score` | number | Outcome anxiety score | non-null, ≥ 0 |
| `baseline_anxiety` | number | Baseline/trait anxiety | nullable, ≥ 0 |
| `age` | integer | Age in years | non-null, 18–100 |
| `gender` | string | Gender category | categorical |
| `social_media_engagement` | number | Overall social-media use | nullable, ≥ 0 |
| `instrument_source` | string | Anxiety instrument name | non-null |
| `measurement_timepoint` | string | "pre"/"post"/"trait" | non-null |
| `proxy_flag` | boolean | Proxy outcome used (FR-008) | non-null |
| `coupling_risk` | boolean | Baseline/outcome coupling risk | non-null |

### RegressionResult (analysis output — real values only; never placeholder/hard-coded)

Single SSoT file: `output/results/regression_results.json`. This file is produced in BOTH outcomes; when no dataset validates, it carries `data_status = "HALTED_NO_VALID_DATASET"` with the nested `halt_report` below (no standalone halt file exists).

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"OLS"` |
| `n_samples` | integer | Rows used after cleaning |
| `r_squared`, `adj_r_squared` | number | Model fit |
| `f_statistic`, `f_pvalue` | number | Overall F-test |
| `coefficients`, `std_errors`, `p_values` | object | Per-variable maps |
| `vif_scores` | object | Per-variable VIF |
| `assumption_checks` | object | Linearity/homoscedasticity/normality verdicts + Shapiro-Wilk p |
| `robustness_result` | object/null | `{subset_n, coefficient, p_value, status}` or null if skipped |
| `flags` | array[string] | "Low Power", "Proxy Used", "High VIF", "Robustness Skipped (r ≤ 0.3)", "Associational Only" |
| `runtime` | number | Measured execution seconds (SC-005) |
| `data_status` | string | `"OK"` or `"HALTED_NO_VALID_DATASET"` — when no verified dataset passes schema validation, this field records the halt and all statistical fields are omitted (never filled with fabricated values) |
| `halt_report` | object/null | Nested HaltReport (see below); present only when `data_status = "HALTED_NO_VALID_DATASET"` |

### HaltReport (nested inside `regression_results.json`; produced when schema validation fails — the expected current outcome)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"HALTED_NO_VALID_DATASET"` |
| `sources_checked` | array | The verified URLs attempted, with SHA-256 and row counts |
| `columns_found` | object | Per-source actual column inventory (real measurement) |
| `missing_variables` | array | Required variables absent (e.g., all six) |
| `reason` | string | Explicit mismatch statement per FR-001 edge case |

## Data Flow
1. Raw download of verified parquets → `data/raw/` (immutable, checksummed).
2. Schema validation against `contracts/dataset.schema.yaml` → per-source column inventory.
3. **If validation fails (current expectation):** `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"` and nested `halt_report`; pipeline stops; no fabricated downstream artifacts.
4. **If validation passes (future verified dataset):** cleaned CSV → OLS → full `regression_results.json` → plots.

## Assumptions & Constraints
- No imputation; no synthetic stand-ins; missing data → listwise deletion or halt.
- Gender one-hot encoded for OLS; continuous predictors on original scale.
- `baseline_anxiety` dropped with `coupling_risk = true` if not distinct from outcome.
- Robustness check auto-skipped with a warning flag if `social_media_engagement` is absent or r ≤ 0.3.

---