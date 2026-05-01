---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Field**: chemistry

## Research question

Can machine learning regression models accurately predict corrosion rates of common metals (e.g., steel, aluminum, copper) using publicly available environmental and material property datasets?

## Motivation

Corrosion causes billions in annual infrastructure damage, yet traditional measurement methods are slow and costly. This project addresses the gap in rapid, cost-effective prediction by leveraging data-driven materials science paradigms. Success would demonstrate that open data repositories contain sufficient signal to train models for industrial maintenance planning.

## Related work

- [Changing Data Sources in the Age of Machine Learning for Official Statistics (2023)](http://arxiv.org/abs/2306.04338v1) — Establishes the paradigm of using automated data collection and ML for statistical analysis in large-scale scientific domains.
- [Data‐Driven Materials Science: Status, Challenges, and Perspectives (2019)](https://doi.org/10.1002/advs.201900808) — Provides the foundational framework for treating materials datasets as a primary resource for extracting knowledge on properties like corrosion.

## Expected results

The project expects to train a regression model (e.g., Random Forest) achieving an R² > 0.7 on a held-out test set of corrosion rates. The measurement will confirm the feasibility of ML prediction if environmental variables (pH, salinity) show high feature importance compared to material composition alone. Evidence will be provided via cross-validation metrics and feature importance plots.

## Methodology sketch

- **Data Acquisition**: Search Zenodo and HuggingFace Datasets for tabular corrosion datasets using `wget` or `curl` (e.g., `https://zenodo.org/search?q=corrosion+dataset`).
- **Preprocessing**: Clean missing values and normalize environmental features (temperature, pH, salinity) using `pandas` and `scikit-learn`.
- **Feature Engineering**: Generate interaction terms between material properties (atomic radius, electronegativity) and environmental stressors.
- **Model Training**: Split data into 80/20 train/test sets; train Random Forest and Gradient Boosting regressors using `scikit-learn` (CPU-only).
- **Hyperparameter Tuning**: Perform grid search with limited depth (max_depth=5) to stay within 7GB RAM and 6-hour runtime limits.
- **Statistical Evaluation**: Calculate Root Mean Squared Error (RMSE) and R² on the test set; apply k-fold cross-validation (k=5) to ensure robustness.
- **Visualization**: Generate SHAP value plots to interpret feature contributions using the `shap` library (CPU-compatible).
- **Reporting**: Save model artifacts and plots to the project repository; document data sources with DOIs for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A.
- Verdict: NOT a duplicate
