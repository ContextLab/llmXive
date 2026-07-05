# Research Notes: Sample Size and Meta-Analytic Stability

## Background
Meta-analyses with few studies (low k) are prone to high variance in effect estimates and unreliable confidence interval coverage. This project aims to empirically determine the "tipping point" where increasing k yields diminishing returns in stability.

## Key References
- Ioannidis, J. P. A., et al. (2008). "The performance of the DerSimonian and Laird method in meta-analysis."
- Cochrane Handbook for Systematic Reviews of Interventions (Chapter 10: Analysing data and undertaking meta-analyses).
- Campbell Collaboration guidelines on meta-analysis.

## Hypotheses
1. **H1**: Stability (inverse of SD of pooled effects) increases non-linearly with k, following a 1/sqrt(k) trend initially, then plateauing.
2. **H2**: Coverage rates for Random Effects models are significantly lower than nominal (95%) when k < 10.
3. **H3**: A threshold exists (likely between k=10 and k=20) where stability metrics stabilize within a 2% margin of the asymptotic value.

## Methodology Notes
- **Bootstrap Strategy**: Stratified resampling of studies to preserve effect size distribution.
- **Model Selection**: REML preferred for small k due to better bias properties; DL used for larger k for computational efficiency.
- **Threshold Detection**: Derivative of the GAM fit (d(SD)/dk) will be used to locate the inflection point where the rate of improvement drops below 0.05 per unit k.
