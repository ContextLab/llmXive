# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview

This document defines the data structures used throughout the audit pipeline, including input schemas, intermediate representations, and output formats. All models conform to the inline schema definitions in the feature specification (FR-002).

## Core Entities

### ABSummary

Represents a single publicly posted A/B test experiment with extracted statistics.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `url` | string | Yes | Valid URL format | Source URL of the summary |
| `variant_a_n` | integer | Yes | ≥1 | Sample size for variant A |
| `variant_b_n` | integer | Yes | ≥1 | Sample size for variant B |
| `variant_a_conversions` | integer | Yes | ≥0 | Conversion count for variant A (binary outcomes only) |
| `variant_b_conversions` | integer | Yes | ≥0 | Conversion count for variant B (binary outcomes only) |
| `variant_a_mean` | float | No | N/A | Mean for variant A (continuous outcomes only) |
| `variant_b_mean` | float | No | N/A | Mean for variant B (continuous outcomes only) |
| `variant_a_std` | float | No | N/A | Standard deviation for variant A (continuous outcomes only) |
| `variant_b_std` | float | No | N/A | Standard deviation for variant B (continuous outcomes only) |
| `reported_p` | float | Yes | 0 < p ≤ 1, or null for inequality bounds | Reported p-value |
| `reported_effect_size` | float | Yes | Can be negative | Reported effect size (conversion difference, lift %, or mean difference) |
| `outcome_type` | string | Yes | One of: `binary`, `continuous` | Type of outcome metric |
| `confidence_interval` | object | No | `{lower: float, upper: float}` | Optional confidence interval |

**Inline Schema Definition (FR-002)**:
```
ABSummary:
 url: string (required, valid URL)
 variant_a_n: integer (required, ≥1)
 variant_b_n: integer (required, ≥1)
 variant_a_conversions: integer (required, ≥0)
 variant_b_conversions: integer (required, ≥0)
 variant_a_mean: float (optional, continuous outcomes only)
 variant_b_mean: float (optional, continuous outcomes only)
 variant_a_std: float (optional, continuous outcomes only)
 variant_b_std: float (optional, continuous outcomes only)
 reported_p: float (required, 0 < p ≤ 1, or null for inequality bounds)
 reported_effect_size: float (required, can be negative)
 outcome_type: string (required, one of: binary, continuous)
 confidence_interval: object (optional, {lower: float, upper: float})
```

### AuditRecord

Represents the result of the consistency check for one ABSummary.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `url` | string | Yes | Valid URL format | Source URL (reference to ABSummary) |
| `reported_p` | float | Yes | 0 < p ≤ 1, or null | Reported p-value from ABSummary |
| `reported_effect_size` | float | Yes | Any float | Reported effect size from ABSummary |
| `reported_sample_size_a` | integer | Yes | ≥1 | Variant A sample size from ABSummary |
| `reported_sample_size_b` | integer | Yes | ≥1 | Variant B sample size from ABSummary |
| `reconstructed_p` | float | Yes | 0 < p ≤ 1 | Reconstructed p-value from statistical test |
| `reconstructed_effect_size` | float | Yes | Any float | Reconstructed effect size |
| `diff_abs_p` | float | Yes | ≥0 | Absolute difference between reported and reconstructed p-values |
| `diff_abs_effect` | float | Yes | ≥0 | Absolute relative difference in effect size (% of larger magnitude) |
| `flag_inconsistent` | boolean | Yes | True/False | Whether summary is flagged as inconsistent |
| `flag_size_mismatch` | boolean | Yes | True/False | True if sample size discrepancy >5% (FR-004b) |
| `flag_missing_metric` | boolean | Yes | True/False | True if required metric missing |
| `flag_unverifiable` | boolean | Yes | True/False | True if source lacks sufficient raw data for independent ground truth verification (FR-031b) |
| `notes` | string | Yes | ≤200 characters | Explanatory notes (e.g., "missing metric", "size mismatch", "heuristic baseline") |

## Input Data Models

### URL Input File

**Format**: CSV
**Location**: `data/raw/urls.csv`
**Schema**:
```csv
url


...
```

### Synthetic Validation Dataset

**Format**: CSV + JSON
**Location**: `data/processed/synthetic_validation.csv`, `data/processed/synthetic_ground_truth.json`
**Schema**:
```csv
url,outcome_type,variant_a_n,variant_b_n,variant_a_conversions,variant_b_conversions,reported_p,reported_effect_size,ground_truth_inconsistent
synthetic-001,binary,1000,1000,150,180,0.042,0.03,False
synthetic-002,continuous,500,500,0,0,0.003,0.15,True
...
```

### Real-World Validation Labels

**Format**: CSV
**Location**: `data/processed/real_world_validation_labels.csv`
**Schema**:
```csv
url,ground_truth_inconsistent,annotator_1,annotator_2,annotator_3,resolution_notes
 on inconsistency due to p-value mismatch
...
```

## Output Data Models

### Audit Report (JSON)

