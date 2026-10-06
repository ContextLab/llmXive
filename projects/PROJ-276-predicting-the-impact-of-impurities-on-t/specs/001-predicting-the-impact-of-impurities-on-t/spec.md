# Specification: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

## Overview
This project aims to predict the critical temperature (Tc) of Magnesium Diboride (MgB2) superconductors when doped with various impurities. We will consolidate data from the Materials Project API and the SuperCon dataset, train machine learning models, and perform statistical validation to determine the significance of specific impurities.

## User Stories

### US1: Data Ingestion and Preprocessing
As a researcher, I want to consolidate MgB₂ data from Materials Project and SuperCon so that I have a single, clean dataset with standardized units (atomic %) and no missing critical values.

### US2: Model Training and Selection
As a data scientist, I want to train multiple regression models (Linear, Ridge, RF, XGBoost) and select the best one based on cross-validated R² so that I can accurately predict Tc changes.

### US3: Statistical Validation and Interpretation
As a domain expert, I want to validate the statistical significance of impurity impacts (p < 0.05) and visualize Partial Dependence Plots so that I can derive physical insights and "rules of thumb".

## Functional Requirements

### FR-001: Data Provenance
All generated datasets must include a provenance header in JSON format indicating source, timestamp, and version.

### FR-002: Unit Standardization
All impurity concentrations must be converted from weight % to atomic % using accurate atomic weights.

### FR-003: Data Filtering
Entries with missing Tc or impurity data must be excluded from the training set.

### FR-004: Feature Permutation Test
To validate model robustness, we will perform a **Feature Permutation Test** (shuffling feature columns X) rather than a Target Permutation Test (shuffling Y), as the latter is methodologically invalid for assessing feature importance in this context. The p-value will be calculated based on the distribution of performance metrics from permuted features compared to the baseline.

### FR-005: Model Comparison
The system must compare at least four model types: Linear Regression, Ridge Regression, Random Forest, and XGBoost.

### FR-006: 30-minute runtime limit
The entire pipeline execution (from data download to final report generation) must complete within a **30-minute runtime limit** to ensure compatibility with CI/CD environments and standard compute budgets. If the process exceeds this limit, it must terminate gracefully with an appropriate error code.

## Non-Functional Requirements

### NFR-001: Reproducibility
All experiments must be reproducible with fixed random seeds and versioned dependencies.

### NFR-002: Error Handling
The system must fail loudly (exit code 1) if real data sources are unreachable or invalid, rather than falling back to synthetic data.

### NFR-003: Code Quality
Code must pass linting (ruff) and formatting (black) checks. Cyclomatic complexity should be kept below 10 for core logic functions.

## Data Sources
- **Materials Project API**: For crystal structure and elemental composition data.
- **SuperCon Dataset (HuggingFace)**: `taqwa92/cm.mgb2` for experimental Tc and impurity data.

## Output Artifacts
- `data/processed/mgb2_clean.csv`: Consolidated and preprocessed dataset.
- `data/processed/best_model.pkl`: The selected machine learning model.
- `data/processed/model_metrics.json`: Performance metrics for all trained models.
- `data/processed/significance_results_reduced.json`: Statistical significance results.
- `figures/pdp_plots.pdf`: Partial Dependence Plots for top impurities.