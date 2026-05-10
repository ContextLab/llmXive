---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Power and Sample Size in Open Neuroimaging Datasets

**Field**: statistics

## Research question

How does sample size in open neuroimaging datasets correlate with the reproducibility of reported effect sizes across independent studies?

## Motivation

Neuroimaging research frequently relies on publicly available datasets where power analyses are not systematically documented. Understanding the empirical relationship between sample size and result reproducibility would inform evidence-based guidelines for minimum sample sizes in future studies and help interpret findings from existing datasets more cautiously.

## Related work

- [Power failure: why small sample size undermines the reliability of neuroscience](https://doi.org/10.1038/nrn3475) — Establishes the theoretical argument that low power in neuroscience leads to inflated effect sizes and poor reproducibility.
- [The Statistical Analysis of fMRI Data](http://arxiv.org/abs/0906.3662v1) — Reviews statistical challenges in fMRI analysis including multiple comparison correction and power considerations.
- [Deep Learning in current Neuroimaging: a multivariate approach with power and type I error control but arguable generalization ability](http://arxiv.org/abs/2103.16685v1) — Discusses power and Type I error control in neuroimaging machine learning applications, highlighting gaps in statistical significance reporting.

## Expected results

We expect to find a positive correlation between reported sample size and effect size stability across studies, with smaller samples showing greater variance in reported effects. The measurement of reproducibility (e.g., effect size consistency across independent analyses) would confirm or falsify whether low-power neuroimaging studies systematically overestimate true effects.

## Methodology sketch

- Download 3-5 open neuroimaging datasets from OpenNeuro or ADNI (public URLs documented in tasks.md)
- Extract reported effect sizes and sample sizes from published analyses associated with each dataset
- Compute post-hoc power estimates using standard formulas (G*Power or equivalent Python implementation)
- Calculate effect size consistency metrics (e.g., coefficient of variation) across independent studies using the same dataset
- Apply linear regression to test the relationship between sample size and effect size stability
- Generate visualization plots showing sample size vs. reproducibility with confidence intervals

## Duplicate-check

- Reviewed existing ideas: N/A (new field)
- Closest match: N/A (first idea in statistics field)
- Verdict: NOT a duplicate
