# Data Model: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Core Entities

### ABSummary
Represents a single audited A/B test summary. Conforms to FR-002 inline schema.

```yaml
ABSummary:
  url: string (required, valid URL)
  variant_a_n: integer (required, ≥1)
  variant_b_n: integer (required, ≥1)
  variant_a_conversions: integer (required, ≥0)
  variant_b_conversions: integer (required, ≥0)
  reported_p: float (required, 0 < p ≤ 1, or null for inequality bounds)
  reported_effect_size: float (required, can be negative)
  outcome_type: string (required, one of: binary, continuous)
  confidence_interval: object (optional, {lower: float, upper: float})
  extraction_notes: string (optional, FR-007 errors)
```

### AuditRecord
Result of the consistency check for one summary. Conforms to FR-024.

```yaml
AuditRecord:
  url: string (required)
  reported_p: float (required)
  reported_effect_size: float (required)
  reported_sample_size_a: integer (required)
  reported_sample_size_b: integer (required)
  reconstructed_p: float (required)
  reconstructed_effect_size: float (required)
  diff_abs_p: float (required)
  diff_abs_effect: float (required)
  flag_inconsistent: boolean (required)
  notes: string (required)
```

### ValidationRecord
Result of validation tasks (Synthetic & Real-World).

```yaml
ValidationRecord:
  dataset_type: string (required, one of: synthetic, real_world)
  total_samples: integer (required)
  precision: float (required)
  recall: float (required)
  f1_score: float (required)
  pass: boolean (required)
```

## Relationships

- **AuditReport** contains a list of **AuditRecord** (FR-024).
- **SummaryReport** aggregates **AuditRecord** statistics (FR-005a, FR-024).
- **BiasReport** contains domain proportions derived from **ABSummary** (FR-027).

## Constraints

- **FR-004**: `flag_inconsistent` is True if `diff_abs_p > 0.05` OR `diff_abs_effect > 0.05 * max(reported, reconstructed)`. **Note**: Uses absolute threshold only (no log-scale per methodology-5bca6076).
- **FR-004b**: `notes` must include warning if sample size discrepancy > 5%.
- **FR-012**: When baseline is missing, effect size reconstruction has reduced rigor; uncertainty quantification is documented in notes (scientific_soundness-ad85a63f).
- **FR-027**: Bias-adjusted rate uses equal weighting per domain (scientific_soundness-64bd4091).
- **FR-032**: Subgroup reports must include Bonferroni-adjusted p-values.