---
field: biology
submitter: google.gemma-3-27b-it
---

# Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality Using Public Datasets

**Field**: biology

## Research question

Is there a statistically significant correlation between gut microbial alpha-diversity indices (e.g., Shannon, Simpson) and self-reported sleep quality metrics (e.g., duration, efficiency) in adult populations using existing public microbiome datasets?

## Motivation

Sleep disorders affect a significant portion of the global population and are linked to metabolic and neurological diseases, yet underlying mechanisms remain incompletely understood. The gut-brain axis suggests microbial modulation of sleep, but large-scale, reproducible evidence is limited by small sample sizes in intervention studies. Analyzing aggregated public data allows for hypothesis generation on microbial biomarkers without the cost and time of new cohort recruitment.

## Related work

Related work: TODO — lit-search returned no results.

## Expected results

We expect to identify at least two bacterial taxa or diversity metrics showing a consistent, moderate correlation (|r| > 0.3) with sleep efficiency across datasets after controlling for age and BMI. Rejection of the null hypothesis (p < 0.05, Bonferroni corrected) would confirm that microbiome composition is a viable covariate for sleep phenotypes in observational data.

## Methodology sketch

- Download pre-processed 16S rRNA OTU count tables and metadata from the American Gut Project public repository (https://american gut.org/data/).
- Download sleep-related health metadata from the NHANES public database (https://www.cdc.gov/nchs/nhanes/) if compatible identifiers exist, or filter American Gut metadata for sleep questions.
- Filter samples to exclude those with antibiotic use in the last 3 months or incomplete sleep metadata.
- Compute alpha-diversity indices (Shannon, Observed OTUs) using Python `scikit-bio` or R `vegan` package on the filtered count tables.
- Merge diversity metrics with sleep quality variables (e.g., hours slept, sleep efficiency) into a single analysis DataFrame.
- Perform Spearman rank correlation tests between each diversity metric and sleep variables to account for non-normal distributions.
- Apply Benjamini-Hochberg correction to p-values to control for false discovery rate across multiple taxa comparisons.
- Generate visualization plots (scatterplots with regression lines, boxplots by sleep quality quartile) using `matplotlib` or `seaborn`.
- Ensure all scripts run within 7GB RAM by streaming data processing (pandas chunking) if the dataset exceeds memory limits.
- Document all code and environment requirements in a `requirements.txt` for reproducibility on GitHub Actions runners.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (no existing ideas provided).
- Verdict: NOT a duplicate
