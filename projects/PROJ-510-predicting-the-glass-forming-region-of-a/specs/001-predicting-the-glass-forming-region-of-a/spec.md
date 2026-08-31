# Feature Specification: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Feature Branch**: `001-predict-glass-forming-region`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Glass Forming Region of Alloy Systems with Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1)

The system MUST successfully download a subset of ternary alloy entries from a curated experimental dataset containing critical cooling rates (e.g., a specific CSV of known glass formers or OQMD if it contains this field), filter for entries with reported glass-forming labels OR critical cooling rates, and compute thermodynamic descriptors (mixing enthalpy, atomic size difference, electronegativity variance) for every valid entry. The primary target variable is `critical_cooling_rate` (continuous).

**Why this priority**: Without a clean, feature-rich dataset with a valid target variable, no modeling or analysis can occur. This is the foundational data pipeline required for the entire research question.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing at least 500 valid alloy records with all required thermodynamic columns and the `critical_cooling_rate` column computed, without training any model.

**Acceptance Scenarios**:

1. **Given** a valid data source endpoint and a list of ternary alloy compositions, **When** the ingestion script runs, **Then** the output file contains at least 500 rows with no missing values in the `critical_cooling_rate` or `mixing_enthalpy` columns.
2. **Given** an alloy entry with missing elemental data for a specific element, **When** the feature engineering step processes it, **Then** the row is flagged or excluded, and a log entry is created with the specific reason for exclusion.
3. **Given** the raw elemental properties, **When** the thermodynamic formulas are applied, **Then** the computed `atomic_size_mismatch` and `electronegativity_variance` match the expected values from the Periodic Table definitions within a tolerance of 1e-6.
4. **Given** the dataset, **When** the target variable is checked, **Then** the `critical_cooling_rate` column must have non-zero variance and at least 500 valid entries; otherwise, the pipeline fails with a data availability error.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

The system MUST train a Random Forest regressor on the engineered features using a standard train-test split and evaluate performance using k-fold cross-validation, reporting RMSE. If a binary classification task is performed (using a physically-grounded threshold), the system MUST also report F1-score.

**Why this priority**: This implements the core methodology to answer the research question. It validates whether the thermodynamic descriptors have predictive power.

**Independent Test**: The training script can be executed on the generated dataset to produce a trained model file and a metrics report containing the cross-validation score, without requiring any external GPU or internet access after the data is loaded.

**Acceptance Scenarios**:

1. **Given** the feature-engineered dataset, **When** the training script executes, **Then** a Random Forest model is saved to disk, and the cross-validation mean RMSE is printed to the console.
2. **Given** a 5-fold cross-validation setup, **When** the folds are generated, **Then** each fold contains a distinct, non-overlapping subset of the data, and the variance between fold scores is calculated.
3. **Given** the trained model, **When** it predicts on the held-out test set, **Then** the test set RMSE is calculated and logged, distinct from the cross-validation score.

---

### User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

The system MUST perform permutation importance analysis to rank thermodynamic parameters and conduct a sensitivity analysis sweeping the decision threshold (if binarized) or analyzing correlation stability across a range of parameter perturbations. The sensitivity analysis MUST use a physically-grounded threshold (e.g., 100 K/s) for any binarization.

**Why this priority**: This addresses the "Expected results" requirement to identify *which* parameters drive the prediction and validates the robustness of the findings against threshold choices.

**Independent Test**: The analysis script can be run on the trained model to output a ranked list of feature importances and a sensitivity report showing how performance metrics vary with threshold changes.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** permutation importance is calculated (n_permutations=1000, random_state=42), **Then** the output lists features in descending order of importance, with the top feature having a statistically significant importance score (p < 0.05 via permutation test).
2. **Given** a critical cooling rate cutoff (e.g., 100 K/s), **When** the threshold is swept across a set of values relative to the baseline, **Then** the RMSE (or F1 if binarized) is reported for each step.
3. **Given** the correlation matrix of predictors, **When** collinearity is checked, **Then** any pair of predictors with a correlation coefficient > 0.8 is flagged, and the model is re-run excluding one of the collinear features to verify stability.

### Edge Cases

