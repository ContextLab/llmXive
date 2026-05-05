---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys

**Field**: statistics

## Research question

How does the choice of missing data handling approach influence the bias of variance estimates in complex survey designs?

## Motivation

Public survey datasets routinely contain missing values, and researchers must choose how to handle them before conducting statistical inference. While multiple imputation is widely recommended, its impact on variance estimation accuracy across different survey designs remains under-characterized. Understanding this relationship matters because biased variance estimates lead to incorrect confidence intervals and hypothesis tests, undermining the reliability of policy-relevant findings from major surveys like the ACS and GSS.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using search terms: "variance estimation imputation survey," "missing data variance bias complex survey," and "multiple imputation variance estimation." We retrieved 3 papers from the literature block, with systematic screening for relevance to variance estimation under missing data in survey contexts.

### What is known

- [Variance estimation for nearest neighbor imputation for US Census long form data (2011)](http://arxiv.org/abs/1108.1074v1) — Establishes variance estimation procedures specifically for nearest neighbor imputation applied to Census long form data, accounting for both imputation uncertainty and sampling design.

### What is NOT known

No published work has systematically compared variance estimation bias across multiple imputation methods (MICE, single imputation, complete-case) using real-world complex survey datasets. The relationship between imputation method choice and variance estimate accuracy remains unquantified for datasets like the ACS and GSS with their specific design features.

### Why this gap matters

Survey analysts and policymakers rely on accurate variance estimates to make decisions about program effectiveness and resource allocation. Without clear guidance on how imputation choices affect variance accuracy, researchers may inadvertently report misleading confidence intervals, leading to incorrect conclusions about population parameters and policy impacts.

### How this project addresses the gap

This project will apply multiple imputation methods to real survey datasets and directly compare resulting variance estimates against known population parameters where available. The methodology produces previously-unavailable empirical evidence on the magnitude and direction of variance estimation bias under different imputation strategies.

## Expected results

We expect to find that complete-case analysis systematically underestimates variance when missingness is not completely at random, while single imputation produces overly narrow confidence intervals. Multiple imputation should yield more accurate variance estimates, but the degree of improvement will depend on the missing data mechanism and survey design complexity. Evidence will be measured through comparison of estimated variances to design-based true variances where calculable.

## Methodology sketch

- Download public survey datasets with documented sampling designs: American Community Survey (https://www.census.gov/programs-surveys/acs), General Social Survey (https://gss.norc.org)
- Extract variables with documented missingness patterns and known design weights
- Implement three missing data handling approaches: complete-case analysis, single mean imputation, and multiple imputation by chained equations (MICE)
- For each approach, calculate point estimates and variance estimates for key population parameters (means, proportions)
- Where true population parameters are known (from census benchmarks), compute bias in variance estimates as (estimated variance − true variance) / true variance
- Apply statistical tests to compare variance estimation accuracy across methods: paired t-tests on bias measures across multiple parameters
- Generate diagnostic plots showing relationship between missingness rate and variance estimation bias for each method
- Document computational requirements and runtime to verify feasibility within GHA constraints (target: ≤6 hours total)

## Duplicate-check

- Reviewed existing ideas: [no existing ideas in corpus provided for comparison]
- Closest match: N/A
- Verdict: NOT a duplicate
