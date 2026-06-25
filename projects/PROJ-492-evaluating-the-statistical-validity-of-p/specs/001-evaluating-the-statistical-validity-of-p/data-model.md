# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries  

## Overview
The data model formalises the entities exchanged between pipeline stages, the schemas used for validation, and the artefacts persisted for reproducibility.

## Entities

### 1. `ABSummary` (extracted summary)
| Field | Type | Description |
|-------|------|-------------|
| `url` | `string` | Original URL of the public A/B test summary. |
| `variant_a_n` | `integer` | Sample size for variant A (may be `null` if missing). |
| `variant_b_n` | `integer` | Sample size for variant B (may be `null` if missing). |
| `effect_size` | `number` | Reported effect size (absolute conversion‑rate difference, lift % or mean difference). |
| `effect_size_unit` | `string` | One of `"abs_diff"`, `"lift_percent"`, `"mean_diff"`, `"odds_ratio"`, `"relative_risk"`. |
| `reported_p` | `string` | Reported p‑value (e.g., `"0.032"` or `"p<0.001"`). |
| `confidence_interval` | `object` | `{ "lower": number, "upper": number }` or `null`. |
| `timestamp` | `string` (ISO‑8601) | Publication date of the summary (if available). |
| `outcome_type` | `string` | `"binary"` or `"continuous"`. |
| `baseline_rate` | `number` | Baseline conversion rate for lift conversion (optional). |
| `source` | `string` | Extracted host or organization name (e.g., `"example.com"`). |
| `retrieval_ts` | `string` (ISO‑8601) | Time when the page was fetched. |
| **`experiment_hash`** | `string` | SHA‑256 hash of the numeric payload (`variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`) used for duplicate‑experiment detection. |

### 2. `AuditRecord`
| Field | Type | Description |
|-------|------|-------------|
| `url` | `string` | Mirrors `ABSummary.url`. |
| `reconstructed_p` | `number` | P‑value recomputed from raw numbers. |
| `diff_abs_p` | `number` | `|reported_p_numeric - reconstructed_p|`. |
| `reconstructed_effect_size` | `number` | Effect size recomputed (absolute difference). |
| `diff_abs_effect` | `number` | Relative absolute difference between reported and reconstructed effect size. |
| `reconstructed_n_a` | `integer` | Sample size for variant A used in reconstruction (may differ from reported). |
| `reconstructed_n_b` | `integer` | Same as above for variant B. |
| `diff_abs_n` | `number` | Relative absolute difference in sample size. |
| `flag_inconsistent` | `boolean` | True if any FR‑004 sub‑criterion is violated. |
| `category` | `string` | One of `"p_value_mismatch"`, `"effect_size_mismatch"`, `"sample_size_mismatch"`, `"ci_violation"`, `"missing_metric"`. |
| `notes` | `string` | Human‑readable explanation of the flag. |

### 3. `SyntheticValidationEntry` (generated for FR‑008/FR‑013)
Same fields as `ABSummary`, plus a Boolean `ground_truth_inconsistent` used for precision/recall calculations.

### 4. `Manifest`
| Field | Type | Description |
|-------|------|-------------|
| `docker_image_sha256` | `string` | SHA‑256 hash of the built Docker image. |
| `audit_json_md5` | `string` | MD5 checksum of `outputs/audit.json`. |
| `dashboard_html_md5` | `string` | MD5 checksum of `outputs/dashboard.html`. |
| `generated_at` | `string` (ISO‑8601) | Timestamp of manifest creation. |

## Schema Files
- `contracts/extracted_summary.schema.yaml` – validates `ABSummary`.  
- `contracts/audit_record.schema.yaml` – validates `AuditRecord`.  

Both schemas are referenced in **FR‑015** and exercised by the pytest contract suite (**FR‑016**).

---


