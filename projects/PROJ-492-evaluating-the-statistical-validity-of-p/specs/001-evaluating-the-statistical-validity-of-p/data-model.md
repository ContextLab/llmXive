# Data Model: 001-eval-ab-test-validity

## ABSummary Entity

Represents a single publicly posted experiment with extracted metrics.

```python
class ABSummary:
    url: str                              # Source URL (Constitution VII)
    domain: str                           # Extracted domain (for FR-027)
    publication_year: int                 # Year of publication (for FR-032)
    outcome_type: str                     # "binary" or "continuous"
    variant_a_n: int                      # Sample size, variant A
    variant_b_n: int                      # Sample size, variant B
    variant_a_rate: float                 # Conversion rate, variant A (if binary)
    variant_b_rate: float                 # Conversion rate, variant B (if binary)
    effect_size: float                    # Reported effect size (difference or lift)
    reported_p: float                     # Reported p-value (numeric or bound)
    reported_p_inequality: bool           # True if p-value was inequality (e.g., p<0.001)
    confidence_interval: Optional[Tuple]  # Reported confidence interval (if available)
    notes: str                            # Extraction notes / warnings
    extracted_at: datetime                # Timestamp of extraction
```

## AuditRecord Entity

Result of the consistency check for one summary.

```python
class AuditRecord:
    url: str                              # Source URL
    reported_p: float                     # Reported p-value
    reported_effect_size: float           # Reported effect size
    reported_sample_size_a: int           # Reported sample size A
    reported_sample_size_b: int           # Reported sample size B
    reconstructed_p: float                # Reconstructed p-value
    reconstructed_effect_size: float      # Reconstructed effect size
    diff_abs_p: float                     # Absolute difference in p-values
    diff_abs_effect: float                # Absolute difference in effect sizes
    flag_inconsistent: bool               # True if inconsistent (FR-004)
    flag_size_mismatch: bool              # True if sample size discrepancy >5% (FR-004b)
    flag_missing_metric: bool             # True if required metric missing
    notes: str                            # Audit notes / explanations
```

## PrevalenceReport Entity

Aggregate statistics for the audit corpus.

```python
class PrevalenceReport:
    total_summaries: int                  # Total audited summaries
    inconsistent_count: int               # Count of inconsistent entries
    consistent_count: int                 # Count of consistent entries
    missing_metric_count: int             # Count with missing metrics
    inconsistent_rate: float              # Raw inconsistency rate
    bias_adjusted_rate: float             # Domain-weighted inconsistency rate
    wilson_ci_lower: float                # 95% Wilson CI lower bound
    wilson_ci_upper: float                # 95% Wilson CI upper bound
    baseline_proportion: float            # Baseline used for binomial test (FR-005a)
    binomial_p_value: float               # Binomial test p-value (FR-005a)
    sensitivity_range: float              # Max variation across baseline 0.02-0.10 (FR-005b)
    generated_at: datetime                # Timestamp of generation
```

## DomainBiasReport Entity

Domain-level bias assessment (FR-027).

```python
class DomainBiasReport:
    domain_proportions: Dict[str, float]  # Proportion per domain
    max_domain_proportion: float          # Maximum domain proportion
    exceeds_30_percent: bool              # True if any domain >30%
    bias_adjusted_rate: float             # Domain-weighted inconsistency rate
    adjustment_method: str                # "weighted_average"
```

## SubgroupReport Entity

Per-domain/year prevalence with Fisher's exact test (FR-032).

```python
class SubgroupReport:
    domain: str                           # Domain name
    year: int                             # Publication year
    total_count: int                      # Summaries in subgroup
    inconsistent_count: int               # Inconsistent count
    prevalence: float                     # Subgroup inconsistency prevalence
    fisher_p_value: float                 # Fisher's exact test p-value
    is_significantly_different: bool      # True if p ≤ 0.05
```
