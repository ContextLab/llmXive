# Spec: Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

## Overview
This project aims to predict the yield strength of steel alloys using machine learning models based on chemical composition and heat treatment parameters. The goal is to identify significant interactions between features that influence yield strength.

## User Stories
- **US1**: Data Ingestion and Preprocessing Pipeline
- **US2**: Model Training and Interaction Detection
- **US3**: Sensitivity Analysis and Threshold Justification

## Data Sources
- NIST Materials Data Repository
- Materials Project API
- Open-access metallurgy journals (for literature mining if needed)

## Assumptions
- The dataset will contain at least 100 samples with complete yield strength measurements.
- Chemical composition percentages will sum to approximately 100% (allowing for minor impurities).
- Heat treatment parameters (temperature, time, cooling rate) will be provided in standard units.
- **Resource Limits**: All models must run within **≤4 hours runtime** and **≤6 GB RAM** (per Constitution VI). This constraint applies to the entire pipeline execution, including data ingestion, feature engineering, model training, and evaluation.
- Feature engineering will include elemental ratios and pairwise interactions.
- Interaction terms will be orthogonalized against main effects using non-linear methods.
- Model evaluation will use nested cross-validation to prevent data leakage.
- Statistical significance will be assessed using Benjamini-Hochberg FDR correction.
- Thresholds for feature selection will be tested for stability using Jaccard index and rank correlation.

## Constraints
- **Constitution VI**: Runtime ≤4h, RAM ≤6GB. All algorithms and data processing must respect these limits.
- CPU-only execution; no CUDA or specialized hardware dependencies.
- Real data sources only; no synthetic data for validation.
- All code must be reproducible with fixed random seeds.

## Acceptance Criteria
1. Data pipeline successfully ingests, cleans, and engineers features from real sources.
2. At least four models (GAM, Linear Regression, RF, XGBoost) are trained and evaluated.
3. Interaction terms are identified with statistical significance (p < 0.05 after FDR correction).
4. Sensitivity analysis confirms stability of feature selection across thresholds.
5. All artifacts (plots, reports, model outputs) are generated and stored in designated directories.

## Dependencies
- Python 3.11+
- scikit-learn, xgboost, shap, pygam, pandas, numpy
- requests, beautifulsoup4, lxml (for data fetching and mining)

## Out of Scope
- Deployment to production environments.
- Real-time prediction services.
- Integration with external manufacturing systems.