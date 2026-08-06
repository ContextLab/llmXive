# Feature Specification: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Feature Branch**: `001-evaluating-compositional-correlation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1)

The research pipeline MUST successfully download the Materials Project MP-2020.12.1 dataset (verified subset), filter for inorganic compounds with complete data, and compute the required compositional descriptors (mean/variance of electronegativity, atomic radius, valence electrons, melting point, first ionization energy) for every entry.

**Why this priority**: Without a clean, computed dataset, no modeling or analysis can occur. This is the foundational step.

**Independent Test**: Can be fully tested by running the data ingestion script against the verified dataset source and verifying the output CSV contains a representative set of rows sufficient for statistical analysis and that all 5 descriptor columns contain non-null numeric values.

**Acceptance Scenarios**:

1. **Given** the verified dataset source is accessible, **When** the ingestion script executes, **Then** the output file contains a substantial set of inorganic compounds with non-missing formation energy and composition data.
2. **Given** a compound with multiple constituent elements, **When** the descriptor computation runs, **Then** the mean and variance of electronegativity, atomic radius, valence electrons, melting point, and ionization energy are correctly calculated across the constituent elements.
3. **Given** the dataset size (12,500 entries), **When** the computation finishes, **Then** the total memory usage does not exceed a moderate threshold and execution time is within 2 hours on a standard CPU.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The system MUST train a Random Forest regressor (max_depth=20, 200 trees) and a Gradient Boosting regressor (estimators) on the training split, evaluate them on the validation split, and output performance metrics (R², MAE, RMSE).

**Why this priority**: This delivers the core predictive capability required to answer the research question. Without valid models, feature importance cannot be determined.

**Independent Test**: Can be tested by training both models on the prepared dataset and verifying that the validation R² score is calculated and stored, and that the models do not crash due to memory or CPU constraints.

**Acceptance Scenarios**:

1. **Given** the 80/20 stratified split by Chemical Family, **When** the Random Forest model is trained, **Then** it completes within 3 hours on a 2-core CPU runner without GPU acceleration.
2. **Given** the trained models, **When** evaluated on the validation set, **Then** the system outputs R², MAE, and RMSE metrics for both models, including negative values if the model performs worse than a mean predictor.
3. **Given** the stratified split by Chemical Family, **When** the model is trained, **Then** the distribution of crystal systems in the validation set matches the training set with a Total Variation Distance ≤ 0.05.

---

### User Story 3 - Feature Importance Ranking and Sensitivity Analysis (Priority: P3)

The system MUST extract feature importances from the Random Forest model, validate rankings via permutation importance, and perform a sensitivity analysis on the top 3 features by generating Accumulated Local Effects (ALE) Plots to visualize non-linear relationships.

**Why this priority**: This addresses the specific research gap (ranking descriptors) and ensures the findings are robust and methodologically sound.

**Independent Test**: Can be tested by running the analysis script and verifying that a ranked list of 5+ features is produced, and that a sensitivity report (ALE visualizations) is generated for the top 3.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** feature importance is extracted, **Then** the top 5 descriptors are ranked by contribution magnitude.
2. **Given** the top 3 descriptors, **When** permutation importance is calculated, **Then** the ranking remains consistent (correlation of feature importance scores ≥ 0.8) with the original tree-based importances.
3. **Given** the top 3 features, **When** Accumulated Local Effects Plots are generated, **Then** the system outputs visualizations showing the non-linear relationship between each feature and formation energy.

### Edge Cases

