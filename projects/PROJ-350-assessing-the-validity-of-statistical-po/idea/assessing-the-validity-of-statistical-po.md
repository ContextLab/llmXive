---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

**Field**: statistics

## Research question

How do planned statistical power estimates in pre-registered studies compare to the achieved power calculated from actual sample sizes and observed effect sizes, and what factors systematically predict discrepancies between them?

## Motivation

Pre-registration of studies now includes required power analyses, yet the accuracy of these initial estimates remains unvalidated at scale. Understanding whether researchers systematically overestimate power, and what methodological or design factors drive discrepancies, would inform best practices for study planning and strengthen reproducibility in empirical science.

## Literature gap analysis

### What we searched

Literature searches were conducted on Semantic Scholar and arXiv using queries including "statistical power pre-registration accuracy," "power analysis validation pre-registered studies," and "achieved power vs planned power empirical studies." The searches returned minimal on-topic results focused specifically on validating power estimates in pre-registered studies.

### What is known

- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — This work addresses statistical methodology for comparing healthcare outcomes, establishing that statistical power considerations are critical in observational studies but does not directly examine power estimation accuracy in pre-registered research.

### What is NOT known

No published work has systematically quantified the discrepancy between planned and achieved statistical power across a corpus of pre-registered studies. There is no evidence base identifying which study design features (e.g., effect size assumptions, sample size targets, field of study) predict power miscalculation. The extent to which researchers' power estimates are systematically optimistic or conservative remains undocumented.

### Why this gap matters

Filling this gap would benefit researchers designing pre-registered studies by providing empirical evidence on power estimation accuracy, potentially reducing underpowered studies that waste resources and fail to detect true effects. It would also inform pre-registration platforms and journals about whether current power analysis requirements are being met in practice.

### How this project addresses the gap

This project will extract planned power estimates, effect size assumptions, and sample sizes from pre-registered studies on OSF, then retrospectively calculate achieved power using observed data. The comparison between planned and achieved power will directly quantify the gap, while regression analysis will identify predictors of discrepancy.

## Expected results

We expect to find systematic overestimation of power in a substantial proportion of pre-registered studies, with effect size assumptions being the primary driver of discrepancies. A null result (no systematic discrepancy) would also be informative, suggesting current power analysis practices are well-calibrated. Either outcome would be publishable as it would either identify a reproducibility concern or validate existing best practices.

## Methodology sketch

- Download pre-registered study metadata and documents from Open Science Framework (OSF) using their public API (https://osf.io/api/v1/)
- Extract planned power estimates, target sample sizes, and effect size assumptions from pre-registration forms using regex and NLP text extraction
- Obtain actual sample sizes and observed effect sizes from published results or data repositories linked to each study
- Calculate achieved power using the `pwr` R package or `statsmodels` Python library with observed effect sizes and actual sample sizes
- Compute discrepancy metrics (planned minus achieved power) for each study
- Perform multiple linear regression to identify predictors of discrepancy (field of study, data type, sample size category, effect size domain)
- Generate diagnostic plots showing distribution of discrepancies and relationship with study characteristics
- Statistical tests: Kolmogorov-Smirnov test for distribution differences, F-test for regression model significance, with alpha = 0.05
- All analysis will be conducted in R or Python on GitHub Actions runners with 7GB RAM, processing batches of 50-100 studies per job

## Duplicate-check

- Reviewed existing ideas: [none provided in input — pending integration with project corpus]
- Closest match: [no existing ideas provided for comparison]
- Verdict: NOT a duplicate (pending corpus integration)
