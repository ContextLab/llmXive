---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

**Field**: materials science

## Research question

Can machine learning regression models accurately predict the diffusion coefficient of carbon in body-centered cubic (BCC) metals using only compositional data from public materials databases?

## Motivation

Carbon diffusion governs critical materials processes including carburization, steel hardening, and high-temperature degradation in BCC alloys. Accurate prediction remains challenging due to complex compositional interactions. This project addresses the gap between traditional physics-based diffusion models and data-driven approaches that could enable rapid materials screening without expensive experiments.

## Related work

- [High-entropy ceramics: Present status, challenges, and a look forward (2021)](https://doi.org/10.1007/s40145-021-0477-y) — Provides context on multi-element materials and compositional complexity relevant to diffusion modeling.

*Note: Limited literature search results available; additional targeted queries recommended for comprehensive background.*

## Expected results

We expect random forest or gradient boosting models to achieve R² > 0.65 on held-out test data when trained on compositional features. Feature importance analysis should reveal dominant alloying elements affecting carbon mobility. A baseline physics-informed model will provide comparison for machine learning performance assessment.

## Methodology sketch

- **Data acquisition**: Download carbon diffusion coefficients in BCC metals from Materials Project (https://materialsproject.org) and NIST Materials Data Repository (https://doi.org/10.18434/T4M88P); collect alloy compositions from OpenKIM (https://openkim.org).
- **Data preprocessing**: Filter for BCC crystal structures only; normalize composition to atomic fractions; handle missing values via mean imputation for <5% missing entries.
- **Feature engineering**: Generate compositional descriptors (average atomic radius, electronegativity variance, valence electron concentration) using pymatgen (https://pymatgen.org).
- **Model training**: Split data 80/20 train/test; train random forest, XGBoost, and linear regression baselines using scikit-learn within 30-minute job chunks.
- **Hyperparameter tuning**: Grid search over 10 combinations per model (trees: 50-200, depth: 3-10, learning rate: 0.01-0.3); limit to 1 hour total computation.
- **Evaluation metrics**: Compute R², RMSE, and MAE on test set; use 5-fold cross-validation to assess generalization stability.
- **Statistical validation**: Apply paired t-test (α=0.05) to compare model performances; report confidence intervals for R² values.
- **Feature importance**: Extract SHAP values to identify compositional drivers; visualize top 5 features with bar plots.
- **Output**: Generate CSV predictions, JSON model artifacts, and PNG figures for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None in corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
