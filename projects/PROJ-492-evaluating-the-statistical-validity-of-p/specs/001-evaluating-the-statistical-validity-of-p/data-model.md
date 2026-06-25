# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries  

## Core Entities

### 1. `ABSummary`
| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Original URL of the public A/B test summary (must be a reachable HTTP/HTTPS address). |
| `source_domain` | string | Domain extracted from `url` (e.g., `blog.example.com`). |
| `retrieved_at` | datetime (ISO‑8601) | Timestamp of the download attempt. |
| `outcome_type` | enum {`binary`, `continuous`} | Determined from the metric description. |
| `variant_a_n` | integer | Reported sample size for variant A (must be ≥ 0). |
| `variant_b_n` | integer | Reported sample size for variant B (must be ≥ 0). |
| `effect_size` | float | Reported effect size **after conversion to absolute difference** (absolute difference for binary, mean diff for continuous). |
| `reported_p` | float \| null | Reported two‑sided p‑value, if present. |
| `p_upper_bound` | float \| null | Upper bound when p is reported as an inequality (`p < 0.001`). |
| `confidence_interval` | object \| null | `{ "lower": float, "upper": float }` when CI is provided. |
| `timestamp` | datetime \| null | Publication date extracted from the page (optional, used for temporal analyses). |
| `raw_html_path` | string | Path to the downloaded HTML file (under `data/raw/`). |
| `checksum_sha256` | string | SHA‑256 checksum of the raw HTML file. |
| `metric_type` *(optional)* | string \| null | Detected unit of the reported effect size (e.g., `lift_percent`, `odds_ratio`, `relative_risk`, `mean_difference`). Used for conversion; null if already absolute. |

### 2. `AuditRecord`
| Field | Type | Description |
|-------|------|-------------|
| `summary_url` | string | Foreign key to `ABSummary.url`. |
| `reconstructed_p` | float | P‑value computed from the reconstructed statistical test. |
| `reconstructed_effect_size` | float | Effect size computed from raw counts/means. |
| `reconstructed_variant_a_n` | integer | Sample size derived (may differ from reported). |
| `reconstructed_variant_b_n` | integer | Same as above for variant B. |
| `diff_abs_p` | float | `|reported_p - reconstructed_p|` (or bound diff if inequality). |
| `diff_rel_effect` | float | Relative difference of effect sizes (`abs(reported - reconstructed) / max(|reported|, |reconstructed|)`). |
| `diff_rel_n` | float | Relative difference of sample sizes (as above). |
| `flag_inconsistent` | boolean | True if any FR‑004 rule is triggered. |
| `category` | enum {`p_value`, `effect_size`, `sample_size`, `ci_mismatch`, `missing_metric`, `size_mismatch`} | Primary reason for inconsistency. |
| `notes` | string | Free‑form notes explaining the flag. |
| `audit_timestamp` | datetime (ISO‑8601) | When the audit was performed. |

### 3. `SyntheticValidationEntry`
| Field | Type | Description |
|-------|------|-------------|
| `outcome_type` | enum {`binary`, `continuous`} | As above. |
| `variant_a_n` | integer | Ground‑truth sample size for A. |
| `variant_b_n` | integer | Ground‑truth sample size for B. |
| `true_effect_size` | float | Ground‑truth effect size used to generate data. |
| `true_p` | float | Ground‑truth p‑value from the analytical test. |
| `reported_p` | float \| string | Simulated reported p‑value (may include rounding or inequality). |
| `reported_effect_size` | float | Simulated reported effect size (may include rounding error or be in a different unit). |
| `reported_variant_a_n` | integer \| null | May intentionally deviate to test size‑mismatch detection. |
| `reported_variant_b_n` | integer \| null | Same as above. |
| `confidence_interval` | object \| null | Simulated CI (optional). |
| `inconsistent` | boolean | Ground‑truth label for evaluation. |

## File Layout
- `data/raw_urls.csv` – Input list of URLs (user supplied).  
- `data/raw/<sha256>.html` – Downloaded HTML files.  
- `data/extracted_summaries.csv` – Flattened `ABSummary` rows (validated against `extracted_summary.schema.yaml`).  
- `data/audit_report.json` – Array of `AuditRecord`.  
- `data/synthetic_validation.csv` – Synthetic ground‑truth set.  
- `outputs/dashboard.html` – HTML dashboard.  
- `outputs/manifest.json` – SHA‑256 hashes for **all** output artifacts (supports Principle V).  

All CSV files use UTF‑8, comma delimiter, header row. JSON is UTF‑8, pretty‑printed.

---

