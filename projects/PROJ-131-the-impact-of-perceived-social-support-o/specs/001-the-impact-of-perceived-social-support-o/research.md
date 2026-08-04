# Research: The Impact of Perceived Social Support on Resilience to Online Harassment

**Date**: 2024-01-15
**Project ID**: PROJ-131
**Status**: Draft

## Methodological Approach

This study strictly follows the **Single-Dataset Analysis** approach mandated by the project plan.
The analysis utilizes the **Cyberbullying Survey 2021** dataset exclusively.

**Note on Synthetic Cohort**: The original specification's requirement for a "Synthetic Cohort" matching
Cyberbullying Survey data with GSS 2022 data has been **DEPRECATED** as methodologically invalid.
This approach is excluded from the current implementation to prevent confounding by dataset source.

## Research Questions

1. Does perceived social support moderate the relationship between online harassment exposure and mental health outcomes?
2. What is the magnitude of the buffering effect of social support on depression, anxiety, and PTSD scores?

## Data Sources

- **Primary Dataset**: Cyberbullying Survey 2021 (Single source)
- **Excluded Dataset**: GSS 2022 (Excluded per Plan's Revised Approach)

## Analysis Plan

1. **Data Ingestion**: Load and validate the Cyberbullying Survey 2021.
2. **Preprocessing**: Apply MICE imputation for missing values in predictor variables.
3. **Cohort Construction**: Filter for valid variance in harassment exposure and sufficient sample size.
4. **Modeling**: Fit OLS models with interaction terms (Social Support × Harassment Exposure) for Depression, Anxiety, and PTSD.
5. **Inference**: Compute bias-corrected accelerated (BCa) bootstrap confidence intervals and apply Benjamini-Hochberg FDR correction.
6. **Sensitivity Analysis**: Test robustness using continuous harassment severity and platform stratification.

## Limitations

- Findings are associational; causal inference is limited by the observational nature of the data.
- The exclusion of the GSS 2022 dataset limits generalizability to the broader population but ensures internal validity of the interaction effect estimates.

## Next Steps

- Execute the full pipeline to generate `data/results/regression_summary.md`.
- Validate results against the reproducibility audit.
- Finalize interpretation of interaction coefficients.