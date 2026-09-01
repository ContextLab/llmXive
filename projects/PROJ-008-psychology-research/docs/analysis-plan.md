# Analysis Plan: Missing Data Handling and Imputation Strategies

**Project**: PROJ-008-psychology-research
**Study**: Mindfulness Components and Delivery Formats in ASD Social Skills
**Version**: 1.0
**Date**: 2026-04-29

## 1. Introduction

This document outlines the statistical strategies for handling missing data in the meta-analysis of mindfulness interventions for social skills in children (ages 6–12) with Autism Spectrum Disorder (ASD). Given the secondary nature of this analysis (ClinicalTrials.gov and OSF), missing data is expected in the form of incomplete reporting of effect sizes, standard deviations, or sample sizes.

The primary goal is to minimize bias while maintaining statistical power, adhering to PRISMA guidelines and the project's Constitution Principle II (Verified Accuracy).

## 2. Missing Data Strategy

Missing data in this meta-analysis will be classified into three mechanisms:
1. **MCAR (Missing Completely at Random)**: Unlikely in this context, as missingness often correlates with study quality or sample size.
2. **MAR (Missing at Random)**: Missingness depends on observed variables (e.g., study year, sample size).
3. **MNAR (Missing Not at Random)**: Missingness depends on the unobserved effect size itself (e.g., studies with non-significant results failing to report standard deviations).

### 2.1 Assessment of Missingness
Before imputation, we will:
- Generate a missingness matrix to visualize patterns.
- Perform Little's MCAR test (if sufficient N) to distinguish MCAR from MAR.
- Compare characteristics of studies with complete data vs. those with missing data (e.g., sample size, publication year) using t-tests or chi-square tests.

### 2.2 Handling Methods Table

| Data Type | Missingness Pattern | Handling Method | Rationale |
|:--- |:--- |:--- |:--- |
| **Study Exclusion** | Missing primary outcome (social skill score) or inability to calculate effect size (missing N, mean, or SD) | **Exclude from Meta-Analysis** | Cannot impute effect sizes without raw summary statistics; excludes from pooled estimate. |
| **Standard Deviation (SD)** | Missing SD but reported SE, CI, or p-value | **Recover via Formula** | Convert reported statistics to SD using standard meta-analytic formulas (see Section 3). |
| **Standard Deviation (SD)** | Missing SD, SE, CI, and p-value | **Multiple Imputation (MI)** | Impute based on observed SDs from similar studies (matched by age, intervention type). |
| **Sample Size (N)** | Missing N for one arm | **Exclude** | Critical for weighting; cannot be reliably imputed. |
| **Covariates** | Missing moderator data (e.g., exact age mean, blinding status) | **Listwise Deletion** or **Indicator Variable** | If <5% missing, listwise deletion. If >5%, create a "Missing" category for categorical moderators. |
| **Effect Size (Hedges' g)** | Missing outcome data entirely | **Exclude** | No data to analyze. |

## 3. Imputation Method

When Standard Deviations (SD) are missing but other statistics are available, we will recover them using deterministic formulas. If SDs are entirely missing, we will use **Multiple Imputation by Chained Equations (MICE)**.

### 3.1 Deterministic Recovery Formulas
If the study reports the Standard Error (SE), Confidence Interval (CI), or p-value for the mean difference, we calculate SD as follows:

**From Standard Error (SE):**
$$ SD = SE \times \sqrt{n} $$
Where $n$ is the sample size of the respective group.

**From 95% Confidence Interval (CI):**
$$ SD = \frac{(CI_{upper} - CI_{lower}) \times \sqrt{n}}{3.92} $$
*(Assuming 95% CI corresponds to $1.96 \times SE$)*

**From t-statistic or p-value:**
$$ SE = \frac{Mean_{diff}}{t} $$
Then proceed to calculate SD from SE.

### 3.2 Multiple Imputation (MICE) for Missing SDs
If SDs are missing and cannot be recovered, we will perform MICE using the `statsmodels` or `scikit-learn` imputation pipelines.

**Model Specification:**
$$ SD_{ij} = \beta_0 + \beta_1(\text{SampleSize}_i) + \beta_2(\text{MeanAge}_i) + \beta_3(\text{InterventionType}_i) + \epsilon_i $$

**Procedure:**
1. Create $m=5$ imputed datasets.
2. Impute missing SDs using predictive mean matching (PMM) to ensure imputed values are within the plausible range of observed SDs.
3. Calculate Hedges' *g* for each imputed dataset.
4. Pool results using Rubin's Rules:
 $$ \bar{Q} = \frac{1}{m} \sum_{i=1}^{m} \hat{Q}_i $$
 $$ T = \bar{U} + \left( 1 + \frac{1}{m} \right) B $$
 Where $\bar{U}$ is the within-imputation variance and $B$ is the between-imputation variance.

## 4. Sensitivity Analysis

To ensure robustness, we will conduct sensitivity analyses to evaluate the impact of missing data assumptions.

### 4.1 Criteria for Sensitivity Analysis
- **Completeness Threshold**: If >20% of studies require imputation for SDs, a sensitivity analysis is mandatory.
- **Method Comparison**: Compare pooled effect sizes from:
 1. Complete-case analysis (Listwise deletion).
 2. Deterministic recovery only.
 3. Full Multiple Imputation.
- **Worst-Case Scenario**: Assume studies with missing SDs have larger variances (less precision) than observed studies, effectively down-weighting them.

### 4.2 Decision Rules
- **Robust**: If the pooled effect size (Hedges' *g*) and its 95% CI direction/significance remain consistent across all three methods above.
- **Sensitive**: If the conclusion (significant vs. non-significant) changes based on the imputation method. In this case, we will report the range of plausible effects and flag the result as "inconclusive due to missing data."

### 4.3 Publication Bias Check
We will compare the distribution of imputed effect sizes against observed ones. If imputed values cluster systematically at the null (g=0), it may indicate MNAR mechanisms (non-significant studies hiding missing data), requiring a selection model adjustment (e.g., Copas selection model) if N permits.

## 5. Software Implementation

- **Language**: Python 3.11+
- **Libraries**:
 - `pandas` for data manipulation.
 - `scikit-learn` (`IterativeImputer`) for MICE.
 - `statsmodels` for meta-analysis and Rubin's rule pooling.
- **Reproducibility**: All imputation models will be seeded (see `code/utils/config.py`) to ensure deterministic results.

## 6. References

1. Higgins JPT, Thomas J, Chandler J, et al. (eds). *Cochrane Handbook for Systematic Reviews of Interventions*. Version 6.4. 2023.
2. Rubin, D. B. (1987). *Multiple Imputation for Nonresponse in Surveys*. Wiley.
3. Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. *Journal of Statistical Software*, 36(3), 1-48.