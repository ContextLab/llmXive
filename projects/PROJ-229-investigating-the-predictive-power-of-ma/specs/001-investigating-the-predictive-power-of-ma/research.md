# Research: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Overview

This research aims to determine if machine learning can effectively identify novel phase-change materials (PCMs) based on structural and compositional descriptors. The study leverages data from the Materials Project and external literature to train interpretable models (symbolic regression, SHAP-analyzed trees) and validate their predictive power and generalizability.

## Dataset Strategy

### Verified Datasets

The following datasets are verified and will be used as the primary data sources:

1.  **Materials Project (MP) Data**:
    *   **Source**: Materials Project API (programmatic access via `pymatgen`).
    *   **Content**: Crystal structures, elemental compositions, melting points, and heat capacity data for inorganic compounds.
    *   **Usage**: Primary training and validation dataset.
    *   **Access**: Requires API key. The retrieval script will handle rate limiting and pagination.
 * **Query Logic**: Use `pymatgen` to query for compounds with `melting_point` and `heat_capacity` properties. The query will be limited to [deferred]-10,000 compounds to fit within memory constraints.
    *   **Note**: The spec assumes sufficient access. If the API returns a limited subset, the system will switch to a fallback strategy (e.g., using a pre-cached subset or reducing the scope) and flag the limitation.

2.  **NIST PCM Data**:
    *   **Source**: If a verified Hugging Face dataset or direct programmatic download is not available, the project will proceed with `melting_point` as the primary target and flag the limitation.
    *   **Content**: Latent heat of fusion values for known PCMs.
    *   **Usage**: Validation of imputation strategies (if latent heat is missing in MP) and external validation.
    *   **Constraint**: The spec mentions NIST latent heat data. If the overlap with MP compounds is < 500, the system will fall back to using melting point and heat capacity as primary predictors and flag the limitation.

3.  **Literature PCM Data**:
    *   **Source**: Independent literature set (e.g., from a verified Hugging Face dataset or a curated CSV from a verified DOI). If the DOI is inaccessible, a pre-defined fallback set of 50 PCMs will be used.
    *   **Content**: Known PCMs with measured latent heat values.
    *   **Usage**: Independent validation set (Constitution Principle VII).
    *   **Access**: The implementation will attempt to fetch from a verified source. If inaccessible, the system will skip this validation step and flag the limitation, rather than hard-failing.
    *   **Fallback**: If the literature dataset cannot be fetched, the validation will be limited to the MP test set, and the report will explicitly state the lack of independent physical validation.

### Data Retrieval & Preprocessing

1.  **MP Data Retrieval**:
    *   Use `pymatgen` to query the MP API for compounds with melting point and heat capacity data.
    *   Filter for compounds with non-null values for key properties.
 * Limit to [deferred]–[deferred] compounds to fit within memory constraints.
    *   Store raw data in `data/raw/mp_raw.csv`.

2.  **Feature Extraction**:
    *   **Elemental Descriptors**: Compute atomic number, electronegativity, atomic radius, etc., using `pymatgen`'s elemental data.
    *   **Structural Descriptors**: Use `pymatgen`'s `StructureGraph` to compute crystal graph representations (e.g., bond lengths, coordination numbers, symmetry).
    *   **Graph-to-Symbolic Transformation**: Aggregate high-dimensional graph representations into scalar descriptors (e.g., mean bond length, coordination number distribution moments) for use in PySR.
    *   **Handling Missing Data**: Impute missing values where appropriate (e.g., using median) or exclude rows with critical missing data. Log all imputation rates.
    *   **Numerical Stability**: Check for `nan`/`inf` in computed features and handle them (e.g., exclude or impute) before model training.

3.  **NIST/Literature Integration**:
    *   Attempt to merge MP data with NIST latent heat data.
    *   If overlap is low, proceed with melting point as the primary target and flag the limitation.
    *   Load literature PCM data for independent validation. If unavailable, skip this step and flag.
    *   **Target Variable Decision**: In Phase 0.5, calculate the correlation between `melting_point` and `latent_heat` for a sample of MP data. If `latent_heat` is available for >50% of the sample, use it as the target. Otherwise, use `melting_point` and flag the change in research scope.

## Model Strategy

### Baseline Models

1.  **Random Forest (RF)**:
    *   **Purpose**: Black-box baseline for predictive performance.
    *   **Implementation**: `scikit-learn` `RandomForestRegressor`.
    *   **Constraints**: CPU-only, limited trees/depth to fit within time/memory.

2.  **Gradient Boosting (GB)**:
    *   **Purpose**: Black-box baseline for predictive performance.
    *   **Implementation**: `scikit-learn` `GradientBoostingRegressor`.
    *   **Constraints**: CPU-only, limited iterations.

