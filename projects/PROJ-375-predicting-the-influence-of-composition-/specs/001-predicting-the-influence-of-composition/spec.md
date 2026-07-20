# Feature Specification: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

The system must retrieve metallic glass composition and CTE data from public repositories (Materials Project, AFLOWlib), filtering specifically for entries flagged as amorphous or metallic glass, and extract compositional descriptors (weighted mean atomic radius, electronegativity variance, valence electron concentration, atomic size mismatch) for every entry.

**Why this priority**: Without a clean, feature-rich dataset filtered for the correct material state, no modeling or analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying that the output CSV contains exactly the required columns (composition, CTE, weighted mean atomic radius, electronegativity, VEC, atomic size mismatch) with no missing values for the selected metallic glass subset, and that the 'amorphous state flag' is present and used for filtering. Note: 'weighted mean atomic radius' and 'atomic size mismatch' are mathematically coupled; the test verifies both are present as derived features.

**Acceptance Scenarios**:

1. **Given** valid API credentials for Materials Project and AFLOWlib, **When** the ingestion script runs, **Then** the output dataset contains all available unique metallic glass entries with valid CTE values and amorphous state flags (target: ≥500, proceed with <500 if available).
2. **Given** a raw composition string (e.g., "Zr50Cu40Al10"), **When** the feature extraction module processes it, **Then** it calculates and appends the weighted mean atomic radius, electronegativity variance, valence electron concentration, and atomic size mismatch.
3. **Given** a dataset entry where the CTE value is missing, unreliable, or not flagged as amorphous in the source, **When** the ingestion script runs, **Then** that entry is excluded from the final training dataset.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

The system must train baseline linear regression and random forest models using scikit-learn on CPU, performing k-fold cross-validation to tune hyperparameters within strict resource limits.

**Why this priority**: This step establishes the predictive capability of the composition-CTE mapping and determines if the relationship is learnable from composition alone.

**Independent Test**: Can be fully tested by executing the training pipeline on a sample subset and verifying that the 5-fold cross-validation scores (R², MAE) are generated as non-null, finite numbers, and that the final model is saved without exceeding standard RAM or CPU core constraints.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset split into [deferred] training and [deferred] testing, **When** the training pipeline runs, **Then** it completes 5-fold cross-validation with a grid search over a range of parameter combinations for both linear regression and random forest models.
2. **Given** a random forest model with a specific `max_depth` and `n_estimators`, **When** the model is trained, **Then** the training job completes within 30 minutes on a 2-core CPU environment.
3. **Given** the trained models, **When** the evaluation step runs, **Then** it outputs the R², MAE, and RMSE metrics for the held-out test set.

---

### User Story 3 - Statistical Significance and Feature Importance Analysis (Priority: P3)

The system must perform permutation testing (A sufficient number of iterations will be performed to ensure convergence and stability of the results.) to validate that model performance exceeds random chance and generate feature importance rankings to identify key compositional drivers.

**Why this priority**: This step provides the statistical rigor required to claim that the observed composition-CTE relationship is real and not an artifact of overfitting or noise.

**Independent Test**: Can be fully tested by running the significance analysis script on the trained model and verifying that a p-value is reported for all models (flagging 'Null Result' if R² ≤ 0.3), and that a ranked list of feature importances is generated where the Top-ranked features match the top-ranked features by correlation coefficient magnitude. on a validation set.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** the permutation test (sufficient iterations) runs, **Then** it reports a p-value; if R² > 0.3, the p-value must be < 0.05; otherwise, the system flags a "Null Result" status.
2. **Given** the trained random forest model, **When** the feature importance analysis runs, **Then** it outputs a ranked list of compositional descriptors (e.g., "atomic size mismatch" ranked #1) with their relative importance scores.
3. **Given** a null result (R² ≤ 0.3), **When** the analysis runs, **Then** the system correctly flags the model as not significantly better than random chance and outputs a "Null Result" status.

---

### Edge Cases

- What happens when the API returns no data for a specific alloy family (e.g., Pd-based)? The system must skip that family and log a warning, rather than crashing.
- How does the system handle alloys with undefined or ambiguous chemical formulas? The system must exclude these entries during the ingestion phase.
- What happens if the dataset size exceeds 7 GB RAM? The system must implement a sampling strategy to reduce the dataset to a manageable size (e.g., [deferred] samples) before training.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve CTE and composition data from Materials Project and AFLOWlib APIs, filtering specifically for entries flagged as amorphous or metallic glass, ensuring all available valid entries are collected (See US-1).
- **FR-002**: System MUST extract compositional descriptors including weighted mean atomic radius, electronegativity variance, valence electron concentration, and atomic size mismatch for each alloy (See US-1).
- **FR-003**: System MUST split the dataset into [deferred] training and [deferred] testing sets, stratified by alloy family (Zr-based, Pd-based, Fe-based, etc.); if stratification fails due to class imbalance (empty test sets), the system MUST revert to a random split (See US-1).
- **FR-004**: System MUST train linear regression and random forest models using scikit-learn, performing 5-fold cross-validation with a grid search over a range of parameter combinations (See US-2).
- **FR-005**: System MUST execute a permutation test with 1000 iterations to assess whether model performance exceeds random chance, reporting p-values (See US-3).
- **FR-006**: System MUST generate feature importance rankings for the trained models to identify the most influential compositional descriptors (See US-3).
- **FR-007**: System MUST enforce resource constraints, ensuring the entire pipeline runs on ≤2 CPU cores and ≤7 GB RAM without GPU acceleration (See US-2).

### Key Entities

- **MetallicGlassEntry**: Represents a single alloy sample with attributes for composition (chemical formula), CTE (thermal expansion coefficient), and derived compositional descriptors.
- **ModelPerformance**: Represents the evaluation results of a trained model, including R², MAE, RMSE, and p-values from permutation tests.
- **FeatureImportance**: Represents the ranking of compositional descriptors by their contribution to the model's predictive power.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (R²) is measured against the baseline of a linear weighted average of elemental CTEs on the held-out test set (See US-2).
- **SC-002**: Statistical significance (p-value) of the model's performance is measured against the null hypothesis of random chance via permutation testing (See US-3).
- **SC-003**: Feature importance rankings are measured against the magnitude of correlation coefficients between each descriptor and CTE on a distinct held-out validation set; the Top 3 features by importance must match the Top 3 by correlation coefficient magnitude to pass (See US-3).
- **SC-004**: Computational efficiency (runtime and memory usage) is measured against the GitHub Actions free-tier limits (≤2 cores, ≤7 GB RAM, ≤6 hours) (See US-2).

## Assumptions

- The Materials Project and AFLOWlib APIs provide metallic glass data, with a target of ≥500 entries, but the system must handle fewer entries gracefully.
- The compositional descriptors (weighted mean atomic radius, electronegativity, etc.) are sufficient to capture the non-linear relationships between composition and CTE in amorphous alloys.
- The dataset size can be reduced to ≤10,000 samples via random sampling if the full dataset exceeds 7 GB RAM, without significantly biasing the results.
- The random forest and linear regression models can be trained effectively on CPU without requiring GPU acceleration or specialized hardware.
- The CTE values in the source databases are consistent and comparable across different alloy families, allowing for a unified analysis.
- The mathematical coupling between 'weighted mean atomic radius' and 'atomic size mismatch' is acknowledged; feature importance is interpreted via permutation importance to mitigate multicollinearity effects.