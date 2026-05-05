---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Field**: statistics

## Research question

Can we quantify the evolution of programming language popularity and topic trends using the temporal frequency of tags associated with questions on Stack Overflow? Specifically, what statistical patterns emerge in tag co-occurrence and growth rates that indicate emerging versus declining technologies?

## Motivation

Understanding technology adoption curves through developer community activity has practical value for educators, employers, and tool creators. This analysis addresses the gap between anecdotal tech trend reports and empirical, reproducible measurements derived from a large-scale public dataset. The Stack Overflow data dump provides sufficient volume and temporal coverage to support statistically robust trend analysis.

## Related work

- [Is Stack Overflow Overflowing With Questions and Tags (2015)](http://arxiv.org/abs/1508.03601v1) — Foundational analysis of question and tag growth patterns on Stack Overflow, establishing baseline methodology for studying platform evolution.
- [Question Relatedness on Stack Overflow: The Task, Dataset, and Corpus-inspired Models (2019)](http://arxiv.org/abs/1905.01966v2) — Provides dataset structure and corpus construction techniques applicable to tag-based question analysis.
- [On negative results when using sentiment analysis tools for software engineering research (2017)](https://doi.org/10.1007/s10664-016-9493-x) — Cautionary methodology for applying statistical analysis to software engineering data, relevant for avoiding analytical pitfalls.

## Expected results

We expect to identify at least 3-5 technology categories showing statistically significant growth trajectories (p < 0.05) and 2-3 declining categories over the 2015-2023 period. Time series decomposition should reveal seasonal patterns in tag usage correlating with major framework releases or conference cycles. The strength of evidence will be measured through confidence intervals on growth rate estimates and cross-validation of trend stability across data subsets.

## Methodology sketch

- Download the Stack Overflow data dump (PostsTags table) from https://archive.org/details/stackexchange or https://data.stackexchange.com/
- Preprocess tag data: extract tag names, post creation dates, and normalize tag strings (lowercase, trim whitespace)
- Aggregate tag frequencies into monthly time bins spanning 2015-2023 to reduce noise
- Compute tag growth rates using linear regression on log-transformed frequencies
- Apply Mann-Kendall test for trend significance on top 50 most-frequent tags
- Perform co-occurrence analysis: calculate Pearson correlation between tag pairs appearing on same posts
- Use hierarchical clustering on correlation matrix to identify technology clusters
- Generate time series plots with confidence intervals using Python (pandas, matplotlib, statsmodels)
- Validate findings via bootstrapping: resample monthly data 1000 times to assess estimate stability
- Export results as reproducible Jupyter notebook with all code and intermediate data files

## Duplicate-check

- Reviewed existing ideas: none available in current corpus.
- Closest match: N/A (first fleshed-out idea in this field).
- Verdict: NOT a duplicate
