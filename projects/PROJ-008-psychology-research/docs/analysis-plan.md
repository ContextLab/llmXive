# Analysis Plan: Missing Data Handling and Imputation Strategies

**Project**: PROJ-008-psychology-research
**Study**: Mindfulness Components and Delivery Formats in ASD Social Skills
**Date**: 2026-04-29
**Version**: 1.0

## 1. Overview

This document details the protocols for handling missing data in the meta-analysis of mindfulness-based interventions for social skills in children with Autism Spectrum Disorder (ASD). Given that this study relies on secondary analysis of data from ClinicalTrials.gov and OSF (Constitution Principle VI), missing data will primarily arise from:
1. **Item Non-Response**: Missing means, standard deviations, or sample sizes in reported study results.
2. **Unit Non-Response**: Studies that meet inclusion criteria but lack sufficient data to calculate effect sizes.
3. **Attrition**: Participant dropout rates reported in the included studies.

All handling strategies adhere to the **Constitution Principle V (Fail Fast)**: if data is insufficient to proceed with a valid statistical estimate, the study is excluded from that specific analysis rather than imputed blindly.

## 2. Missing Data Mechanisms Assessment

Before applying any imputation, the mechanism of missingness will be assessed where possible:
- **Missing Completely at Random (MCAR)**: Likely for studies with incomplete reporting due to formatting or transcription errors.
- **Missing at Random (MAR)**: Possible if missingness correlates with observed variables (e.g., older studies reporting fewer covariates).
- **Missing Not at Random (MNAR)**: Possible if studies with non-significant results are less likely to report detailed standard deviations.

**Diagnostic Check**: For variables with >5% missingness, a Little's MCAR test will be conducted if the dataset size (N) permits (N ≥ 30). If N < 30 (common in meta-analyses of niche interventions), we will assume MAR and proceed with conservative imputation or exclusion.

## 3. Strategies by Data Type

### 3.1. Missing Means and Standard Deviations (Primary Outcomes)

The calculation of Hedges' *g* requires the mean ($M$), standard deviation ($SD$), and sample size ($n$) for both intervention and control groups at pre- and post-treatment timepoints.

**Strategy A: Contact Authors**
- If primary data is missing but the study is otherwise eligible, a standardized inquiry will be sent to the corresponding author.
- **Timeout**: If no response is received within 14 days, the study moves to Strategy B.

**Strategy B: Derivation from Statistics**
- If $SE$ (Standard Error) or $CI$ (Confidence Interval) is reported, $SD$ will be reconstructed using standard formulas:
 $$SD = SE \times \sqrt{n}$$
 $$SD = \frac{Upper\ Limit - Lower\ Limit}{2 \times t_{critical}} \times \sqrt{n}$$
- If $F$-statistics or $t$-statistics are reported for the group difference, $SD$ can be back-calculated from the effect size estimate.

**Strategy C: Imputation from Correlated Studies**
- If $SD$ is missing but $M$ is present, we will impute the $SD$ using the **pooled standard deviation** of all other studies in the dataset with similar characteristics (same age group, same outcome measure, same intervention type).
- **Formula**: $SD_{imputed} = SD_{pooled\_subgroup}$
- **Constraint**: This is only applied if the subgroup size $k \geq 3$. If $k < 3$, the study is excluded from the quantitative synthesis for that specific outcome.

**Strategy D: Exclusion**
- If means or sample sizes are missing and cannot be derived or imputed, the study is excluded from the meta-analysis for that specific outcome.
- **Documentation**: All excluded studies are logged in `data/raw/excluded_studies.log` with the reason code `MISSING_DATA`.

### 3.2. Missing Sample Sizes (Attrition)

- **Intention-to-Treat (ITT) vs. Per-Protocol**: We will prioritize ITT data ($n$ at baseline) if reported. If only Per-Protocol data is available, we will use it but flag the study for sensitivity analysis.
- **Attrition Rate Calculation**: If dropout rates are missing, we will assume 0% attrition for the primary analysis but conduct a sensitivity analysis assuming a 20% attrition rate (conservative estimate for pediatric ASD trials) to assess robustness.

### 3.3. Missing Follow-up Data

- If follow-up data (3-month or 6-month) is missing for a study that has post-treatment data, the study contributes to the post-treatment analysis but is excluded from the follow-up subgroup analysis.
- No imputation will be performed for follow-up data to avoid introducing bias regarding long-term efficacy.

## 4. Imputation Algorithms

All imputation logic is implemented in `code/data/cleaner.py` (Task T016) and `code/analysis/effect_sizes.py` (Task T024).

### 4.1. Single Imputation for SD (Pooled Mean)
```python
def impute_sd_from_pooled(df, group_col, sd_col):
 """
 Replaces NaN in sd_col with the mean SD of the same group_col category.
 Only applied if category count >= 3.
 """
 # Implementation details in code/data/cleaner.py
 pass
```

### 4.2. Sensitivity Analysis (Multiple Imputation)
- For the primary report, we will use the single imputation strategy (Strategy C) to maintain transparency.
- A sensitivity analysis using **Multiple Imputation by Chained Equations (MICE)** will be prepared if $N \geq 10$ studies have missing SDs. This will use the `statsmodels` or `sklearn.impute` libraries.
- If $N < 10$, MICE is suppressed (per FR-014) to prevent overfitting, and the single imputation or exclusion strategy is used.

## 5. Sensitivity Analysis Plan

To ensure the robustness of results against missing data assumptions:

1. **Complete Case Analysis**: Run meta-analysis only on studies with zero missing data.
2. **Imputed Dataset Analysis**: Run meta-analysis using the imputed values described in Section 3.
3. **Worst-Case Scenario**: Assume missing SDs are 1.5x the pooled SD (increasing variance, reducing effect size significance).
4. **Comparison**: If the direction of the pooled effect size changes or statistical significance is lost between Complete Case and Imputed analyses, the result will be reported as "Sensitive to missing data handling" in `docs/results.md`.

## 6. Reporting Standards

- **PRISMA Flow Diagram**: Will explicitly state the number of studies excluded due to missing data.
- **Table of Characteristics**: Will include a column indicating "Data Completeness" (e.g., "Full", "Imputed SD", "Excluded").
- **Code Transparency**: All imputation logic and flags will be visible in the `data/processed/cleaned_studies.csv` via a `data_quality_flag` column.

## 7. Software Implementation

- **Imputation Logic**: `code/data/cleaner.py` (Task T016)
- **Effect Size Calculation**: `code/analysis/effect_sizes.py` (Task T024)
- **Sensitivity Checks**: `code/analysis/meta_analysis.py` (Task T025)
- **Logging**: All imputation events are logged via `utils.logging.log_event` with `event_type='MISSING_DATA_HANDLING'`.

---
*This plan is subject to update if the actual data from ClinicalTrials.gov and OSF reveals patterns of missingness not anticipated here.*