- What happens when the dataset contains compounds with missing elemental properties (e.g., unknown electronegativity for a rare element)? The system must exclude these rows and log the count.
- How does the system handle extreme outliers in formation energy that might skew the regression? The system must detect and optionally cap values at the extreme lower and upper percentiles before training..
- What if the Random Forest model overfits (training R² >> validation R²)? The system must flag this discrepancy *and* only perform feature importance analysis if the validation R² exceeds a minimum threshold.
- How does the system handle VIF scores > 10? The system must log a warning that the features are highly correlated (expected due to physical reality) but MUST NOT remove them unless explicitly configured, as physical correlation is not a statistical error.
- What if the primary dataset source fails? The system MUST attempt to download from the fallback `matminer` source, and if that fails, load from a local cache, logging the source used.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download the Materials Project MP-2020.12.1 dataset (verified subset) and filter for inorganic compounds with complete composition and formation energy data (See US-1). If the primary source is inaccessible, attempt to download a fallback dataset from `matminer`, and if that fails, load from a local cache, logging the source used.
- **FR-002**: The system MUST compute mean and variance descriptors for electronegativity, atomic radius, valence electrons, melting point, and first ionization energy for every compound (See US-1).
- **FR-003**: The system MUST train a Random Forest regressor (max_depth=20, 200 trees) and a Gradient Boosting regressor (100 estimators) using scikit-learn on a CPU-only environment (See US-2).
- **FR-003a**: The system MUST save the trained Random Forest model to `data/evaluation/model_rf.pkl` and the Gradient Boosting model to `data/evaluation/model_gb.pkl` (See US-2).
- **FR-004**: The system MUST evaluate model performance using R², MAE, and RMSE on a validation set (See US-2).
- **FR-004a**: The validation set data MUST be split using Chemical Family stratification to control for compositional bias, as formation energy is driven by composition rather than just crystal structure (See US-2).
- **FR-004b**: The system MUST record negative R² values as valid metrics indicating the model performs worse than a mean predictor, and MUST NOT set them to null (See US-2).
- **FR-005**: The system MUST extract feature importances from the Random Forest model and validate them using permutation importance (See US-3).
- **FR-006**: The system MUST generate Accumulated Local Effects (ALE) Plots for the top 3 features to visualize their marginal effect on predicted formation energy, writing them as PNG images to `data/evaluation/ale_*.png` (See US-3).
- **FR-007**: The system MUST log the start and end times of each pipeline phase to enable accurate measurement of total compute time (See US-1, US-2).
- **FR-008**: The system MUST write ALE plots as PNG images to `data/evaluation/ale_*.png` (See US-3).
- **FR-009**: The system MUST measure the total execution time of the pipeline (ingestion, training, analysis) and record it in `data/evaluation/model_metrics.json` to verify compliance with the 6-hour limit (See US-1, US-2, US-3).

### Key Entities

- **Compound**: Represents an inorganic material with a specific chemical formula, formation energy, and crystal system.
- **DescriptorSet**: A collection of computed features (mean/variance of elemental properties) associated with a specific Compound.
- **ModelOutput**: The result of training a regression model, containing metrics (R², MAE, RMSE) and feature importance rankings.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The R² score of the best-performing model on the validation set is measured against the baseline of 0.0 (random guessing) to confirm predictive power (See US-2).
- **SC-002**: The correlation between tree-based feature importance and permutation importance is measured against a threshold of r ≥ 0.8 to confirm ranking stability (See US-3).
- **SC-003**: The Accumulated Local Effects (ALE) Plots for the top 3 features are generated and contain non-linearity score > 0.5, measured against the specified threshold to confirm robustness (See US-3).
- **SC-004**: The total compute time for the entire pipeline (ingestion, training, analysis) is measured against the time limit of the GitHub Actions free-tier runner: ≤ 6 hours (See US-1, US-2, US-3).
- **SC-005**: ALE images are written to `data/evaluation/ale_*.png` with valid image format (See US-3).
- **SC-006**: Downloaded dataset size is within the expected range (verified count) and checksum matches recorded value (See US-1).

## Assumptions

- The Materials Project MP-2020.12.1 dataset verified subset contains a substantial collection of inorganic compound entries with the required formation energy and composition data (source: Q47604, https://www.wikidata.org/wiki/Q47604).
- Elemental property databases (electronegativity, atomic radius, etc.) are available in a standard format (e.g., `pymatgen` or `matminer` built-in) and do not require external API calls during execution.
- The GitHub Actions free-tier runner (multi-core CPU, ~7 GB RAM) is sufficient to process the verified a large-scale dataset and train the specified Random Forest and Gradient Boosting models within 6 hours.
- The dataset does not contain significant class imbalance that would require resampling techniques beyond stratified splitting by chemical family.
- Stratification by Chemical Family is chosen over crystal system because formation energy is primarily driven by compositional thermodynamics, and this stratification better controls for compositional bias in the training/validation split.
- Tree-based models are appropriate for capturing the expected non-linear interactions in compositional data, rather than assuming a primarily linear relationship.
- No GPU acceleration is available or required; all computations will be performed using CPU-only scikit-learn implementations.
- VIF scores > 10 indicate high multicollinearity (expected due to physical correlation of elemental properties) and will trigger a warning but will not result in feature removal unless explicitly configured.
- Negative R² values are valid indicators of model failure (worse than mean predictor) and must be recorded, not nullified.