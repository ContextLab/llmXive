# Analysis Plan: Missing Data Handling and Imputation Strategies

This document outlines the statistical strategies for handling missing data in the meta-analysis of mindfulness interventions for social skills in children with Autism Spectrum Disorder (ASD). The plan adheres to PRISMA guidelines and addresses the specific constraints of secondary analysis of registry data.

## 1. Missing Data Strategy

Missing data in this meta-analysis primarily arises from:
1. **Registry Metadata Gaps**: ClinicalTrials.gov or OSF records may lack specific fields (e.g., exact age range, specific outcome measures, rater blinding status).
2. **Outcome Reporting**: Studies may report aggregate statistics (means/SDs) for some outcomes but not others, or report only p-values.
3. **Follow-up Attrition**: Loss to follow-up in longitudinal arms.

The following table details the handling methods for each data type:

| Data Element | Missingness Mechanism Assumption | Handling Strategy | Criteria for Exclusion |
|:--- |:--- |:--- |:--- |
| **Study Inclusion Criteria** (Age, Diagnosis, Outcomes) | Missing Not At Random (MNAR) | **Strict Exclusion**. If mandatory inclusion fields (Age 6-12, ASD diagnosis, Social Outcome) are missing and cannot be inferred from the abstract, the study is excluded. | Abstract also missing or insufficient to verify criteria. |
| **Rater Blinding Status** | Missing At Random (MAR) | **Sensitivity Analysis**. Studies are categorized as "Blinded", "Unblinded", or "Unknown". The primary analysis includes all. A secondary analysis excludes "Unknown" to test bias impact. | N/A |
| **Effect Size Components** (Mean, SD, N) | Missing At Random (MAR) | **Imputation or Estimation**. If SD is missing but SE or CI is provided, SD is calculated. If N is missing for a subgroup, it is estimated from total N if proportions are known. | No convertible statistic available; study excluded from quantitative synthesis. |
| **Follow-up Duration** | Missing At Random (MAR) | **Categorical Imputation**. If exact duration is missing, the study is assigned to the "Not Reported" category for subgroup analysis. | N/A |
| **Intervention Components** | Missing At Random (MAR) | **Text Extraction**. If not explicitly listed, the 'description' and 'abstract' fields are scanned for keywords (breathing, body scan, etc.). | No keywords found; assigned "None" or "Unclassified". |

## 2. Imputation Method

When effect size components are partially missing, we apply the following deterministic transformations to recover the missing values before calculating Hedges' *g*. These methods are preferred over stochastic imputation for meta-analysis to preserve the integrity of the variance estimates.

### 2.1. Standard Deviation (SD) Imputation

If the Standard Deviation ($SD$) is missing but the Standard Error ($SE$) or Confidence Interval ($CI$) is reported, $SD$ is calculated as follows:

**From Standard Error:**
$$ SD = SE \times \sqrt{N} $$
Where $N$ is the sample size of the respective group (treatment or control).

**From 95% Confidence Interval:**
$$ SD = \frac{CI_{upper} - CI_{lower}}{2 \times 1.96} \times \sqrt{N} $$
*Note: If the reported CI is not 95%, the multiplier $1.96$ is adjusted to the appropriate $t$-value or $z$-value based on the reported degrees of freedom.*

### 2.2. Hedges' *g* Calculation with Small-Sample Correction

Once means ($M$), standard deviations ($SD$), and sample sizes ($N$) are established for treatment ($T$) and control ($C$) groups, the pooled standard deviation ($SD_{pooled}$) is calculated:

$$ SD_{pooled} = \sqrt{\frac{(N_T - 1)SD_T^2 + (N_C - 1)SD_C^2}{N_T + N_C - 2}} $$

The raw effect size (Cohen's *d*) is:
$$ d = \frac{M_T - M_C}{SD_{pooled}} $$

To correct for small-sample bias, Hedges' *g* is computed using the correction factor $J$:
$$ g = J \times d $$
$$ J = 1 - \frac{3}{4(N_T + N_C) - 9} $$

### 2.3. Variance of Hedges' *g*

The sampling variance ($v_g$) required for the random-effects model is calculated as:
$$ v_g = \frac{N_T + N_C}{N_T N_C} + \frac{g^2}{2(N_T + N_C)} $$

## 3. Sensitivity Analysis

To assess the robustness of the meta-analytic results against missing data assumptions and potential bias, the following sensitivity analyses will be conducted:

### 3.1. Blinding Bias Sensitivity
**Criteria**: Compare the pooled effect size ($g$) and heterogeneity ($I^2$) between:
1. **Full Set**: All included studies (treating "Unknown" blinding as a separate subgroup).
2. **Restricted Set**: Only studies with explicitly reported "Blinded" raters.
3. **Exclusion Set**: Studies with "Unblinded" or "Unknown" raters are removed.

**Decision Rule**: If the pooled effect size in the "Restricted Set" differs by more than 0.2 standard deviations from the "Full Set", or if the direction of the effect changes, the result is considered sensitive to rater bias.

### 3.2. Imputation Method Sensitivity
**Criteria**: For studies where SD was imputed from CI or SE:
1. **Primary**: Include imputed studies.
2. **Secondary**: Exclude all studies requiring SD imputation.

**Decision Rule**: If the exclusion of imputed studies significantly alters the heterogeneity ($I^2$) or statistical significance ($p < 0.05$) of the pooled effect, the imputation strategy is flagged as a limiting factor.

### 3.3. Missing Outcome Sensitivity
**Criteria**: Compare results when studies with missing "Social Skill" specific outcome measures (relying on proxy measures) are included vs. excluded.
**Decision Rule**: If the effect size magnitude changes by >15%, the definition of "social skill outcome" is refined in the protocol.

## 4. Documentation of Missing Data

All decisions regarding exclusion due to missing mandatory fields or imputation of effect size components will be logged in `data/raw/excluded_studies.log` (JSONL format) and summarized in the `docs/results.md` report. The number of studies excluded for each reason will be reported in the PRISMA flow diagram description.