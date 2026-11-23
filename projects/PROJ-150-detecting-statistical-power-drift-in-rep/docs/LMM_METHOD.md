# Linear Mixed-Effects Model Methodology for Statistical Power Drift Detection

## Overview

This document details the statistical methodology used to detect and quantify statistical power drift in replicated studies. The primary analysis employs a Linear Mixed-Effects Model (LMM) to estimate temporal trends while accounting for hierarchical data structures.

## Data Preparation

### Source Data
- **Dataset**: OSF Reproducibility Project (`osf/reproducibility_project`)
- **Primary File**: `data.csv`
- **Validation**: Title-token-overlap ≥ 0.7 verified against "OSF Reproducibility Project" metadata

### Preprocessing Steps
1. **Missing Data Handling**: Rows with missing `year`, `effect_size`, or `sample_size` are excluded with logged warnings.
2. **Power Estimation**: Post-hoc power (`power_est`) calculated using Cohen's d formula with observed effect sizes and sample sizes.
3. **Grouping Validation**: Random effect factors (`field`, `original_study_id`) checked for variance and cardinality. Factors with single levels are retained with fixed variance (ε = 1e-6) to preserve model structure.

## Statistical Model

### Primary Hypothesis Test

**Research Question**: Does statistical power exhibit a temporal decline over the years of publication?

**Model Specification**:

```
Full Model:
power_est ~ year + effect_size + sample_size + (1|field) + (1|original_study_id)

Reduced Model:
power_est ~ effect_size + sample_size + (1|field) + (1|original_study_id)
```

**Components**:
- **Fixed Effects**:
 - `year`: Primary predictor of interest (temporal trend)
 - `effect_size`: Control variable (Cohen's d)
 - `sample_size`: Control variable (N)
- **Random Effects**:
 - `(1|field)`: Random intercept for academic field
 - `(1|original_study_id)`: Random intercept for original study (replications nested within)

**Key Metric**:
- **Slope Year (`slope_year`)**: The coefficient for `year` in the Full Model. This represents the average change in statistical power per year, controlling for effect size and sample size.
- **Interpretation**: A negative `slope_year` indicates declining power over time; a positive value indicates increasing power.

### Model Fitting Strategy

1. **Pilot OLS Model**: `power_est ~ effect_size + sample_size`
 - Purpose: Capture deterministic relationship between power and its inputs
 - Output: Used to calculate residuals for exploratory visualization

2. **Residual Calculation**:
 ```
 power_residual = power_est - predicted_power (from Pilot OLS)
 ```
 - Purpose: Remove variance explained by effect size and sample size
 - Usage: Visualization and exploratory checks (NOT for primary inference)

3. **LMM Fitting**:
 - **Software**: `statsmodels` with REML estimation
 - **Convergence Handling**: If random effect variance is zero (single-level groups), variance is fixed to ε = 1e-6 rather than excluding the term (Constitution Principle VII)

### Significance Testing

**Likelihood-Ratio Test (LRT)**:
- **Null Hypothesis**: Reduced model fits as well as Full model (year coefficient = 0)
- **Test Statistic**: χ² = 2 × (logLik_full - logLik_reduced)
- **Degrees of Freedom**: Difference in number of parameters (df = 1)
- **Output**: `p_value_lrt`, `chi2_statistic`, `df_diff`

**Primary Inference**:
- The `slope_year` coefficient and its Wald confidence interval are the primary drift metrics
- LRT p-value validates whether adding `year` significantly improves model fit

## Robustness Checks

### Permutation Test (User Story 2)
- **Method**: Shuffle `year` labels while preserving other variables
- **Iterations**: 10,000 (or fallback to minimum if resource constraints)
- **Output**: Empirical p-value for drift slope
- **Consistency Check**: Compare parametric p-value with empirical p-value

### Sensitivity Analysis (User Story 2)
- **Method**: Sweep alpha thresholds (0.01 to 0.10)
- **Output**: Drift significance rates across thresholds
- **Conclusion**: Determine if drift is driven by specific alpha choice

### Cross-Field Aggregation (User Story 3)
- **Method**: DerSimonian-Laird inverse-variance weighting
- **Input**: Field-specific slope estimates from `power_residual ~ year` models
- **Output**: Aggregated drift estimate with heterogeneity adjustment (Q-statistic, τ²)

## Output Artifacts

### Primary Results
- `results/lmm_final_summary.json`: Contains `slope_year`, `se_year`, `ci_lower`, `ci_upper`, `p_value_lrt`, `chi2_statistic`, `df_diff`
- `results/permutation_pvalue.json`: Empirical p-value and iteration count
- `results/permutation_consistency.json`: Consistency check between parametric and empirical p-values
- `results/sensitivity_report.json`: Drift significance across alpha thresholds
- `results/aggregated_drift.json`: Cross-field aggregated drift estimate
- `results/comparison_aggregated_vs_lmm.json`: Comparison of aggregated vs. primary LMM slope

### Visualizations
- `results/power_drift_scatter.png`: Scatter plot of residual power vs. year with regression line
- `results/null_distribution_implied_power.csv`: Null distribution from input permutation

### Data Artifacts
- `data/derived/cleaned_data.csv`: Filtered dataset with no missing critical values
- `data/derived/grouping_validation.json`: Validation status for random effect factors
- `data/derived/pilot_ols_model.pkl`: Fitted pilot OLS model
- `data/derived/residuals.csv`: Residualized power for visualization
- `data/derived/field_slopes.csv`: Field-specific slope estimates

## Implementation Details

### Software Stack
- **Python**: 3.9+
- **Key Libraries**:
 - `pandas`: Data manipulation
 - `numpy`: Numerical operations
 - `scipy`: Statistical functions
 - `statsmodels`: Linear Mixed-Effects Models
 - `scikit-learn`: Model utilities
 - `matplotlib`/`seaborn`: Visualization
 - `huggingface_hub`: Dataset fetching

### Error Handling
- **Data Fetch**: Fails loudly on unreachable sources (no synthetic fallback)
- **Missing Columns**: Proceeds with available data (Spec Assumptions)
- **Missing Rows**: Skips with logged warning (row index and reason)
- **Zero Variance**: Fixes random effect variance to ε = 1e-6

## References

- Constitution Principle VII: Model structure must be preserved regardless of variance checks
- FR-002, FR-003, FR-009: LMM requirements for drift detection
- SC-001, SC-002, SC-003, SC-004: Validation and consistency scenarios
- OSF Reproducibility Project: Primary data source