### Interpretable Models

1.  **SHAP Analysis**:
    *   **Purpose**: Explain feature importance of tree-based models.
    *   **Implementation**: `shap` library on trained RF/GB models.
    *   **Output**: Ranked list of feature importances.

2.  **Symbolic Regression (PySR)**:
    *   **Purpose**: Derive explicit mathematical formulas governing phase-change suitability.
    *   **Implementation**: `pysr` library.
    *   **Constraints**: CPU-only, time-limited (4 hours). If convergence fails, default to Lasso regression (linear model with L1 regularization) which produces a sparse, interpretable formula.
    *   **Output**: Explicit mathematical formulas (or Lasso coefficients).

### Validation & Sensitivity

1.  **External Validation**:
    *   Apply derived rules (from PySR or Lasso) to the independent literature set (or random sample of materials).
    *   **Metric**: Calculate Spearman correlation between predicted and actual latent heat (or melting point) for the validation set. This avoids the tautology of 'top-k PCM' ranking if the validation set is random.
    *   **Success Criterion**: Spearman correlation > 0.5 (value deferred).
    *   **Top-k Accuracy**: If the validation set contains a sufficient number of PCMs, calculate the percentage of top-k PCMs correctly ranked. The value 'k' is read from `config.yaml` (default 10). If the validation set contains fewer than 'k' PCMs, the metric is calculated on the available count, and this limitation is reported.

2.  **Sensitivity Analysis**:
    *   Sweep feature importance thresholds (e.g., 0.01, 0.05, 0.1) to assess robustness.
    *   Read thresholds from `config.yaml`.
    *   Report variation in false-positive/false-negative rates.
    *   **Success Criterion**: Robustness across a range of low thresholds.

3.  **Collinearity Check**:
    *   Identify definitionally related predictors (e.g., atomic radius vs. ionic radius).
    *   Flag these relationships and frame interpretations descriptively, not causally.
    *   Write `data/results/collinearity_report.json` with the flagged dependencies and adjusted interpretation text.

4.  **Multicollinearity Test**:
    *   Train a model with and without `melting_point` as a predictor.
    *   Compare performance to determine if `melting_point` is a dominant predictor.
    *   If performance drops significantly, report that `melting_point` is a strong predictor, and evaluate the 'structural descriptors' for independent contribution only after controlling for `melting_point`.

## Decision/Rationale

- **CPU-First**: All models (RF, GB, PySR, Lasso) are chosen for their CPU-tractability. PySR is known to run on CPU, though it may be slower. The plan does not require GPU acceleration for the primary methods.
- **Dataset Fit**: The MP dataset is verified to contain the necessary structural and compositional data. The NIST and literature datasets are used for validation and imputation checks. If these are unavailable, the plan includes fallback strategies (flagging limitations) rather than hard-failing.
- **Statistical Rigor**:
    - **Multiple Comparisons**: Not directly applicable as the focus is on model performance and rule derivation, but the sensitivity analysis addresses threshold robustness.
 - **Sample Size**: The plan targets [deferred]–[deferred] compounds, which is sufficient for ML models. Power limitations will be acknowledged if the dataset is smaller.
    - **Causal Inference**: The data is observational. All claims will be framed as associational. The term 'governing factors' is replaced with 'highly predictive structural descriptors' in the context of the study's findings.
    - **Measurement Validity**: The use of `pymatgen` for feature extraction ensures standard, validated methods.
    - **Collinearity**: Explicit checks and descriptive framing will be implemented.
    - **Circular Validation**: The literature set is a random sample of materials, and the 'top-k PCMs' are identified post-hoc by sorting the sample by predicted latent heat. This avoids selecting the validation set based on the target variable.
    - **Tautological Metric**: The primary metric is Spearman correlation, which measures the model's ability to predict the target variable without pre-selecting the validation set based on the target.

## Compute Feasibility

- **CPU**: The chosen methods (RF, GB, PySR, Lasso) are designed to run on CPU. The plan includes time and memory limits to ensure feasibility on the GitHub Actions free-tier.
- **GPU Escape Hatch**: Not required for the primary methods. If a future extension requires deep learning, the plan would include a scaled-down GPU version for Kaggle.
- **Data Streaming**: The MP dataset will be streamed or sampled to fit within memory constraints. The full dataset will not be loaded at once if it exceeds 7 GB.

## Critical Methodological Note (for Report)

> **Critical Methodological Note**: This study is observational. All findings are framed as associational relationships between structural descriptors and phase-change suitability. The term 'governing factors' is used to describe highly predictive structural descriptors, not causal mechanisms. The validation against literature PCMs tests predictive generalization, not causal governance. Any claim of 'governing' is a hypothesis for future experimental validation, not a finding of this study.