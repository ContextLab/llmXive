# Project Specification: Predicting Carbon Diffusion in BCC Metals

## Objectives
- Predict diffusion coefficients of carbon in BCC metals using compositional data.
- Identify key descriptors influencing diffusion.
- Quantify variance explained by composition vs. microstructure.

## Requirements
- Use MeLiDC dataset for training.
- Implement RF, XGBoost, and Elastic Net models.
- Perform permutation tests and SHAP analysis.
- Ensure reproducibility with random seeds.
- Adhere to memory constraints (< 6 GB peak).

## Deliverables
- Cleaned dataset (`dataset_cleaned.csv`).
- Trained models and results (`model_results.json`, `best_model.pkl`).
- Feature importance and variance partitioning reports.