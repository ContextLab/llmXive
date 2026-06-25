# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Entity: ABSummary

Represents a single publicly posted A/B test experiment extracted from a summary.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | YES | Original URL of the A/B test summary (provenance metadata). |
| `outcome_type` | string | YES | "binary" or "continuous" (determines statistical test). |
| `variant_a_n` | integer | YES | Sample size for variant A. |
| `variant_b_n` | integer | YES | Sample size for variant B. |
| `variant_a_conversions` | integer | NO | Conversion count for variant A (binary outcomes only). |
| `variant_b_conversions` | integer | NO | Conversion count for variant B (binary outcomes only). |
| `variant_a_mean` | float | NO | Mean value for variant A (continuous outcomes only). |
| `variant_b_mean` | float | NO | Mean value for variant B (continuous outcomes only). |
| `variant_a_std` | float | NO | Standard deviation for variant A (continuous outcomes only). |
| `variant_b_std` | float | NO | Standard deviation for variant B (continuous outcomes only). |
| `reported_effect_size` | float | YES | Reported effect size (absolute difference, lift %, or mean difference). |
| `reported_p` | float | NO | Reported p-value (numeric) or bound (for inequality p-values). |
| `reported_ci_lower` | float | NO | Lower bound of reported confidence interval. |
| `reported_ci_upper` | float | NO | Upper bound of reported confidence interval. |
| `publication_year` | integer | NO | Year of publication (for subgroup analysis). |
| `domain` | string | NO | Source domain (e.g., "optimizely.com", "airbnb.io") for bias assessment. |
| `extraction_timestamp` | string | YES | ISO 8601 timestamp of extraction. |
| `extraction_status` | string | YES | "success", "partial", or "failed". |
| `notes` | string | NO | Extraction notes (e.g., "baseline rate missing, used average"). |

## Entity: AuditRecord

Represents the result of the consistency check for one A/B summary.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | YES | Original URL of the A/B test summary. |
| `reported_p` | float | NO | Reported p-value (may be null for inequality). |
| `reported_effect_size` | float | YES | Reported effect size. |
| `reported_sample_size_a` | integer | YES | Reported sample size for variant A. |
| `reported_sample_size_b` | integer | YES | Reported sample size for variant B. |
| `reconstructed_p` | float | NO | Reconstructed p-value from statistical test. |
| `reconstructed_effect_size` | float | NO | Reconstructed effect size from sample data. |
| `diff_abs_p` | float | NO | Absolute difference between reported and reconstructed p-value. |
| `diff_abs_effect` | float | NO | Absolute relative difference between reported and reconstructed effect size. |
| `flag_inconsistent` | boolean | YES | True if any inconsistency condition met. |
| `inconsistency_reasons` | list[string] | NO | List of reasons (e.g., "p-value diff >0.05", "sample size mismatch"). |
| `notes` | string | NO | Additional audit notes (e.g., "missing baseline, used average"). |

## Entity: Manifest

Represents the pipeline execution metadata for reproducibility.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | YES | Unique identifier for this pipeline run (UUID). |
| `start_time` | string | YES | ISO 8601 timestamp of pipeline start. |
| `end_time` | string | YES | ISO 8601 timestamp of pipeline completion. |
| `status` | string | YES | "success", "partial", or "failed". |
| `input_url_count` | integer | YES | Number of URLs processed. |
| `extraction_success_count` | integer | YES | Number of successful extractions. |
| `extraction_error_count` | integer | YES | Number of extraction failures. |
| `inconsistent_count` | integer | YES | Number of inconsistent summaries. |
| `consistent_count` | integer | YES | Number of consistent summaries. |
| `output_files` | list[object] | YES | List of output files with checksums. |
| `resource_usage` | object | YES | CPU time, memory peak, disk usage. |
| `random_seeds` | object | NO | Random seeds used for reproducibility. |
| `dependencies` | object | YES | Python package versions (from requirements.txt). |
