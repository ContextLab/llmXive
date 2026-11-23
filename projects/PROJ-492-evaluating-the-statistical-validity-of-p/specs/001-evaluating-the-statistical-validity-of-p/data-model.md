# Data Model: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Core Entities

### `ABSummary`
Represents a single extracted A/B test summary (FR‑002).

```yaml
ABSummary:
  url: string               # required, valid URL
  source_domain: string     # required, domain extracted from URL (provenance)
  variant_a_n: integer      # required, ≥1
  variant_b_n: integer      # required, ≥1
  variant_a_conversions: integer   # required, ≥0 (binary only)
  variant_b_conversions: integer   # required, ≥0 (binary only)
  reported_p: float|null   # required, 0 < p ≤ 1 or null for inequality bounds
  reported_effect_size: float      # required, can be negative
  outcome_type: string      # required, one of: binary, continuous
  confidence_interval:      # optional
    lower: float
    upper: float
  extraction_timestamp: string     # ISO‑8601 timestamp
  publication_year: integer|null  # optional
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
  diff_abs_p: float                # |reported p – reconstructed p|
  diff_abs_effect: float           # absolute relative difference in effect size
  flag_inconsistent: boolean
  notes: string                    # ≤ 200 chars, includes ERR‑### codes if any
```

### `SummaryReport`
Aggregated prevalence statistics (FR‑024, SC‑024).

```yaml
SummaryReport:
  total_summaries: integer
  inconsistent_count: integer
  inconsistent_rate: float          # 0 – 1
  wilson_ci_lower: float
  wilson_ci_upper: float
```

### `ValidationRecord`
Outcome of a validation task (synthetic Monte Carlo or real‑world extraction) (FR‑026, FR‑031b).

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
- Each **AuditRecord** is a one‑to‑one mapping from an **ABSummary**.  
- **SummaryReport** aggregates the `flag_inconsistent` field across all **AuditRecord** rows.  
- **ValidationRecord** lives under `data/validation/` and is referenced in CI logs.

## Constraints (derived from FRs)
- **FR‑004**: `flag_inconsistent` is `true` iff `diff_abs_p > 0.05` **or** `diff_abs_effect > 0.05 × max(|reported_effect|,|reconstructed_effect|)`.  
- **FR‑004b**: If `|variant_a_n – variant_b_n| / max(variant_a_n, variant_b_n) > 0.05`, `notes` must contain a `data_quality_warning`.  
- **FR‑012**: When baseline conversion is missing, `reconstructed_effect_size` is derived from the average of the two variant rates; `notes` must contain a `baseline_heuristic` flag.  
- **SC‑001**: Extraction accuracy (field‑level) must be ≥ 95 % on the validation set (evaluated via `ValidationRecord`).  
- **SC‑003** & **SC‑026**: Monte Carlo validation must achieve absolute difference ≤ 0.005 for each statistical routine.  
- **SC‑015**: The sensitivity sweep must not change the overall inconsistency prevalence by more than 0.02; runs exceeding this limit are flagged as failures.

---===END DATA MODEL===---
