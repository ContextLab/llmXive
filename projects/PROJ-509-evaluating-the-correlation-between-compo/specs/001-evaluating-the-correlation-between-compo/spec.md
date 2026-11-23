# Specification: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Overview
This project evaluates the correlation between compositional features (mean/variance of elemental properties) and predicted formation energy in inorganic materials using the MP-2020.12.1 dataset.

## Functional Requirements

### FR-001: Data Ingestion
The system must download the MP-2020.12.1 dataset via the MPDS API. If the API is unavailable, it must fall back to a local checksummed CSV file. If both fail, the system must raise an exception.

### FR-002: Filtering
The system must filter the dataset to include only inorganic compounds.

### FR-003: Descriptor Computation
The system must compute mean and variance descriptors for five elemental properties: electronegativity, radius, valence, melting point, and ionization energy.

### FR-004: Stratified Splitting
The system must perform a stratified split of the dataset by **Chemical Family** (not crystal system) to ensure structural diversity in the validation set. The dominant element determines the family (e.g., Group 1 -> Alkali, d-block -> Transition, O-containing -> Oxide).

### FR-004a: Chemical Family Assignment
The system must use a fixed set of rules to map the dominant element to a chemical family for stratification purposes.

### FR-004b: Negative R² Handling
The system must explicitly verify and record negative R² values without converting them to null or zero.

### FR-005: Multi-Collinearity Check
The system must perform a Variance Inflation Factor (VIF) check on descriptors to diagnose stability.

### FR-006: Feature Importance Validation
The system must validate feature importances using permutation importance and calculate correlation with tree-based importances.

### FR-007: Phase Timing
The system must log start and end times for each pipeline phase.

## Assumptions

1. **Dataset Size**: The MP-2020.12.1 dataset contains a large-scale set of inorganic compound entries (expected > 100k rows).
2. **Memory Constraints**: The dataset may exceed available RAM, requiring chunked processing or stratified sampling.
3. **Stratification Strategy**: Stratified splitting by **Chemical Family** (based on the most abundant element) is sufficient to preserve statistical power and structural diversity in the validation set.
4. **Descriptor Relevance**: Mean and variance of elemental properties are predictive of formation energy.
5. **Model Performance**: Random Forest and Gradient Boosting models will achieve R² > 0.0 on the validation set.

## Non-Functional Requirements

- **Determinism**: All random operations must use a fixed seed (RANDOM_SEED = 42).
- **Reproducibility**: The system must be reproducible end-to-end with versioned artifacts.
- **Error Handling**: The system must fail loudly (raise exceptions) on data fetch failures or checksum mismatches.
- **Logging**: All pipeline phases and critical decisions must be logged.

## Data Flow

1. **Ingest**: Download MP-2020.12.1 -> Filter Inorganic -> Save Raw CSV
2. **Process**: Load Raw CSV -> Compute Descriptors -> Cap Outliers -> Save Processed CSV
3. **Train**: Load Processed CSV -> Stratified Split (Chemical Family) -> Train RF/GB -> Save Models
4. **Evaluate**: Load Models -> Calculate Metrics (R², MAE, RMSE) -> Calculate TVD -> Save Metrics
5. **Importance**: Load RF Model -> Extract Importances -> Calculate Permutation Importance -> Validate Correlation -> Save Rankings
6. **Plot**: Generate ALE/PDP Plots -> Save PNGs
7. **Summary**: Aggregate Metrics -> Generate Research Summary

## Artifacts

- `data/raw/mp-2020.12.1.csv`: Raw downloaded dataset
- `data/processed/computed_descriptors.csv`: Processed dataset with descriptors
- `data/evaluation/model_rf.pkl`: Trained Random Forest model
- `data/evaluation/model_gb.pkl`: Trained Gradient Boosting model
- `data/evaluation/model_metrics.json`: Model performance metrics
- `data/evaluation/permutation_importance.json`: Permutation importance scores
- `data/evaluation/feature_ranking.json`: Ranked features
- `data/evaluation/vif_scores.json`: VIF scores
- `data/evaluation/ale_*.png`: ALE plots
- `research.md`: Final research summary