---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

**Field**: materials science

## Research question

Can machine learning regression models trained on elemental composition and thermodynamic descriptors accurately predict high-temperature oxidation weight gain in nickel-based superalloys using publicly available materials data?

## Motivation

Experimental characterization of oxidation resistance is slow and resource-intensive, creating a bottleneck in alloy development for aerospace and power generation. This research addresses the gap in accessible, predictive computational tools by leveraging existing public datasets to screen alloy compositions before physical testing.

## Related work

- [Fundamentals and advances in magnesium alloy corrosion (2017)](https://doi.org/10.1016/j.pmatsci.2017.04.011) — Establishes fundamental relationships between alloy composition and corrosion/oxidation behavior, providing mechanistic context for alloying effects despite the focus on magnesium rather than nickel.

## Expected results

We expect Gaussian Process Regression and Random Forest models to achieve a coefficient of determination (R²) greater than 0.65 on held-out test sets. Feature importance analysis will identify specific alloying elements (e.g., Chromium, Aluminum) that most significantly influence oxidation rate, confirming known metallurgical trends.

## Methodology sketch

- **Data Acquisition**: Download tabular datasets containing alloy composition and oxidation weight gain from the NIST Materials Data Repository (https://www.nist.gov/mml/mmd/material-data-repository) or Zenodo (search query: "superalloy oxidation data").
- **Feature Engineering**: Construct input vectors including elemental weight percentages, atomic radii, and electronegativity values sourced from standard periodic table databases (e.g., WebElements API).
- **Thermodynamic Descriptors**: Calculate formation enthalpies for potential oxide scales using public thermodynamic databases (e.g., Thermo-Calc public samples or OpenCalphad) to augment composition features.
- **Model Implementation**: Train Random Forest and Gaussian Process Regressor models using `scikit-learn` (CPU-only, memory-efficient).
- **Validation**: Perform 5-fold cross-validation to assess generalization; calculate Root Mean Squared Error (RMSE) and R² metrics.
- **Compute Constraints**: All steps fit within 7 GB RAM and 6-hour runtime limits; no GPU acceleration required.
- **Analysis**: Generate SHAP (SHapley Additive exPlanations) plots to interpret feature contributions to predicted oxidation rates.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None (no existing ideas to compare).
- Verdict: NOT a duplicate
