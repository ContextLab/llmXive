# Data Model: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

## Entity Definitions

### ConversationSession

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| session_id | string | Unique session identifier | CBT dataset |
| user_id | string | User identifier (may be synthetic) | Synthetic (linked to demographics) |
| utterances | list[string] | Ordered list of utterance text | CBT dataset |
| agency_score | float | Computed agency score, normalized to [0, 1] | Derived |
| marker_counts | dict[string, int] | Count of each linguistic marker type detected | Derived |
| utterance_count | int | Total number of utterances in the session | Derived |
| processing_timestamp | string (ISO‑8601) | Timestamp when the agency score was computed | Derived (pipeline_logger) |

### UserEngagement

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| user_id | string | Unique user identifier | Synthetic (linked to demographics) |
| completion_rate | float | Proportion of sessions marked completed (0 ≤ ≤ 1) | Derived from usage metadata |
| avg_inter_session_days | float | Mean gap between consecutive sessions (days) | Derived |
| total_minutes | float | Sum of session durations (minutes) | Derived |
| self_reported_engagement | float | Average Likert‑scale score (0 ≤ ≤ 5) | Derived (survey) |
| sessions_per_week | float | Total sessions divided by observation weeks | Derived |
| observation_weeks | float | `(last_session_date - first_session_date + 1) / 7` | Derived |
| time_gap_days | float | Days between last session and self‑report (≥ 7 enforced) | Derived; used as covariate if < 7 |

### Demographics

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| user_id | string | Unique user identifier | Synthetic or real |
| age | int | Age in years | External dataset (required) |
| gender | string | Gender category | External dataset (required) |
| baseline_symptom_severity | float | Pre‑treatment symptom score | External dataset (required) |
| prior_therapy_exposure | int | Number of prior therapy sessions | External dataset (required) |

### RegressionResult

| Attribute | Type | Description |
|-----------|------|-------------|
| dependent_metric | string | Name of the adherence outcome variable |
| beta_agency | float | Regression coefficient for `agency_score` |
| p_value | float | Two‑tailed p‑value |
| adjusted_p_value | float | Benjamini‑Hochberg FDR‑adjusted p‑value |
| ci_lower | float | 95 % confidence interval lower bound |
| ci_upper | float | 95 % confidence interval upper bound |
| r_squared | float | Model R² (or pseudo‑R² for logistic/beta) |

### ValidationReport

| Attribute | Type | Description |
|-----------|------|-------------|
| split_half_reliability | float | Spearman‑Brown reliability coefficient |
| convergent_validity_r | float | Pearson correlation with external agency scale |
| convergent_validity_p | float | Two‑tailed p‑value for the correlation |
| validation_passed | bool | True only if reliability ≥ 0.80 **and** r ≥ 0.30, p < 0.05 |
| report_path | string | Path to the PDF report (`validation/report.pdf`) |

## Data Flow Overview

```
CBT Parquet → ingest_transcripts.py → agency_scoring/
   ├─ compute_scores.py → data/derived/agency_scores.csv
   └─ marker_counts.csv (optional)

Usage metadata (real) → extract_metrics.py → data/derived/adherence_metrics.csv
Demographics (real) → impute_confounders.py → data/derived/demographics_imputed.csv

merge_datasets.py (agency + adherence + demographics) → data/derived/merged_data.csv

validation/
   ├─ compute_reliability.py (agency_scores.csv) → data/validated_features/reliability.yaml
   ├─ compute_convergent.py (requires external_scale.csv) → data/validated_features/convergent.yaml
   └─ report_generator.py → validation/report.pdf & data/validated_features/validation_report.yaml

analysis/
   ├─ run_regression.py (merged_data.csv) → data/derived/regression_results.csv
   └─ generate_plots.py → output/regression_plots.png

logging/
   └─ verify_logging.py → logs/completeness_metric.json
```

## File Formats

| File | Format | Purpose |
|------|--------|---------|
| `data/raw/cbt_*.parquet` | Parquet | Downloaded conversation transcripts (FR‑012) |
| `data/raw/usage_metadata.csv` | CSV | Real usage logs (required for final analysis) |
| `data/raw/demographics.csv` | CSV | Real demographic confounders (required) |
| `data/raw/external_agency_scale.csv` | CSV | External validated agency scale scores (required for validation) |
| `data/derived/agency_scores.csv` | CSV | Session‑level agency scores (FR‑003) |
| `data/derived/adherence_metrics.csv` | CSV | User‑level adherence metrics (FR‑004, FR‑013) |
| `data/derived/demographics_imputed.csv` | CSV | Imputed confounder dataset (FR‑010) |
| `data/derived/merged_data.csv` | CSV | Combined dataset for regression (FR‑005) |
| `data/derived/regression_results.csv` | CSV | Coefficients, p‑values, CIs, R² (FR‑006) |
| `data/validated_features/validation_report.yaml` | YAML | Psychometric validation results (FR‑009, Constitution VII) |
| `validation/report.pdf` | PDF | Human‑readable validation report |
| `logs/run_<timestamp>.log` | Text | Timestamped pipeline log (FR‑008) |
| `logs/completeness_metric.json` | JSON | Logging completeness metric (SC‑005) |
| `output/results_summary.csv` | CSV | Human‑readable summary of all key outcomes |
| `output/regression_plots.png` | PNG | Visualizations of regression fits |

## Constraints

| Constraint | Value | FR Reference |
|------------|-------|--------------|
| RAM limit | ≤ 6 GB | FR‑007 |
| CPU cores | ≤ 2 | FR‑007 |
| Disk | ≤ 14 GB | Compute feasibility |
| Runtime | ≤ 6 h total, regression ≤ 30 min | SC‑003 |
| Agency score range | [0, 1] | FR‑003 |
| Completion rate range | [0, 1] | FR‑004 |
| Self‑reported engagement range | [0, 5] | FR‑004 |
| `time_gap_days` ≥ 7 for valid self‑report | Enforced in extraction | FR‑011 |
