# Specification: Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

## 1. Overview

This project aims to develop a predictive model for the yield strength of steel alloys based on their chemical composition and heat treatment parameters. The model will utilize machine learning techniques, specifically Generalized Additive Models (GAMs), to capture non-linear relationships and interactions between features. The primary goal is to identify significant interaction terms that influence yield strength, providing insights into the underlying metallurgical mechanisms.

## 2. Objectives

- **Primary Objective**: Develop a robust predictive model for yield strength using composition and heat treatment data.
- **Secondary Objective**: Identify and validate significant interaction terms that contribute to yield strength prediction.
- **Tertiary Objective**: Provide interpretable insights into the relationships between input features and yield strength.

## 3. Scope

### In Scope
- Data ingestion from NIST and Materials Project.
- Data preprocessing, including cleaning, normalization, and feature engineering.
- Model training using GAMs, Linear Regression, Random Forest, and XGBoost.
- Interaction detection using SHAP values and nested permutation tests.
- Sensitivity analysis on decision thresholds.
- Generation of interpretable plots (PDPs, SHAP summaries).

### Out of Scope
- Real-time prediction API deployment.
- Integration with external manufacturing execution systems.
- Experimental validation of predicted alloys in a physical lab setting.

## 4. Assumptions

- **Data Availability**: Sufficient high-quality data will be available from NIST and Materials Project to train and validate the models.
- **Computational Resources**: The project will be executed on a standard workstation with the following constraints:
 - **Runtime**: Maximum 4 hours for the entire pipeline (Constitution VI).
 - **Memory**: Maximum 6 GB RAM usage (Constitution VI).
 - **Hardware**: CPU-only execution; no GPU/CUDA acceleration.
- **Data Quality**: Raw data will be reasonably clean, requiring standard preprocessing steps but not extensive manual curation.
- **Model Performance**: The chosen models (GAM, RF, XGBoost) will be capable of achieving a reasonable R² score (>0.6) on the test set.
- **Interaction Significance**: There exist meaningful interaction terms between composition and heat treatment parameters that significantly impact yield strength.
- **Software Dependencies**: All required Python libraries (scikit-learn, xgboost, shap, pygam, pandas, numpy, requests, beautifulsoup4, lxml) are available and compatible with Python 3.11.

## 5. Constraints

- **Constitution VI**: The total runtime must not exceed 4 hours, and memory usage must not exceed 6 GB.
- **Hardware**: CPU-only execution; no CUDA, 8-bit/4-bit quantization, or large LLMs.
- **Data Integrity**: No synthetic data generation for validation; only real data from specified sources.
- **Reproducibility**: All experiments must be reproducible with a fixed random seed.
- **Interpretability**: Models must provide interpretable outputs (SHAP values, PDPs) to support scientific inquiry.

## 6. Data Sources

- **NIST**: National Institute of Standards and Technology database for steel properties.
- **Materials Project**: Open database of materials properties and compositions.
- **Literature Mining**: Supplementary data may be scraped from open-access metallurgy journals if the primary sources yield <100 samples.

## 7. Feature Engineering

- **Elemental Ratios**: C/Mn, Cr/Ni, etc.
- **Interaction Terms**: Pairwise interactions (e.g., Cooling Rate × Holding Time, C × Cooling Rate).
- **Orthogonalization**: Interaction terms will be orthogonalized against their constituent main effects using non-linear orthogonalization (regressing against a natural spline basis, degree=3, knots=5).
- **Normalization**: Thermal parameters (temperature, cooling rate) will be normalized to [0.0, 1.0].
- **Encoding**: Heat treatment types will be one-hot encoded.

## 8. Model Training

- **Algorithms**:
 - Generalized Additive Models (GAM) with splines.
 - Regularized Linear Regression.
 - Random Forest.
 - XGBoost.
- **Cross-Validation**:
 - Default: 3-fold CV.
 - If dataset size < 100: 10-Fold Repeated CV.
- **Hyperparameter Tuning**: Grid search or randomized search within the CV framework.

## 9. Evaluation Metrics

- **Primary**: R² Score.
- **Secondary**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE).
- **Interaction Detection**: SHAP interaction values, p-values from nested permutation tests.
- **Stability**: Jaccard index and Kuncheva index for feature selection stability across thresholds.

## 10. Deliverables

- **Code**: Python modules for data ingestion, preprocessing, feature engineering, model training, and evaluation.
- **Data**: Processed datasets in CSV/Parquet format.
- **Reports**:
 - Sensitivity analysis report (`results/sensitivity_report.md`).
 - Model performance summary.
 - Interaction term analysis.
- **Visualizations**:
 - SHAP summary plots.
 - Partial Dependence Plots (PDPs) for top interaction terms.

## 11. Risks and Mitigations

- **Risk**: Insufficient data from primary sources.
 - **Mitigation**: Implement literature mining fallback.
- **Risk**: Model performance below threshold.
 - **Mitigation**: Explore alternative feature engineering techniques and model architectures.
- **Risk**: Computational resource limits exceeded.
 - **Mitigation**: Optimize code for memory and speed; use efficient data structures.

## 12. Future Work

- Integration of additional data sources (e.g., proprietary databases).
- Extension to other mechanical properties (e.g., tensile strength, ductility).
- Deployment of the model as a web service for real-time predictions.
- Experimental validation of predicted high-strength alloys.