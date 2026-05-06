---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

**Field**: materials science

## Research question

How does elemental composition determine the shear modulus of bulk metallic glasses, and which compositional descriptors (atomic size mismatch, mixing enthalpy, valence electron concentration) most strongly govern this relationship across different alloy families?

## Motivation

Bulk metallic glasses (BMGs) possess exceptional mechanical properties that make them valuable for structural applications, yet their composition-property relationships remain poorly understood due to the complexity of multi-component systems. A quantitative model linking composition to shear modulus would enable faster discovery of BMGs with tailored stiffness, reducing the trial-and-error burden in alloy development. This project addresses a gap in the existing literature where compositional predictors for mechanical properties have not been systematically validated across diverse BMG families.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: "bulk metallic glasses shear modulus composition", "BMG mechanical properties machine learning", and "metallic glass elastic modulus prediction". Retrieved 3 results total, with only 1 directly addressing BMGs.

### What is known

- [Bulk Metallic Glasses: At the Cutting Edge of Metals Research (2007)](https://doi.org/10.1557/mrs2007.121) — This review establishes that BMG composition-property relationships are complex and that elastic moduli correlate with packing density and atomic size mismatch, but does not provide quantitative predictive models.

### What is NOT known

No published work has systematically quantified which compositional descriptors (beyond atomic size mismatch) most strongly predict shear modulus across multiple BMG families using modern machine learning techniques. Existing reviews from 2007 predate the availability of larger BMG datasets and contemporary regression methods that could reveal non-linear composition-property relationships.

### Why this gap matters

Materials scientists developing new BMG alloys would benefit from a validated compositional predictor to screen candidate formulations before synthesis, potentially reducing development costs and time. Filling this gap would provide a benchmark for data-driven materials design in the metallic glass community and establish whether simple descriptors suffice or if more complex feature engineering is required.

### How this project addresses the gap

This project will compile public BMG composition-shear modulus datasets, compute standard compositional descriptors (atomic size mismatch, mixing enthalpy, valence electron concentration), and train multiple regression models to quantify which features most strongly predict shear modulus. The model performance and feature importance analysis will directly measure whether current descriptors capture the composition-property relationship or if gaps remain in our understanding.

## Expected results

We expect to find that atomic size mismatch and mixing enthalpy together explain ≥60% of shear modulus variance across BMG families, with valence electron concentration providing secondary predictive power. Model performance will be measured using R² and mean absolute error on a held-out test set, with statistical significance assessed via permutation testing on feature importance rankings.

## Methodology sketch

- **Data acquisition**: Download BMG composition and shear modulus data from the Materials Project (https://materialsproject.org) and published BMG databases (e.g., Inoue's BMG compilation, DOI: 10.1016/j.msea.2004.07.033)
- **Data cleaning**: Filter for bulk metallic glasses (exclude crystalline alloys), remove entries with missing shear modulus values, standardize composition notation to atomic percent
- **Feature engineering**: Compute compositional descriptors: (1) atomic size mismatch (δ), (2) mixing enthalpy (ΔHmix), (3) valence electron concentration (VEC), (4) electronegativity difference, using elemental properties from the Mendeleev database
- **Dataset split**: Partition data into 80% training / 20% test stratified by alloy family (Zr-based, Cu-based, Mg-based, etc.)
- **Model training**: Fit three regression models: (1) linear regression, (2) random forest regressor, (3) gradient boosting regressor using scikit-learn
- **Hyperparameter tuning**: Grid search over 5-fold cross-validation for each model, limited to ≤50 parameter combinations to stay within GHA memory constraints
- **Performance evaluation**: Report R², mean absolute error (MAE), and root mean squared error (RMSE) on held-out test set; compare models using paired t-test on cross-validation folds
- **Feature importance analysis**: Extract feature importances from tree-based models; perform permutation importance testing (100 permutations) to assess statistical significance of each descriptor
- **Visualization**: Generate partial dependence plots for top 3 features and correlation heatmap of descriptors vs. shear modulus
- **Reproducibility**: Save all code, processed datasets, and model artifacts in a single Python script with pinned dependencies in requirements.txt

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: No close match found (first BMG composition-property ML project in this field).
- Verdict: NOT a duplicate