- What happens if the data source returns an empty dataset or fewer than 500 entries? The system MUST fail gracefully with a specific error message indicating insufficient data for statistical significance.
- How does the system handle alloys with undefined glass-forming labels (e.g., "unknown" or "mixed")? The system MUST exclude these entries from the training set and log the count of excluded samples.
- What if the computed mixing enthalpy is zero for a specific composition? The system MUST treat this as a valid numeric value (not an error) and proceed, as zero enthalpy is a physically valid state.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download a subset of ternary alloy entries (target N ≥ 1000, minimum N ≥ 500 required) from a source containing experimental critical cooling rates (e.g., OQMD if available, or a curated experimental CSV) via HTTP or file load and parse the response into a structured format (See US-1).
- **FR-002**: System MUST compute thermodynamic descriptors (mixing enthalpy, atomic size mismatch, electronegativity variance) for every valid entry using standard elemental properties from the Periodic Table (See US-1).
- **FR-003**: System MUST train a Random Forest regressor on the computed features using an 80/20 train-test split and perform 5-fold cross-validation to estimate generalization performance (See US-2).
- **FR-004**: System MUST perform permutation importance analysis to rank the contribution of each thermodynamic parameter to the model's predictive power (See US-3).
- **FR-005**: System MUST execute a sensitivity analysis sweeping a physically-grounded critical cooling rate cutoff (e.g., {50, 100, 150} K/s) to report RMSE variance or correlation stability (See US-3).
- **FR-006**: System MUST explicitly frame all predictive findings as ASSOCIATIONAL if the dataset is observational, avoiding causal claims unless randomization is specified (See US-2).

### Key Entities

- **AlloyRecord**: Represents a single ternary alloy entry. Attributes include composition (A_x B_y C_z), critical_cooling_rate, mixing_enthalpy, atomic_size_mismatch, electronegativity_variance, and source_label.
- **ModelMetrics**: Represents the output of the training and validation process. Attributes include fold_scores, mean_rmse, test_rmse, and feature_importance_ranking.
- **SensitivityReport**: Represents the output of the threshold/collinearity analysis. Attributes include threshold_values, rmse_variance, and collinearity_flags.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The dataset construction pipeline MUST produce a final training set with at least 500 valid entries (after filtering) to ensure statistical power, measured against the initial data query count (See FR-001, US-1).
- **SC-002**: The Random Forest model MUST achieve a cross-validation RMSE that is statistically distinguishable from a null model (dummy regressor predicting mean target value) with p < 0.05 (two-sided t-test), measured against the baseline null performance (See FR-003, US-2).
- **SC-003**: The sensitivity analysis MUST demonstrate that the headline metric (e.g., RMSE) varies by a negligible margin across the swept threshold range {50, 100, 150} K/s (or F1 varies by <10% if binarized using threshold < 100 K/s), measured against the baseline threshold result (See FR-005, US-3).
- **SC-004**: The feature importance analysis MUST identify at least one thermodynamic parameter (e.g., mixing enthalpy) as a top-2 contributor with a p-value < 0.05 from a permutation test (n=1000), measured against the shuffled baseline (See FR-004, US-3).
- **SC-005**: The analysis MUST complete within 6 hours on a standard CPU-only runner (2 cores, 7 GB RAM) without GPU acceleration, measured against the CI job time limit (See US-2, US-3).

## Assumptions

- The data source (e.g., curated experimental CSV or OQMD) is accessible and contains the `critical_cooling_rate` field for a sufficient number of ternary alloys (≥ 500) to support machine learning training.
- The Random Forest algorithm, as implemented in scikit-learn, is computationally feasible on a CPU-only environment with standard RAM for a dataset of moderate size and a standard number of features.
- The thermodynamic formulas for mixing enthalpy and atomic size mismatch are well-defined and can be calculated using standard elemental properties available in a local periodic table database.
- The relationship between thermodynamic parameters and glass-forming ability is non-linear, justifying the use of a Random Forest model over a linear regression model.
- No GPU or CUDA acceleration is available or required for the training and inference steps of this specific model size and dataset.
- The primary target variable is the continuous `critical_cooling_rate`. Binarization (if performed) is based on a physically-grounded threshold (e.g., 100 K/s).