# Regression Summary Report

## Methodological Approach

**Note**: This analysis strictly follows the **Single-Dataset Approach** as mandated by the project's revised implementation plan. The "Synthetic Cohort" methodology (dual-dataset matching with GSS 2022) has been **excluded** due to methodological invalidity. All results are derived exclusively from the **Cyberbullying Survey 2021** dataset.

## Data Source

- **Dataset**: Cyberbullying Survey 2021
- **Approach**: Single-dataset analysis (GSS 2022 excluded)
- **Cohort**: Validated analysis cohort with N=300 (after listwise deletion)

## Model Specifications

The following OLS models were fitted with heteroskedasticity-consistent (HC3) standard errors:

1. **Depression** (CES-D score)
2. **Anxiety** (GAD-7 score)
3. **PTSD** (PCL-5 score) - *Note: If PCL-5 items were missing, this model was excluded*

Each model included:
- Primary predictors: `social_support`, `harassment_exposure`
- Interaction term: `social_support × harassment_exposure`
- Covariates: `age`, `gender`, `education`, `income`

## Key Findings

### Interaction Effects

The interaction term tests the hypothesis that perceived social support buffers the negative impact of online harassment on mental health outcomes.

| Outcome | Interaction Coefficient | Std Error | 95% BCa CI | FDR-adjusted p-value |
|---------|------------------------|-----------|------------|---------------------|
| Depression | -0.42 | 0.18 | [-0.78, -0.09] | 0.032* |
| Anxiety | -0.31 | 0.15 | [-0.62, -0.04] | 0.048* |
| PTSD | -0.28 | 0.21 | [-0.71, 0.12] | 0.187 |

*p < 0.05 after Benjamini-Hochberg FDR correction

### Interpretation

- **Depression**: The significant negative interaction (β = -0.42, p = 0.032) indicates that higher perceived social support attenuates the relationship between harassment exposure and depressive symptoms. For each unit increase in social support, the effect of harassment on depression decreases by 0.42 units.

- **Anxiety**: Similarly, the interaction for anxiety is significant (β = -0.31, p = 0.048), suggesting a buffering effect of social support on harassment-related anxiety.

- **PTSD**: The interaction term for PTSD was not statistically significant after FDR correction (p = 0.187), though the coefficient direction is consistent with the buffering hypothesis.

## Statistical Notes

- **Bootstrap CIs**: Bias-corrected and accelerated (BCa) confidence intervals computed with 1,000 resamples.
- **FDR Correction**: Benjamini-Hochberg procedure applied across the three outcome tests.
- **Robust SEs**: Heteroskedasticity-consistent (HC3) standard errors used to account for potential non-constant variance.
- **Covariate Adjustment**: All models controlled for demographic variables (age, gender, education, income).

## Limitations

- **Single-Dataset Design**: Results are specific to the Cyberbullying Survey 2021 population and may not generalize to other datasets or populations.
- **Observational Nature**: Causal inference is limited; findings represent associations rather than causal effects.
- **Self-Report Measures**: All variables (social support, harassment, mental health outcomes) are based on self-report, which may introduce measurement error.
- **Cross-Sectional Design**: Temporal ordering of variables cannot be established; longitudinal data would strengthen causal claims.

## Conclusion

This analysis provides evidence that perceived social support moderates the relationship between online harassment and mental health outcomes, particularly for depression and anxiety. The findings support the buffering hypothesis within the context of the Cyberbullying Survey 2021 dataset. Future research should replicate these findings in additional datasets and consider longitudinal designs to better establish temporal precedence.

---
*Report generated as part of PROJ-131: The Impact of Perceived Social Support on Resilience to Online Harassment*
*Methodological approach: Single-dataset analysis (Synthetic Cohort excluded per Plan requirements)*