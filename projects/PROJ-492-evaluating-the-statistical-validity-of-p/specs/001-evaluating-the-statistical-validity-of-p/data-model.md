# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview
Two primary entities are required throughout the pipeline:

1. **ABSummary** – the extracted representation of a public A/B test summary.  
2. **AuditRecord** – the result of the consistency check for a single summary.

Both entities are defined by JSON schemas stored in `contracts/`. The schemas enable contract testing, automatic validation, and serve as the single source of truth for downstream analysis.

## 1. ABSummary (`extracted_summary.schema.yaml`)
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `url` | string | Original URL of the public summary (must be a valid HTTP/HTTPS URL). | Yes |
| `source_domain` | string | Domain name extracted from `url` (e.g., `example.com`). | Yes |
| `variant_a_n` | integer | Sample size for variant A (≥ 0). | Yes |
| `variant_b_n` | integer | Sample size for variant B (≥ 0). | Yes |
| `effect_size` | number | Reported effect size (absolute conversion difference or mean difference). | Yes |
| `reported_p` | string | Reported p‑value; may be a numeric string (`"0.043"`) or inequality (`"p<0.001"`). | Yes |
| `confidence_interval` | string \| null | Reported confidence interval (optional). | No |
| `outcome_type` | string | `"binary"` or `"continuous"` (validated against enum). | Yes |
| `timestamp` | string | ISO‑8601 timestamp of when the summary was published (optional). | No |

*Schema file*: `contracts/extracted_summary.schema.yaml`

## 2. AuditRecord (`audit_record.schema.yaml`)
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `url` | string | Mirrors the `url` from the corresponding `ABSummary`. | Yes |
| `reported_p` | number | Numeric representation of the reported p‑value (inequalities converted to bound). | Yes |
| `reported_effect_size` | number | Numeric reported effect size. | Yes |
| `reported_sample_size_a` | integer | Sample size for variant A (from extraction). | Yes |
| `reported_sample_size_b` | integer | Sample size for variant B. | Yes |
| `reconstructed_p` | number | P‑value computed from the reconstructed test. | Yes |
| `reconstructed_effect_size` | number | Effect size recomputed from raw numbers. | Yes |
| `diff_abs_p` | number | Absolute difference `|reported_p - reconstructed_p|`. | Yes |
| `diff_abs_effect` | number | Absolute difference in effect sizes. | Yes |
| `flag_inconsistent` | boolean | `true` if any FR‑004 condition holds. | Yes |
| `notes` | string | Human‑readable explanation or error code (e.g., `ERR-002: missing variant_b_n`). | Yes |

*Schema file*: `contracts/audit_record.schema.yaml`

## 3. Manifest (`manifest.schema.yaml`)
The manifest records hashes of all generated artifacts for reproducibility.

| Field | Type | Description |
|-------|------|-------------|
| `generated_at` | string | ISO‑8601 timestamp of manifest creation. |
| `artifacts` | mapping | Keys are relative file paths; values are SHA‑256 hashes. |
| `git_commit` | string | Full commit SHA of the code used for the run. |
| `random_seed` | integer | Seed value used for all stochastic components. |

*Schema file*: `contracts/manifest.schema.yaml`

All schemas are validated with `jsonschema` in the CI pipeline (see `tests/contract/`).

---
