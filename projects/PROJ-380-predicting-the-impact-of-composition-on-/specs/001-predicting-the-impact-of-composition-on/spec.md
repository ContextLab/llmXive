# Feature Specification: Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

**Feature Branch**: `001-predicting-shear-modulus`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1)

The researcher needs to automatically download raw composition and shear modulus data from public repositories (Materials Project, Inoue's compilation), clean the dataset by filtering for non-crystalline BMGs, and compute standard compositional descriptors (atomic size mismatch, mixing enthalpy, valence electron concentration, electronegativity difference) to create a ready-to-train feature matrix.

**Why this priority**: Without a clean, processed dataset with computed descriptors, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script on a small sample dataset and verifying that the output CSV contains exactly the expected columns (compositions, shear modulus, δ, ΔHmix, VEC, electronegativity difference) with no missing values in the target variable.

**Acceptance Scenarios**:

1. **Given** a raw dataset containing mixed alloy types (crystalline and amorphous) and missing shear modulus values, **When** the ingestion script runs, **Then** the output dataset contains only entries where the phase is confirmed as "bulk metallic glass" and the shear modulus is non-null.
2. **Given** a list of elemental compositions in atomic percent, **When** the feature engineering module runs, **Then** the output includes calculated columns for atomic size mismatch (δ), mixing enthalpy (ΔHmix), valence electron concentration (VEC), and electronegativity difference derived from standard elemental property tables.
3. **Given** a dataset with inconsistent composition notation (e.g., weight percent vs atomic percent), **When** the cleaning step runs, **Then** all compositions are standardized to atomic percent before feature calculation.

---

### User Story 2 - Model Training and Performance Evaluation (Priority: P2)

The researcher needs to train three regression models (Linear Regression, Random Forest, Gradient Boosting) on the engineered dataset using 5-fold cross-validation and leave-one-family-out cross-validation, tune hyperparameters via grid search (limited to ≤50 combinations), and evaluate performance using R², MAE, and RMSE on a held-out test set. The researcher also needs to compare model performance using a statistically sound method that accounts for fold dependency.

**Why this priority**: This story delivers the core predictive capability and quantitative comparison of methods, directly addressing the research question about which descriptors best predict shear modulus.

**Independent Test**: The training script can be tested by running it on a fixed subset of the data and verifying that it outputs a JSON report containing R², MAE, and RMSE scores for all three models, along with the best hyperparameters found for each, and results from the corrected resampled t-test.

**Acceptance Scenarios**:

1. **Given** the processed dataset split into [deferred] training and [deferred] test sets (stratified by alloy family), **When** the model training script executes, **Then** all three regression models are trained and their performance metrics (R², MAE, RMSE) are recorded on the held-out test set.
2. **Given** a grid of hyperparameters for Random Forest and Gradient Boosting, **When** the grid search runs with 5-fold cross-validation, **Then** the system selects the parameter combination yielding the highest mean cross-validated R² score, limiting the search space to ≤50 combinations to respect memory constraints.
3. **Given** the performance metrics of the three models, **When** the comparison step runs, **Then** a corrected resampled t-test (Nadeau & Bengio) or paired permutation test is performed on the cross-validation folds to determine if differences in model performance are significant, accounting for the non-independence of folds.
4. **Given** the dataset grouped by alloy family, **When** the validation step runs, **Then** a leave-one-family-out (LOFO) cross-validation is performed to ensure the model generalizes across different alloy families, not just within them.

---

### User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

The researcher needs to extract feature importances from the best-performing tree-based model, perform permutation importance testing (100 permutations) to assess predictive contribution, and generate visualizations including partial dependence plots for the top 3 features and a correlation heatmap. The analysis must clarify that permutation importance measures model dependency, not physical significance.

**Why this priority**: This story provides the interpretability required to answer "which compositional descriptors most strongly govern this relationship," adding scientific value beyond mere prediction accuracy.

**Independent Test**: The analysis script can be tested by running it on the trained model and verifying that it outputs a JSON file with permutation importance scores and generates the required plot files (PNG/PDF) for partial dependence and correlation heatmap.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest or Gradient Boosting model, **When** the feature importance analysis runs, **Then** the system outputs a ranked list of descriptors with their permutation importance scores and p-values derived from 100 permutations, explicitly labeled as 'predictive contribution within the trained model' rather than 'statistical significance of the physical relationship'.
2. **Given** the top 3 most important descriptors, **When** the visualization module runs, **Then** partial dependence plots are generated showing the relationship between each descriptor and the predicted shear modulus, holding other features constant.
3. **Given** the full set of descriptors and the target variable, **When** the correlation analysis runs, **Then** a heatmap is generated showing the correlation coefficients between all descriptors and the shear modulus, highlighting potential collinearity issues.

---

### Edge Cases

- What happens when the dataset contains entries with elemental compositions that exceed the bounds of the Mendeleev database (e.g., hypothetical elements or missing atomic data)?
- How does the system handle alloy families with very few samples (e.g., <10 entries) during stratified splitting, potentially causing empty test folds?
- How does the system respond if the grid search exhausts all 50 parameter combinations without finding a model that meets a minimum performance threshold?
- What occurs if the permutation test yields a p-value > 0.05 for all descriptors, indicating no statistically significant feature importance?

## Requirements

### Functional Requirements

- **FR-001**: System MUST download BMG composition and shear modulus data from the Materials Project API and Inoue's BMG compilation (See US-1)
- **FR-002**: System MUST filter the dataset to include only entries confirmed as bulk metallic glasses, excluding crystalline alloys (See US-1)
- **FR-003**: System MUST compute atomic size mismatch (δ), mixing enthalpy (ΔHmix), valence electron concentration (VEC), and electronegativity difference for each composition (See US-1)
- **FR-004**: System MUST split the dataset into [deferred] training and [deferred] test sets, stratified by alloy family (See US-2)
- **FR-005**: System MUST train Linear Regression, Random Forest, and Gradient Boosting regressors using scikit-learn (See US-2)
- **FR-006**: System MUST perform grid search hyperparameter tuning with 5-fold cross-validation, limited to ≤50 parameter combinations (See US-2)
- **FR-007**: System MUST evaluate model performance using R², MAE, and RMSE on the held-out test set and compare models using a corrected resampled t-test or paired permutation test (See US-2)
- **FR-008**: System MUST perform leave-one-family-out (LOFO) cross-validation to validate generalization across alloy families (See US-2)
- **FR-009**: System MUST extract feature importances from tree-based models and perform permutation importance testing with 100 permutations, explicitly labeling results as predictive contribution (See US-3)
- **FR-010**: System MUST provide a single entry point script or Makefile that orchestrates the full pipeline from raw data to final artifacts, including a requirements.txt or pyproject.toml file with pinned dependencies (See US-3)
- **FR-011**: System MUST generate partial dependence plots for the top 3 features and a correlation heatmap of descriptors vs. shear modulus (See US-3)

### Key Entities

- **BMGEntry**: Represents a single bulk metallic glass sample with attributes including elemental composition (atomic percent), shear modulus value, alloy family classification, and source dataset reference.
- **CompositionalDescriptor**: Represents a calculated feature derived from elemental properties, including atomic size mismatch (δ), mixing enthalpy (ΔHmix), valence electron concentration (VEC), and electronegativity difference.
- **ModelPerformance**: Represents the evaluation results of a trained model, including R² score, MAE, RMSE, and cross-validation statistics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of variance in shear modulus explained by compositional descriptors is measured against the hypothesis that atomic size mismatch and mixing enthalpy together explain ≥60% of variance (See US-2)
- **SC-002**: Model prediction accuracy (MAE) is measured against the baseline of linear regression performance to quantify improvement from non-linear methods (See US-2)
- **SC-003**: Feature importance rankings are measured against permutation testing results to determine predictive contribution within the trained model (See US-3)
- **SC-004**: Computational efficiency is measured against the constraint of completing the analysis within the resource limits of a standard GitHub Actions free-tier runner (See US-2)
- **SC-005**: Reproducibility is measured by the ability to regenerate all results from the entry point script or Makefile with pinned dependencies (See US-3)

## Assumptions

- The Materials Project API and Inoue's BMG compilation provide sufficient data points (≥100 entries) across multiple alloy families to enable meaningful machine learning analysis.
- Elemental property data (atomic radii, electronegativity, etc.) from the Mendeleev database are complete and accurate for all elements present in the BMG compositions.
- The GitHub Actions free-tier runner provides adequate resources (multiple CPU cores, sufficient RAM) to process the dataset and train the specified models without memory overflow.
- The stratified split by alloy family will result in balanced train/test distributions for each family, avoiding empty test folds for rare alloy types.
- The grid search hyperparameter tuning will identify optimal parameters within the limited search space of ≤50 combinations for all three model types.
- Permutation importance testing with 100 permutations will provide sufficient statistical power to distinguish significant from non-significant feature contributions.