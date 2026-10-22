# Data Model: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Core Entities

### `ABSummary`
Represents a single extracted A/B test summary (FR‑002).

```yaml
ABSummary:
  url: string               # required, valid URI
  source_domain: string     # required, domain extracted from URL (used for bias handling, FR‑027)
  variant_a_n: integer      # required, ≥1
  variant_b_n: integer      # required, ≥1
  variant_a_conversions: integer  # required, ≥0 (binary only)
  variant_b_conversions: integer  # required, ≥0 (binary only)
  reported_p: float|null    # required, 0 < p ≤ 1 or null for inequality
  reported_effect_size: float   # required, can be negative
  outcome_type: string      # required, one of: binary, continuous
  confidence_interval:      # optional
    lower: float
    upper: float
  extraction_timestamp: string # ISO‑8601 timestamp of extraction
  publication_year: integer|null   # optional, year of the source (used for subgroup analysis, FR‑032)
  extraction_notes: string|null   # optional, FR‑007 messages
```

### `AuditRecord`
Result of the inconsistency check for one `ABSummary` (FR‑024).

```yaml
AuditRecord:
  url: string
  reported_p: float|null
  reported_effect_size: float
  reported_sample_size_a: integer
  reported_sample_size_b: integer
  reconstructed_p: float
  reconstructed_effect_size: float
  diff_abs_p: float
  diff_abs_effect: float
  flag_inconsistent: boolean
  notes: string   # ≤ 200 chars, includes ERR‑### codes if any
```

### `SummaryReport`
Aggregated prevalence statistics (FR‑024, SC‑024).

```yaml
SummaryReport:
  total_summaries: integer
  inconsistent_count: integer
  inconsistent_rate: float      # 0 – 1
  bias_adjusted_rate: float     # 0 – 1
  wilson_ci_lower: float
  wilson_ci_upper: float
```

### `ValidationRecord`
Outcome of a validation task (synthetic or real‑world).

```yaml
ValidationRecord:
  dataset_type: string          # "synthetic" or "real_world"
  total_samples: integer
  precision: float
  recall: float
  f1_score: float
  pass: boolean
```

## Relationships
- An **AuditReport** is a list of `AuditRecord`s plus a `SummaryReport` metadata block.  
- `ABSummary` → `AuditRecord` (one‑to‑one).  
- `ValidationRecord` is stored in `data/validation/` and referenced by the CI summary.  

## Constraints (derived from FRs)
- **FR‑004**: `flag_inconsistent` is `true` iff `diff_abs_p > 0.05` **or** `diff_abs_effect > 0.05 × max(|reported_effect|,|reconstructed_effect|)`.  
- **FR‑004b**: If `|variant_a_n – variant_b_n| / max(variant_a_n, variant_b_n) > 0.05`, `notes` must contain a `data_quality_warning`.  
- **FR‑012**: When baseline conversion is missing, `reconstructed_effect_size` is derived from the average of variant rates; `notes` must contain a heuristic flag.  
- **FR‑027**: Domain proportions are stored separately; any domain > 30 % triggers subsampling before prevalence calculation.  
- **FR‑032**: Subgroup `AuditRecord`s are grouped by `source_domain` and `publication_year`; each subgroup with ≥ 10 entries runs a Fisher exact test with Bonferroni‑adjusted α.

---===END_ARTIFACT===
===BEGIN_ARTIFACT projects/PROJ-492-evaluating-the-statistical-validity-of-p/specs/001-evaluating-the-statistical-validity-of-p/contracts/ABSummary.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "ABSummary"
type: object
required:
  - url
  - source_domain
  - variant_a_n
  - variant_b_n
  - variant_a_conversions
  - variant_b_conversions
  - reported_p
  - reported_effect_size
  - outcome_type
properties:
  url:
    type: string
    format: uri
    description: "Original URL of the public A/B test summary"
  source_domain:
    type: string
    description: "Domain extracted from URL hostname for bias assessment (FR‑027)"
  variant_a_n:
    type: integer
    minimum: 1
    description: "Sample size for variant A"
  variant_b_n:
    type: integer
    minimum: 1
    description: "Sample size for variant B"
  variant_a_conversions:
    type: integer
    minimum: 0
    description: "Conversions for variant A (binary outcomes)"
  variant_b_conversions:
    type: integer
    minimum: 0
    description: "Conversions for variant B (binary outcomes)"
  reported_p:
    type:
      - number
      - "null"
    minimum: 0.0
    maximum: 1.0
    description: "Reported p‑value (null if given as inequality)"
  reported_effect_size:
    type: number
    description: "Reported effect size (absolute difference, lift, or mean difference)"
  outcome_type:
    type: string
    enum:
      - "binary"
      - "continuous"
    description: "Nature of the outcome metric"
  confidence_interval:
    type:
      - object
      - "null"
    description: "Optional confidence interval"
    properties:
      lower:
        type: number
      upper:
        type: number
    required:
      - lower
      - upper
  extraction_timestamp:
    type: string
    format: date-time
    description: "ISO‑8601 timestamp of extraction"
  publication_year:
    type:
      - integer
      - "null"
    minimum: 1900
    maximum: 2100
    description: "Publication year of the source (optional, used for subgroup analysis)"
  extraction_notes:
    type:
      - string
      - "null"
    description: "Optional notes or error messages from the extraction step"
additionalProperties: false