# Data Model: Evaluating the Statistical Validity of Public A/B Test Summaries

## Core Entities (as defined in the spec)

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **ABSummary** | Raw metrics extracted from a public A/B test summary. | `url` (string, required), `variant_a_n` (int, required), `variant_b_n` (int, required), `effect_size` (float, required), `effect_size_type` (enum: `absolute`, `lift_percent`), `reported_p` (float or string for inequality), `confidence_interval` (object with `lower` and `upper` floats, optional), `outcome_type` (enum: `binary`, `continuous`), `timestamp` (ISO‑8601 string, optional) |
| **AuditRecord** | Result of consistency checking for one `ABSummary`. | `url` (string), `reconstructed_p` (float), `reconstructed_effect_size` (float), `diff_abs_p` (float), `diff_abs_effect` (float), `flag_inconsistent` (bool), `category` (enum: `p_value`, `effect_size`, `sample_size`, `missing_metric`, `size_mismatch`, `ci_violation`), `notes` (string) |

## Schemas

### `contracts/extracted_summary.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Extracted A/B Summary"
type: object
required:
  - url
  - variant_a_n
  - variant_b_n
  - effect_size
  - effect_size_type
  - reported_p
  - outcome_type
properties:
  url:
    type: string
    format: uri
    description: "Original URL of the public A/B test summary."
  variant_a_n:
    type: integer
    minimum: 1
    description: "Sample size for variant A."
  variant_b_n:
    type: integer
    minimum: 1
    description: "Sample size for variant B."
  effect_size:
    type: number
    description: "Reported effect size (absolute difference for binary outcomes, mean difference for continuous)."
  effect_size_type:
    type: string
    enum: ["absolute", "lift_percent"]
    description: "Units of the reported effect size."
  reported_p:
    type: string
    description: "Reported p‑value; may be a numeric string (e.g., \"0.032\") or an inequality (e.g., \"p<0.001\")."
  confidence_interval:
    type: object
    required:
      - lower
      - upper
    properties:
      lower:
        type: number
      upper:
        type: number
    description: "Optional 95 % confidence interval for the effect size."
  outcome_type:
    type: string
    enum: ["binary", "continuous"]
    description: "Whether the metric is a conversion rate (binary) or a continuous measure."
  timestamp:
    type: string
    format: date-time
    description: "Optional publication timestamp extracted from the source."
```

### `contracts/audit_record.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Audit Record"
type: object
required:
  - url
  - reconstructed_p
  - reconstructed_effect_size
  - diff_abs_p
  - diff_abs_effect
  - flag_inconsistent
  - category
properties:
  url:
    type: string
    format: uri
    description: "URL of the audited summary."
  reconstructed_p:
    type: number
    description: "Two‑sided p‑value computed from the reconstructed statistical test."
  reconstructed_effect_size:
    type: number
    description: "Effect size derived from raw counts (absolute difference)."
  diff_abs_p:
    type: number
    description: "Absolute difference between reported and reconstructed p‑values."
  diff_abs_effect:
    type: number
    description: "Absolute difference between reported and reconstructed effect sizes."
  flag_inconsistent:
    type: boolean
    description: "True if any inconsistency rule from FR‑004 is triggered."
  category:
    type: string
    enum: ["p_value", "effect_size", "sample_size", "missing_metric", "size_mismatch", "ci_violation", "inequality_p", "none"]
    description: "Primary reason for inconsistency, or \"none\" if consistent."
  notes:
    type: string
    description: "Human‑readable explanation of the flag or any parsing issues."
```

## Derivation Flow
1. **Raw HTML** → `extracted_summary.schema.yaml` (via `code/extract.py`).  
2. **Extracted Summary** → `audit_record.schema.yaml` (via `code/reconstruct.py` + `code/audit.py`).  
3. **Audit Records** → Aggregated CSV (`summary_report.csv`) and final JSON (`audit_report.json`).  

All intermediate files are version‑hashed and recorded in `data/manifest.yaml` to satisfy **III** and **V** of the constitution.  

**Single Source of Truth (SSoT)**: `data/manifest.yaml` is the authoritative record of provenance and checksums for all raw and processed data; `output/audit_report.json` is the authoritative source for all reported metrics and figures, ensuring traceability back to a single artifact.

---

