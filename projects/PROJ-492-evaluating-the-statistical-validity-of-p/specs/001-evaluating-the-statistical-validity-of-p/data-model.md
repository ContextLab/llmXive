# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview
The audit pipeline works with two core entities:

1. **`ABSummary`** – the extracted representation of a single public A/B test summary.  
2. **`AuditRecord`** – the result of the consistency check for an `ABSummary`.

Both entities are serialized as JSON objects and validated against the schemas in `contracts/`.

## Entity Definitions

### ABSummary
| Field | Type | Description |
|-------|------|-------------|
| `url` | `string` | Original URL of the public summary (required). |
| `retrieved_at` | `string` (ISO‑8601 datetime) | Timestamp when the HTML page was downloaded. |
| `variant_a_n` | `integer` | Sample size for Variant A. |
| `variant_b_n` | `integer` | Sample size for Variant B. |
| `variant_a_rate` | `number` | Conversion rate or mean for Variant A (0 – 1 for binary). |
| `variant_b_rate` | `number` | Conversion rate or mean for Variant B. |
| `effect_size` | `number` | Reported absolute difference (or lift % converted to absolute). |
| `effect_size_unit` | `string` (enum: `["abs_diff","lift_percent","mean_diff","odds_ratio"]`) | Unit of the reported effect size. |
| `reported_p` | `string` | Reported p‑value (e.g., `"0.032"` or `"p<0.001"`). |
| `confidence_interval` | `object` (optional) | `{ "lower": number, "upper": number }` – 95 % CI if reported. |
| `outcome_type` | `string` (enum: `["binary","continuous"]`) | Nature of the outcome metric. |
| `source` | `string` (optional) | Human‑readable source name (e.g., “Company Blog”). |
| `timestamp` | `string` (ISO‑8601 datetime, optional) | Publication date of the summary, if available. |

The schema file is `contracts/extracted_summary.schema.yaml`.

### AuditRecord
| Field | Type | Description |
|-------|------|-------------|
| `summary_url` | `string` | Mirrors `ABSummary.url`. |
| `reconstructed_p` | `number` | Two‑proportion or Welch‑t p‑value computed by the pipeline. |
| `reconstructed_effect_size` | `number` | Effect size derived from raw counts/rates. |
| `diff_abs_p` | `number` | Absolute difference `|reported_p - reconstructed_p|`. |
| `diff_abs_effect` | `number` | Absolute relative difference between reported and reconstructed effect size. |
| `diff_abs_n` | `number` | Absolute relative difference between reported and reconstructed sample sizes (max of the two variants). |
| `flag_inconsistent` | `boolean` | `true` if any FR‑004 rule triggers. |
| `category` | `string` (enum: `["p_value","effect_size","sample_size","ci_mismatch","missing_metric","size_mismatch","parsing_failure"]`) | Primary reason for inconsistency. |
| `notes` | `string` (optional) | Human‑readable explanation or error message. |
| `hash` | `string` | SHA‑256 hash of the normalized payload (used for deduplication, FR‑017). |
| `processed_at` | `string` (ISO‑8601 datetime) | Timestamp of audit processing. |

The schema file is `contracts/audit_record.schema.yaml`.

## Relationships
- Each `AuditRecord` corresponds one‑to‑one with an `ABSummary`.  
- After deduplication (FR‑017), only unique `ABSummary`s generate `AuditRecord`s.  
- The final JSON audit report (`output/audit_report.json`) is an array of `AuditRecord`s.

---
