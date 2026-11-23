# Research Plan

## Objective
Investigate the correlation between molecular descriptors and drug-likeness scores.

## Methodology
1. **Data Acquisition**: Download ChEMBL 33.
2. **Preprocessing**: Sanitize, deduplicate, filter, and calculate descriptors.
3. **Modeling**: Train Linear Regression and Random Forest.
4. **Evaluation**: Assess performance using RMSE and Pearson correlation.
5. **Visualization**: Generate plots for interpretation.

## Hypotheses
- H1: Molecular weight and logP are strong predictors of drug-likeness.
- H2: Non-linear models (Random Forest) outperform linear models.

## Expected Outcomes
- A clean dataset of molecular descriptors.
- Trained models with documented performance.
- Visualizations highlighting key features.
