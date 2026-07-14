# Project Overview: Predicting Adsorption Isotherm Parameters

## Introduction

This project addresses the challenge of predicting adsorption isotherm parameters (specifically Langmuir capacity and Henry constants) using molecular descriptors derived from the adsorbate structure. By leveraging machine learning and cheminformatics, we aim to establish a robust predictive model that can accelerate the screening of adsorbent-adsorbate pairs for gas separation and storage applications.

## Scientific Context

Adsorption isotherms describe the relationship between the amount of adsorbate on an adsorbent and its pressure at a constant temperature. The Langmuir model and Henry's law are fundamental approximations used to characterize these interactions. Key parameters include:

- **Langmuir Capacity ($q_{max}$)**: The maximum amount of adsorbate the material can hold.
- **Henry Constant ($K_H$)**: A measure of adsorbate-adsorbent affinity at low pressures.

Predicting these parameters from molecular properties (e.g., polarizability, kinetic diameter) allows for high-throughput virtual screening without expensive experimental measurements or molecular simulations.

## Methodology

The project follows a structured pipeline:

1. **Data Curation**:
 - **Synthetic Generation**: Creates a large synthetic dataset (N=5000) with realistic noise and correlations to validate the pipeline.
 - **External Loading**: Loads manually curated data from literature (e.g., Krypton on Carbon Nanotubes) for scientific validation.
 - **Preprocessing**: Filters for Type I isotherms, normalizes units, and handles missing values.
 - **Descriptor Calculation**: Uses RDKit to compute molecular features (MW, PSA, Polarizability, Kinetic Diameter, etc.).

2. **Model Training**:
 - **Splitting**: Material-level splitting ensures no data leakage (adsorbates from the same material do not appear in both train and test sets).
 - **Algorithms**: Linear Regression, Random Forest, and Gradient Boosting.
 - **Validation**: 5-fold cross-validation and hyperparameter tuning.

3. **Evaluation & Interpretation**:
 - **Metrics**: R², RMSE, MAE.
 - **Statistical Significance**: Permutation testing with Benjamini-Hochberg FDR correction.
 - **SHAP Analysis**: Identifies the most influential molecular descriptors.
 - **Consensus Check (SC-002)**: Validates if top SHAP features match known physicochemical drivers (e.g., polarizability, kinetic diameter).
 - **Performance Threshold (SC-003)**: Verifies if a model using only top 3 features achieves R² >= 0.60.

## Validation Criteria

The project is driven by specific acceptance criteria:

- **SC-001**: Models must outperform a null model (predicting the mean) with significant RMSE improvement.
- **SC-002**: Top-ranked features from SHAP analysis must include at least 2 from the consensus list (polarizability, kinetic diameter, Lennard-Jones energy, quadrupole moment, molecular volume) when using external data.
- **SC-003**: A model retrained on the top 3 descriptors must achieve R² >= 0.60 on the external dataset.
- **SC-004**: Pipeline runtime must be under 6 hours on standard CI runners.

## Architecture

The codebase is modularized into distinct components:

- `code/data/`: Handles all data ingestion, cleaning, and feature engineering.
- `code/models/`: Manages model training, splitting, and evaluation logic.
- `code/interpret/`: Implements SHAP analysis, partial dependence plots, and diagnostic reports.
- `code/main.py`: The central orchestrator that coordinates the workflow based on the selected mode (synthetic vs. external).

## Future Work

- Integration of real-time NIST database fetching (currently fallback to verification log).
- Expansion to include more complex isotherm models (e.g., BET, Sips).
- Deployment of a web interface for interactive model exploration.
