# Linear Mixed-Effects Model (LMM) Methodology

## Overview

This document details the statistical methodology employed to detect and quantify **Statistical Power Drift** in replicated studies. The core analysis utilizes a Linear Mixed-Effects Model (LMM) to estimate the temporal decline in statistical power while controlling for heterogeneity across scientific fields and specific original studies.

## Research Question

Does statistical power in replication attempts exhibit a significant temporal decline over the years, after accounting for variations in effect size, sample size, and the nested structure of the data (replications within original studies within fields)?

## Statistical Model Specification

### Primary Hypothesis Test

The primary analysis compares two nested Linear Mixed-Effects Models to determine if including `year` as a fixed effect significantly improves model fit.

#### 1. Reduced Model (Null Hypothesis)

The reduced model assumes no temporal drift in power. It includes fixed effects for known determinants of power (effect size and sample size) and random intercepts for grouping factors.

$$ \text{power\_est}_{ij} = \beta_0 + \beta_1(\text{effect\_size}_{ij}) + \beta_2(\text{sample\_size}_{ij}) + u_{0j}^{field} + u_{0k}^{study} + \epsilon_{ij} $$

* **Fixed Effects**: `effect_size`, `sample_size`
* **Random Effects**: `(1 | field)`, `(1 | original_study_id)`
* **Assumption**: The coefficient for `year` is zero.

#### 2. Full Model (Alternative Hypothesis)

The full model introduces `year` as a fixed effect predictor. A significant negative coefficient for `year` indicates a drift in power over time.

$$ \text{power\_est}_{ij} = \beta_0 + \beta_1(\text{year}_{ij}) + \beta_2(\text{effect\_size}_{ij}) + \beta_3(\text{sample\_size}_{ij}) + u_{0j}^{field} + u_{0k}^{study} + \epsilon_{ij} $$

* **Fixed Effects**: `year`, `effect_size`, `sample_size`
* **Random Effects**: `(1 | field)`, `(1 | original_study_id)`
* **Target Parameter**: $\beta_1$ (Slope of `year`)

### Model Fitting and Estimation

* **Estimation Method**: Restricted Maximum Likelihood (REML) is used to estimate variance components, while Maximum Likelihood (ML) is used for the Likelihood Ratio Test (LRT) comparison.
* **Optimizer**: The model is fitted using the `lme4` algorithm (via `statsmodels` or `lmer` compatible backends) with convergence checks enabled.
* **Handling Zero Variance**: If a grouping factor (e.g., `field` or `original_study_id`) exhibits zero variance (single level), the model does not exclude the term. Instead, the variance component is constrained to a small epsilon (e.g., $10^{-6}$) to preserve the required model structure and prevent singular fit errors that would invalidate the comparison.

## Hypothesis Testing Strategy

### Likelihood Ratio Test (LRT)

To assess the significance of the `year` predictor, we perform a Likelihood Ratio Test comparing the Full Model against the Reduced Model.

* **Test Statistic**: $\chi^2 = -2(\ln L_{reduced} - \ln L_{full})$
* **Degrees of Freedom**: $df = df_{full} - df_{reduced}$ (typically 1, representing the `year` coefficient)
* **Null Hypothesis ($H_0$)**: The reduced model fits the data as well as the full model (i.e., $\beta_{year} = 0$).
* **Decision Rule**: Reject $H_0$ if $p < \alpha$ (typically $\alpha = 0.05$).

### Primary Drift Metric

The primary metric for drift is the **slope coefficient of `year` ($\beta_{year}$)** extracted from the **Full Model**.

* **Interpretation**: A negative $\beta_{year}$ indicates that for every unit increase in year, the estimated statistical power decreases by that magnitude, holding effect size and sample size constant.
* **Confidence Intervals**: Wald 95% confidence intervals are calculated for $\beta_{year}$ to quantify the precision of the estimate.

## Data Preprocessing

1. **Filtering**: Rows with missing `year`, `effect_size`, or `sample_size` are excluded.
2. **Validation**: Grouping variables (`field`, `original_study_id`) are validated for cardinality.
3. **Normalization**: Continuous predictors (`effect_size`, `sample_size`) are standardized to improve model convergence and interpretability (optional, depending on implementation).

## Robustness Checks

To ensure the validity of the LMM results, the following robustness checks are performed:

1. **Permutation Test**: Non-parametric shuffling of `year` labels to generate an empirical null distribution of the slope coefficient. This validates the parametric p-value assumption.
2. **Sensitivity Analysis**: Sweeping the significance threshold ($\alpha$) to determine if the drift conclusion is robust across different confidence levels.
3. **Cross-Field Aggregation**: Stratifying by `field` and using DerSimonian-Laird weighting to aggregate drift estimates, ensuring the result is not driven by a single discipline.

## Implementation Details

* **Library**: Python `statsmodels` (MixedLM) or `linearmodels`.
* **Input**: `data/derived/cleaned_data.csv`
* **Output**: `results/lmm_final_summary.json` containing `slope_year`, `se_year`, `ci_lower`, `ci_upper`, `p_value_lrt`.

## References

* Bates, D., et al. (2015). Fitting Linear Mixed-Effects Models Using lme4. *Journal of Statistical Software*.
* OSF Reproducibility Project: Psychology (2015). *Science*.
* Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*.
