# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview

This document defines the data models used throughout the audit pipeline. All models conform to the schema contracts in `contracts/` and are validated via pytest contract tests.

## Core Entities

### 1. ABSummary (Extraction Output)

Represents a single audited A/B test summary with extracted metrics.

| Field | Type | Required | Constraints | FR Reference |
|-------|------|----------|-------------|--------------|
| url | string | Yes | Valid URL format | FR-002 |
| variant_a_n | integer | Yes | ≥1 | FR-002 |
| variant_b_n | integer | Yes | ≥1 | FR-002 |
| variant_a_conversions | integer | Yes | ≥0 | FR-002 |
| variant_b_conversions | integer | Yes | ≥0 | FR-002 |
| reported_p | float or null | Yes | 0 < p ≤ 1, or null for inequality bounds | FR-002 |
| reported_effect_size | float | Yes | Can be negative | FR-002 |
| outcome_type | string | Yes | One of: "binary", "continuous" | FR-002 |
| confidence_interval | object or null | No | {lower: float, upper: float} | FR-002 |
| source_domain | string | Yes | Extracted from URL hostname | FR-007, VII |
| publication_year | integer or null | No | Extracted from URL or page metadata | FR-032 |
| extraction_timestamp | string | Yes | ISO 8601 format | FR-007 |

**Schema Contract**: `contracts/abs_summary.schema.yaml`

### 2. AuditRecord (Inconsistency Detection Output)

Represents the audit result for a single summary.

| Field | Type | Required | Constraints | FR Reference |
|-------|------|----------|-------------|--------------|
| url | string | Yes | Valid URL format | FR-024 |
| reported_p | float or null | Yes | 0 < p ≤ 1, or null | FR-024 |
| reported_effect_size | float | Yes | Can be negative | FR-024 |
| reported_sample_size_a | integer | Yes | ≥1 | FR-024 |
| reported_sample_size_b | integer | Yes | ≥1 | FR-024 |
| reconstructed_p | float | Yes | 0 < p ≤ 1 | FR-024 |
| reconstructed_effect_size | float | Yes | Can be negative | FR-024 |
| diff_abs_p | float | Yes | Absolute difference | FR-024 |
| diff_abs_effect | float | Yes | Absolute difference | FR-024 |
| flag_inconsistent | boolean | Yes | True if any inconsistency criterion met | FR-024 |
| notes | string | Yes | ≤200 characters; includes error codes if applicable | FR-024, FR-007 |

**Schema Contract**: `contracts/audit_record.schema.yaml`

### 3. SummaryReport (Aggregate Output)

Represents the aggregated audit results.

| Field | Type | Required | Constraints | FR Reference |
|-------|------|----------|-------------|--------------|
| total_summaries | integer | Yes | ≥300 (per FR-025) | FR-024, SC-025 |
| inconsistent_count | integer | Yes | ≤total_summaries | FR-024 |
| inconsistent_rate | float | Yes | 0 ≤ rate ≤ 1 | FR-024 |
| bias_adjusted_rate | float | Yes | 0 ≤ rate ≤ 1 | FR-024, FR-027 |
| wilson_ci_lower | float | Yes | 0 ≤ value ≤ 1 | FR-024, SC-014 |
| wilson_ci_upper | float | Yes | 0 ≤ value ≤ 1 | FR-024, SC-014 |
| parsing_error_count | integer | Yes | ≤5% of total_summaries (SC-005) | FR-007 |
| bias_report_url | string | Yes | Path to bias_report.json | FR-027 |
| subgroup_report_url | string | Yes | Path to subgroup_report.json | FR-032 |
| generated_timestamp | string | Yes | ISO 8601 format | FR-024 |

**Schema Contract**: `contracts/summary_report.schema.yaml`

## Data Flow

```
input/urls.csv
 ↓ (FR-001)
code/extraction.py
 ↓ (FR-002)
data/processed/abs_summaries.csv (ABSummary records)
 ↓ (FR-003)
code/reconstruction.py
 ↓ (FR-004)
code/inconsistency.py
 ↓ (FR-004)
output/audit_report.json (AuditRecord array)
 ↓ (FR-005a, FR-027)
code/prevalence.py, code/bias.py
 ↓ (FR-005a, FR-027)
output/summary_report.csv (SummaryReport)
 ↓ (FR-032)
code/subgroup.py
 ↓ (FR-032)
output/subgroup_report.json (Subgroup analysis)
```

## Validation Rules

### ABSummary Validation
- `variant_a_n` and `variant_b_n` must be ≥1 (non-zero sample sizes).
- `variant_a_conversions` and `variant_b_conversions` must be ≥0 and ≤ variant_n respectively.
- `reported_p` must be in (0, 1] if not null.
- `outcome_type` must be "binary" or "continuous".

### AuditRecord Validation
- `diff_abs_p` = |reported_p - reconstructed_p| (if reported_p is not null).
- `flag_inconsistent` is True if:
 - `diff_abs_p` > 0.05 (absolute threshold per Constitution Principle VI), OR
 - For inequality p-values: reconstructed_p > bound, OR
 - `diff_abs_effect` > 5% of larger magnitude.
- `notes` must be ≤200 characters and include ERR-### codes if applicable.

### SummaryReport Validation
- `total_summaries` ≥300 (per FR-025 power analysis).
- `parsing_error_count` ≤5% of `total_summaries` (per SC-005).
- `wilson_ci_upper - wilson_ci_lower` ≤0.10 (per SC-014).

## File Formats

### JSON (audit_report.json)
```json
{
 "audit_records": [
 {
 "url": "",
 "reported_p": 0.03,
 "reported_effect_size": 0.05,
 "reported_sample_size_a": 1000,
 "reported_sample_size_b": 1000,
 "reconstructed_p": 0.032,
 "reconstructed_effect_size": 0.048,
 "diff_abs_p": 0.002,
 "diff_abs_effect": 0.002,
 "flag_inconsistent": false,
 "notes": "All metrics within tolerance"
 }
 ],
 "metadata": {
 "generated_timestamp": "2026-06-24T12:00:00Z",
 "pipeline_version": "1.0.0"
 }
}
```

### CSV (summary_report.csv)
```csv
total_summaries,inconsistent_count,inconsistent_rate,bias_adjusted_rate,wilson_ci_lower,wilson_ci_upper
300,45,0.15,0.14,0.11,0.19
```

### YAML (schema contracts)
See `contracts/*.schema.yaml` for full schema definitions.
