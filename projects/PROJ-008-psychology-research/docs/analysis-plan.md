# Analysis Plan: Missing Data Handling and Imputation Strategies

**Project**: PROJ-008-psychology-research
**Study Focus**: Mindfulness Components and Delivery Formats in ASD Social Skills
**Date**: 2026-04-29
**Version**: 1.0

## 1. Introduction

This document outlines the statistical strategies for handling missing data in the systematic review and meta-analysis of mindfulness-based interventions for children with Autism Spectrum Disorder (ASD). The analysis relies on secondary data from ClinicalTrials.gov and OSF. While registry data is generally structured, missingness may occur in outcome means, standard deviations, or subgroup counts required for effect size calculation.

## 2. Missing Data Strategy

We adopt a tiered approach to missing data, prioritizing the recovery of raw statistics before resorting to estimation. The strategy is defined by the mechanism of missingness and the availability of auxiliary information.

| Missing Data Scenario | Mechanism | Method | Justification |
|:--- |:--- |:--- |:--- |
| **Outcome Mean/SD Missing** | MCAR (Random) | Contact study authors via registry email; search supplementary materials. | Primary recovery method; preserves raw data integrity. |
| **N (Sample Size) Missing** | MAR (Dependent on reported stats) | Impute from total N if group allocation ratio is known (e.g., 1:1). | Standard practice in meta-analysis when randomization is balanced. |
| **SD Missing, CI Reported** | MCAR | Convert Confidence Intervals (CI) to SD using standard formulas. | CI is often reported when SD is omitted; mathematically reversible. |
| **SD Missing, SE Reported** | MCAR | Convert Standard Error (SE) to SD using $SD = SE \times \sqrt{N}$. | Direct algebraic transformation. |
| **SD Missing, p-value Reported** | MCAR | Back-calculate t-statistic or z-score from p-value, then derive SD. | Allows inclusion of studies otherwise excluded due to incomplete stats. |
| **Complete Outcome Missing** | MNAR (Missing Not At Random) | Exclude from quantitative synthesis; include in narrative synthesis. | Imputation of entirely missing outcomes introduces unacceptable bias. |

## 3. Imputation Method

When direct contact fails and auxiliary statistics (CI, SE, p-value) are available, the following formulas will be applied to recover the Standard Deviation ($SD$) and subsequently calculate Hedges' $g$.

### 3.1. Deriving SD from Confidence Intervals
If the 95% Confidence Interval ($CI_{lower}, CI_{upper}$) is reported for a group mean:
$$ SE = \frac{CI_{upper} - CI_{lower}}{2 \times 1.96} $$
$$ SD = SE \times \sqrt{N} $$
*Note: If the CI is not 95%, the Z-score (1.96) must be adjusted to the corresponding quantile.*

### 3.2. Deriving SD from Standard Error
If the Standard Error ($SE$) is explicitly reported:
$$ SD = SE \times \sqrt{N} $$

### 3.3. Deriving SD from p-values
If only a p-value and group means ($M_1, M_2$) are available:
1. Calculate the t-statistic ($t$) from the p-value (assuming degrees of freedom $df = N_1 + N_2 - 2$).
2. Calculate the pooled standard error ($SE_{diff}$):
 $$ SE_{diff} = \frac{M_1 - M_2}{t} $$
3. Derive the pooled standard deviation ($SD_{pooled}$):
 $$ SD_{pooled} = SE_{diff} \times \sqrt{\frac{1}{N_1} + \frac{1}{N_2}} $$

### 3.4. Hedges' g Calculation
Once $SD_{pooled}$ is recovered or observed, the effect size is calculated as:
$$ g = J \times \frac{M_1 - M_2}{SD_{pooled}} $$
Where $J$ is the small-sample correction factor:
$$ J = 1 - \frac{3}{4(N_1 + N_2) - 9} $$

## 4. Sensitivity Analysis

To assess the robustness of the meta-analysis results to missing data assumptions, the following sensitivity analyses will be conducted:

1. **Best-Worst Case Scenario**:
 * **Best Case**: Missing outcomes in the treatment group are assumed to be favorable (mean = max observed), and missing in control are unfavorable.
 * **Worst Case**: Reverse the assumption.
 * **Criteria**: If the pooled effect size direction changes or significance is lost ($p > 0.05$) under either scenario, the result is deemed sensitive to missing data assumptions.

2. **Imputation vs. Complete Case Comparison**:
 * Run the meta-analysis twice: once including studies with imputed SDs and once excluding them.
 * **Criteria**: Calculate the percentage change in the pooled effect size ($\% \Delta$). If $\% \Delta > 10\%$, the imputation strategy significantly influences the conclusion, and the result must be reported with a cautionary note.

3. **Heterogeneity Assessment**:
 * Compare $I^2$ statistics between the complete-case model and the imputed model.
 * **Criteria**: A substantial increase in $I^2$ in the imputed model suggests that the imputed values introduce unexplained variance, potentially indicating that the missingness is not random.

## 5. Implementation in Pipeline

The `code/analysis/effect_sizes.py` module will implement the conversion logic described in Section 3. The `code/analysis/meta_analysis.py` module will execute the sensitivity checks described in Section 4. All imputation steps will be logged in `data/processed/imputation_log.json` to ensure full reproducibility and auditability, satisfying Constitution Principle V.