**Format**: JSON
**Location**: `data/output/audit_report.json`
**Schema**: Array of `AuditRecord` objects

```json
[
 {
 "url": "",
 "reported_p": 0.042,
 "reported_effect_size": 0.03,
 "reported_sample_size_a": 1000,
 "reported_sample_size_b": 1000,
 "reconstructed_p": 0.038,
 "reconstructed_effect_size": 0.03,
 "diff_abs_p": 0.004,
 "diff_abs_effect": 0.0,
 "flag_inconsistent": false,
 "flag_size_mismatch": false,
 "flag_missing_metric": false,
 "flag_unverifiable": false,
 "notes": "Consistent"
 },
...
]
```

### Summary Report (CSV)

**Format**: CSV
**Location**: `data/output/summary_report.csv`
**Schema**:

| Column | Type | Description |
|--------|------|-------------|
| `total_summaries` | integer | Total number of summaries audited |
| `inconsistent_count` | integer | Number of inconsistent summaries |
| `inconsistent_rate` | float | Raw inconsistency rate (inconsistent_count / total_summaries) |
| `bias_adjusted_rate` | float | Domain-weighted bias-adjusted rate |
| `wilson_ci_lower` | float | Lower bound of 95% Wilson confidence interval |
| `wilson_ci_upper` | float | Upper bound of 95% Wilson confidence interval |

### Bias Report (JSON)

**Format**: JSON
**Location**: `data/output/bias_report.json`
**Schema**:

```json
{
 "domain_proportions": {
 "tech": 0.25,
 "e-commerce": 0.30,
 "finance": 0.20,
 "healthcare": 0.15,
 "saas": 0.10
 },
 "raw_inconsistency_rate": 0.12,
 "bias_adjusted_rate": 0.11,
 "max_domain_proportion": 0.30,
 "dominance_warning": false
}
```

### Subgroup Report (JSON)

**Format**: JSON
**Location**: `data/output/subgroup_report.json`
**Schema**:

```json
{
 "subgroups": [
 {
 "domain": "tech",
 "sample_size": 75,
 "inconsistent_count": 10,
 "prevalence": 0.133,
 "fisher_p_value": 0.42,
 "bonferroni_adjusted_alpha": 0.006,
 "statistically_different": false
 },
...
 ]
}
```

### Manifest (JSON)

**Format**: JSON
**Location**: `data/output/manifest.json`
**Schema**:

```json
{
 "pipeline_version": "1.0.0",
 "execution_timestamp": "2026-06-24T12:00:00Z",
 "total_summaries_processed": 300,
 "parsing_error_count": 5,
 "parsing_error_rate": 0.017,
 "checksums": {
 "audit_report.json": "sha256:abc123...",
 "summary_report.csv": "sha256:def456...",
...
 },
 "resource_usage": {
 "cpu_time_seconds": 7200,
 "peak_memory_mb": 1500
 }
}
```

## Validation Rules

### ABSummary Validation

1. `url` must be a valid URL (validated via `urllib.parse.urlparse`)
2. `variant_a_n`, `variant_b_n` must be integers ≥1
3. `variant_a_conversions`, `variant_b_conversions` must be integers ≥0 (binary outcomes only)
4. `variant_a_mean`, `variant_b_mean` must be floats (continuous outcomes only)
5. `variant_a_std`, `variant_b_std` must be floats (continuous outcomes only)
6. `reported_p` must be 0 < p ≤ 1, or null for inequality bounds
7. `outcome_type` must be one of: `binary`, `continuous`
8. If `confidence_interval` is present, `lower` and `upper` must be floats

### AuditRecord Validation

1. `diff_abs_p` must equal `abs(reported_p - reconstructed_p)` (or handle null reported_p)
2. `diff_abs_effect` must equal relative difference (% of larger magnitude)
3. `flag_inconsistent` is True if `diff_abs_p > 0.05` OR `diff_abs_effect > 0.05`
4. `flag_size_mismatch` is True if sample size discrepancy >5%
5. `flag_missing_metric` is True if required metric absent
6. `flag_unverifiable` is True if source lacks sufficient raw data
7. `notes` must be ≤200 characters

### Output Consistency

1. `summary_report.csv` values must exactly match computed values in `audit_report.json` (SC-024)
2. `manifest.json` checksums must match actual file checksums (T076, T077)
3. Parsing error rate must be ≤5% of total summaries (SC-005)

## Error Handling

### Parsing Errors (FR-007)

All parsing failures must be logged with:
- Error code of form `ERR-###`
- Affected field name
- Concise description ≤200 characters

**Example**:
```
ERR-001: Missing field 'variant_a_n' in summary at
ERR-002: Malformed HTML in summary at
ERR-003: Dead URL (HTTP 404) in summary at
```

### Warning Conditions

- `data_quality_warning`: Sample sizes differ by >5% (FR-004b)
- `heuristic_baseline`: Baseline conversion rate missing, using average of variants (FR-012)
- `missing_metric`: Required metric absent (e.g., effect size without p-value)