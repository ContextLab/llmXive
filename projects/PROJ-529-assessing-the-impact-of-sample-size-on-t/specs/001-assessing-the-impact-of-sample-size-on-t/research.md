# Research Notes: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Background
Meta-analyses combine results from multiple studies to produce a pooled effect estimate.
However, the reliability of these estimates depends on the number of studies (k) included.
This project investigates the relationship between k and meta-analytic stability.

## Key Questions
1. What is the minimum k required for stable effect size estimates?
2. How does coverage rate vary with k?
3. At what point do we observe diminishing returns in stability?

## Methodology
- Data: Real-world meta-analyses from Cochrane/Campbell (fallback: simulation)
- Subsampling: Bootstrap resampling for k = 3 to N
- Models: Fixed Effects (FE) and Random Effects (RE) with estimator switching
- Analysis: GAM modeling for threshold detection

## Preliminary Findings
*To be updated as analysis progresses*