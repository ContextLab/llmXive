# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview
The data model defines two core entities—`ABSummary` (extracted raw metrics) and `AuditRecord` (audit outcome). A supplemental `Manifest` records artefact hashes for reproducibility.

## Entity Definitions

### 1. ABSummary
Represents the information extracted from a single public A/B test summary.

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Original URL of the summary (must be a valid HTTP/HTTPS URL). |
| `domain` | string | Top‑level domain extracted from `url` (e.g., `example.com`). |
| `year` | integer | Publication year inferred from URL or metadata; `null` if unavailable. |
| `outcome_type` | enum[`binary`, `continuous`] | Type of metric reported. |
| `variant_a_n` | integer | Sample size for variant A (must be ≥ 1). |
| `variant_b_n` | integer | Sample size for variant B (must be ≥ 1). |
| `variant_a_rate` | number | Conversion rate or mean for variant A (if binary, between 0‑1). |
| `variant_b_rate` | number | Conversion rate or mean for variant B. |
| `reported_effect_size` | number | Reported absolute difference (or lift % converted to absolute). |
| `reported_p` | number \| null | Reported two‑sided p‑value (0 ≤ p ≤ 1) or `null` if only CI given. |
| `reported_ci_lower` | number \| null | Lower bound of reported confidence interval (optional). |
| `reported_ci_upper` | number \| null | Upper bound of reported confidence interval (optional). |
| `timestamp` | string (ISO‑8601) | Date‑time when the summary was published (if available). |

Schema file: `contracts/extracted_summary.schema.yaml`.

### 2. AuditRecord
Result of the consistency check for one `ABSummary`.

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Mirrors `ABSummary.url`. |
| `reported_p` | number \| null | Copied from extraction. |
| `reported_effect_size` | number | Copied from extraction. |
| `reported_sample_size_a` | integer | Copied from extraction. |
| `reported_sample_size_b` | integer | Copied from extraction. |
| `reconstructed_p` | number | p‑value computed by the pipeline. |
| `reconstructed_effect_size` | number | Effect size computed from raw counts/means. |
| `diff_abs_p` | number | `|reported_p - reconstructed_p|`. |
| `diff_abs_effect` | number | Absolute difference in effect size. |
| `flag_inconsistent` | boolean | `true` if any FR‑004 condition triggered. |
| `category` | enum[`inconsistent`, `size_mismatch`, `missing_metric`, `consistent`] | High‑level classification. |
| `notes` | string | Human‑readable explanation (≤ 200 chars). |

Schema file: `contracts/audit_record.schema.yaml`.

### 3. Manifest
Tracks hashes of all generated artefacts for reproducibility (Principle V).

| Field | Type | Description |
|-------|------|-------------|
| `artifact_path` | string | Relative path to file under `output/`. |
| `sha256` | string | Hex‑encoded SHA‑256 checksum. |
| `generated_at` | string (ISO‑8601) | Timestamp of creation. |

Schema file: `contracts/manifest.schema.yaml`.

## Relationships
- Each `AuditRecord` **must** have a corresponding `ABSummary` (one‑to‑one).  
- `Manifest` entries are created for `audit_report.json`, `summary_report.csv`, `bias_report.json`, `subgroup_report.json`, and `checksums.txt`.

## Validation Strategy
- Contract tests (pytest) load each JSON/CSV line and validate against the appropriate schema using `jsonschema`.  
- Checksums are recomputed and compared to `manifest.json` entries.  
- Any schema violation aborts the CI job (fulfills **SC‑013**).

---
