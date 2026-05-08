---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Field**: materials science

## Research question

How does the compositional diversity of high-entropy alloys (specifically the number and relative proportions of principal elements) influence their elastic modulus (Young's modulus, shear modulus, and Poisson's ratio)?

## Motivation

High-entropy alloys (HEAs) represent a vast compositional space where traditional alloy design rules break down. Understanding the fundamental relationship between alloying composition and elastic stiffness would enable more targeted materials selection for structural applications. Currently, most HEA property predictions focus on formation stability or hardness, leaving elastic modulus as an underexplored but critical mechanical property for engineering design.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: "high-entropy alloy elastic modulus prediction machine learning", "HEA Young's modulus composition relationship", and "high-entropy alloy mechanical properties dataset". Retrieved 2 relevant papers from the literature block.

### What is known

- [High-entropy high-hardness metal carbides discovered by entropy descriptors (2018)](https://doi.org/10.1038/s41467-018-07160-7) — Establishes that entropy-based descriptors can predict mechanical properties (hardness) in high-entropy materials, demonstrating ML feasibility for property prediction.
- [High-entropy ceramics: Present status, challenges, and a look forward (2021)](https://doi.org/10.1007/s40145-021-0477-y) — Reviews high-entropy material systems broadly but focuses on ceramics rather than metallic alloys.

### What is NOT known

No published work has systematically quantified the relationship between compositional features (element counts, mixing enthalpies, atomic size mismatch) and elastic modulus specifically for metallic high-entropy alloys. Existing studies focus on formation energy, hardness, or stability rather than elastic stiffness properties.

### Why this gap matters

Elastic modulus is a primary design constraint for structural applications requiring specific stiffness-to-weight ratios. Without predictive models for elastic properties, HEA screening for aerospace, automotive, and energy applications remains incomplete. Filling this gap would enable computational pre-screening before expensive synthesis and characterization.

### How this project addresses the gap

This project will train and validate ML models on public HEA datasets with measured elastic moduli, explicitly testing which compositional descriptors (atomic percentages, mixing enthalpies, electronegativity variance) most strongly predict Young's modulus, shear modulus, and Poisson's ratio. The model performance and feature importance analysis will directly quantify previously unknown composition-property relationships.

## Expected results

We expect to identify 2-3 compositional descriptors that explain >50% of variance in elastic modulus across the HEA dataset. A null result (R² < 0.3) would indicate that elastic modulus depends on microstructural factors beyond bulk composition alone, constraining ML-based materials design approaches. Either outcome provides actionable insight for HEA development.

## Methodology sketch

- **Data collection**: Download HEA composition and property data from Materials Project (https://next-gen.materialsproject.org) and Open Quantum Materials Database (OQMD) using their public APIs; filter for alloys with ≥5 principal elements and reported elastic constants.
- **Feature engineering**: Compute compositional descriptors per sample: atomic percentages of each element, mixing enthalpy (using Miedema's model), atomic radius variance, electronegativity variance, valence electron concentration, and entropy of mixing.
- **Dataset assembly**: Create a tabular dataset with ~500-1000 HEA samples (targeted based on available public data); split 70/15/15 for train/validation/test with stratification by element count.
- **Model training**: Fit 3 regression models (Random Forest, Gradient Boosting, ElasticNet) using scikit-learn; perform 5-fold cross-validation on training set with hyperparameter grid (max_depth: 3-10, n_estimators: 50-200).
- **Model evaluation**: Compute R², RMSE, and MAE on held-out test set for each elastic modulus target (Young's, shear, Poisson's); compare against baseline mean-prediction model.
- **Feature importance analysis**: Extract permutation importance and SHAP values for best-performing model; identify top 3-5 descriptors contributing to prediction accuracy.
- **Statistical testing**: Perform bootstrap resampling (1000 iterations) on test set predictions to compute 95% confidence intervals for R²; test significance against null hypothesis (R² = 0) using t-test.
- **Visualization**: Generate parity plots (predicted vs. measured), feature importance bar charts, and partial dependence plots for top descriptors.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate
