# Census Data Statistical Interpretation

## Overview

This document provides the statistical interpretation framework for the knot
census data used in this project. The dataset consists of the complete enumeration
of prime knots with crossing number ≤13, obtained from {{claim:c_3ea0f57a}}
(Katlas) and validated against OEIS A002863 and KnotInfo reference values.

## Census Data Definition

A census in mathematical knot theory refers to a complete, exhaustive enumeration
of all prime knots up to a specified crossing number. Unlike sampling-based
datasets, a census represents the entire population of interest with no missing
elements (within the defined bounds).

For this project:
- **Population**: All prime knots with crossing number ≤13
- **Source**: {{claim:c_3ea0f57a}} (Katlas)
- **Validation**: Cross-referenced with OEIS A002863 (counts per crossing number)
- **Scope**: Hyperbolic knots only (non-hyperbolic knots excluded per FR-012)

## Statistical Interpretation Principles

### Census vs. Sample Distinction

This dataset is a **census**, not a sample. This distinction has critical
implications for statistical interpretation:

1. **No Sampling Variability**: Since all elements are enumerated, there is no
 sampling error. Observed statistics are exact for the defined population.

2. **No Inferential Statistics**: Traditional inferential statistics (hypothesis
 testing, confidence intervals, p-values) are **not applicable** to census data.
 These tools are designed to generalize from samples to populations, but here
 we already have the complete population.

3. **Descriptive Statistics Only**: All reported statistics must be framed as
 descriptive summaries of the observed population, not estimates of broader
 parameters.

### Constitution Principle VII Compliance

Per Constitution Principle VII (census-data exception), p-values are explicitly
**not reported** for any analysis on this census data. This aligns with the
mathematical consensus that p-values have no meaningful interpretation when
the complete population is enumerated.

In all output artifacts:
- Correlation coefficients (Pearson, Spearman) are reported as **descriptive
 measures of association**
- Effect sizes (Cohen's d, correlation r) are reported without p-values
- All statistical claims are qualified as "for the census of prime knots with
 crossing number ≤13"

## Appropriate Statistical Measures

### Descriptive Statistics

The following descriptive statistics are appropriate and reported:

| Measure | Purpose | Census Interpretation |
|---------|---------|----------------------|
| Mean | Central tendency | Exact average for the population |
| Standard Deviation | Dispersion | Exact spread for the population |
| Correlation (r) | Association strength | Exact association in the population |
| Cohen's d | Effect size | Exact standardized difference |
| R² | Model fit | Exact proportion of variance explained |

### Measures to Avoid

The following are **inappropriate** for census data:

| Measure | Reason for Avoidance |
|---------|---------------------|
| p-values | No sampling variability to test |
| Confidence intervals | Parameters are known exactly, not estimated |
| Hypothesis tests | Null hypothesis testing assumes sampling |
| Standard errors | No sampling error to quantify |

## Interpretation Guidelines

### For Correlation Analysis

When reporting correlations between knot invariants (e.g., crossing number vs.
braid index, crossing number vs. hyperbolic volume):

1. **Frame as Descriptive**: Report as "The correlation between X and Y in the
 census is r = 0.XX" rather than "X and Y are significantly correlated"

2. **Report Effect Size**: Include Cohen's guidelines for interpretation:
 - r < 0.1: Negligible
 - 0.1 ≤ r < 0.3: Small
 - 0.3 ≤ r < 0.5: Medium
 - r ≥ 0.5: Large

3. **Acknowledge Constraints**: Note mathematical constraints (e.g., braid
 index ≤ crossing number) that may induce structural correlations

### For Group Comparisons

When comparing alternating vs. non-alternating knots:

1. **Report Exact Differences**: "The mean crossing number for alternating
 knots is X, compared to Y for non-alternating knots (difference = Z)"

2. **Use Effect Sizes**: Report Cohen's d as the standardized measure of
 difference magnitude

3. **Avoid Significance Language**: Do not use terms like "significantly
 different" or "statistically significant"

## Census-Specific Considerations

### Selection Bias Acknowledgment

This census has explicit boundaries that limit generalizability:

1. **Crossing Number Bound**: Results apply only to knots with crossing number
 ≤13. No inference is made about knots with higher crossing numbers.

2. **Hyperbolic-Only Filtering**: Per FR-012, non-hyperbolic knots (volume = 0)
 are excluded. This creates a selection bias that must be acknowledged in
 all interpretations. See docs/reproducibility/selection_bias.md for details.

3. **Prime Knots Only**: Composite knots are not included in this census.

### Population Boundaries

The census represents a **finite, bounded population**:

- Total prime knots with crossing number ≤13: [See docs/reproducibility/dataset_counts.md]
- Total hyperbolic knots after filtering: [See docs/reproducibility/dataset_counts.md]

All statistical claims must explicitly reference these population boundaries.

## Reporting Template

When presenting statistical results, use the following template:

```
For the census of prime knots with crossing number ≤13 (N = [count]):
- The [measure] between [variable1] and [variable2] is [value].
- This represents a [small/medium/large] effect per Cohen's guidelines.
- No p-values are reported as this is census data (Constitution Principle VII).
- Results apply only to the specified population bounds.
```

## Related Documentation

- docs/reproducibility/data_quality_report.md: Data quality metrics
- docs/reproducibility/dataset_counts.md: Population enumeration
- docs/reproducibility/selection_bias.md: Hyperbolic-only filtering acknowledgment
- docs/reproducibility/core_invariants_tabulation.md: Core invariant validation
- docs/reproducibility/correlation_metrics.md: Correlation coefficient documentation

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-06-02 | PROJ-552 Team | Initial creation per Constitution Principle VII |