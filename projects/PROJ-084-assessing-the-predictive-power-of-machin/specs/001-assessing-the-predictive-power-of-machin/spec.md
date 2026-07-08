# Feature Specification: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

**Feature Branch**: `001-assess-ml-predictive-power`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction Pipeline (Priority: P1)

A researcher needs to ingest the raw USPTO reaction yield dataset, sanitize the chemical structures, and generate standardized molecular fingerprints (ECFP4 and MACCS) to create a clean, analysis-ready dataset for classical machine learning models.

**Why this priority**: Without a validated, clean dataset with correctly computed features, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a subset of the USPTO data and verifying that the output CSV contains valid SMILES, non-null fingerprint vectors, and the correct yield values without requiring any model training.

**Acceptance Scenarios**:

1. **Given** a raw USPTO dataset file containing SMILES and yield values, **When** the preprocessing script is executed, **Then** the output file contains sanitized SMILES with salts removed and standardized reaction components.
2. **Given** a sanitized reaction entry, **When** the fingerprint generation module runs, **Then** the output includes both ECFP (2048-bit) and MACCS (167-bit) vectors that are non-null and match the expected dimensionality.
3. **Given** a reaction with missing or malformed yield data, **When** the preprocessing script runs, **Then** that entry is excluded from the final dataset with a log entry recording the exclusion reason.

---

### User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

A researcher needs to train Random Forest and Support Vector Machine (SVM) regressors on the extracted fingerprints, automatically tuning hyperparameters via grid search with cross-validation to identify the best-performing model configuration for yield prediction.

**Why this priority**: This step establishes the baseline predictive performance. It determines whether classical ML methods can achieve the expected R² range (0.4–0.6) before investing effort in detailed analysis or feature importance extraction.

**Independent Test**: The training module can be tested by running the grid search on a small, fixed validation subset and verifying that the best hyperparameters are selected and the model achieves a measurable R² score on the validation set.

**Acceptance Scenarios**:

1. **Given** a training set of fingerprint vectors and yield labels, **When** the Random Forest training script runs with grid search, **Then** the system selects the optimal number of trees and max depth based on 5-fold cross-validation performance on the training set.
2. **Given** a training set, **When** the SVM training script runs with kernel selection (linear, RBF), **Then** the system identifies the optimal C parameter and kernel type that maximize validation R².
3. **Given** a trained model, **When** the system evaluates it on the held-out validation set, **Then** the system reports R², RMSE, and MAE metrics that are consistent with the cross-validation estimates (within ±0.05).

---

### User Story 3 - Generalization and Feature Importance Analysis (Priority: P3)

A researcher needs to evaluate how well the trained models generalize across different reaction classes (e.g., Suzuki coupling vs. amide formation) and identify which specific molecular substructures (fingerprint bits) are most predictive of high yields.

**Why this priority**: This analysis addresses the core research question regarding structural determinants and generalization. It provides the interpretability and chemical insight that distinguishes this study from a simple black-box prediction task.

**Independent Test**: The analysis can be tested by running the evaluation script on the test set and generating a report that includes per-class R² scores and a ranked list of top predictive fingerprint bits, without requiring manual intervention.

**Acceptance Scenarios**:

1. **Given** a trained model and a test set stratified by reaction class, **When** the generalization evaluation runs, **Then** the system outputs R² and RMSE metrics for each reaction class separately.
2. **Given** a trained Random Forest model, **When** the feature importance analysis runs, **Then** the system identifies the top fingerprint bits contributing most to yield prediction using permutation importance.
3. **Given** the feature importance results, **When** the system maps bits back to molecular substructures, **Then** the output includes at least 3 interpretable chemical substructures (e.g., specific functional groups) with their associated importance scores.

---

### Edge Cases

- What happens when the USPTO dataset contains duplicate reactions with conflicting yield values? (System must handle by averaging or selecting the most frequent value, with logging).
- How does the system handle reactions where the yield is reported as a range (e.g., "50-60%") rather than a single value? (System must either exclude these or parse the midpoint, with explicit handling documented).
- How does the system handle reactions with missing reagent information? (System must exclude these entries during preprocessing to ensure valid fingerprint generation).
- What happens if the stratified split results in a reaction class with fewer than 10 samples in the test set? (System must either merge small classes or exclude them from per-class analysis, with a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the USPTO reaction yield dataset (a large-scale collection of reactions) and parse SMILES strings and yield values into a structured format (See US-1).
- **FR-002**: System MUST sanitize molecules by removing salts and standardizing reaction components using RDKit before fingerprint generation (See US-1).
- **FR-003**: System MUST generate both ECFP fingerprints (with standard bit lengths) and MACCS fingerprints for all reactants and reagents in the dataset (See US-1).
- **FR-004**: System MUST split the dataset into training, validation, and test sets using a scaffold-based split (grouping by reactant core) to prevent data leakage, with split ratios deferred to implementation (See US-2). The system MUST log the exact split ratios used in the final report.
- **FR-005**: System MUST train Random Forest and SVM regressors with grid search hyperparameter tuning using cross-validation on the training set to select the best model configuration, then evaluate on the held-out validation set (See US-2).
- **FR-006**: System MUST evaluate model performance on the held-out test set using R², RMSE, and MAE metrics (See US-2).
- **FR-007**: System MUST compute per-reaction-class performance metrics to assess generalization across chemical space (See US-3).
- **FR-008**: System MUST extract feature importance scores using permutation importance and map the top bits to reaction centers and associated substructures, explicitly acknowledging potential bit collisions (See US-3).
- **FR-009**: System MUST ensure all data processing and model training runs within ≤ 7.0 GB RAM (targeting free-tier CI runner limits) by processing data in batches where necessary (See US-2).
- **FR-010**: System MUST avoid GPU-dependent operations and use only CPU-tractable methods (scikit-learn, RDKit) to ensure compatibility with free-tier CI runners (See US-2).

### Key Entities

- **Reaction**: Represents a single organic reaction instance with associated SMILES strings for reactants/reagents and a numeric yield value.
- **Fingerprint**: A binary vector representation (ECFP4 or MACCS) derived from a reaction's molecular structure, used as input features for ML models.
- **Model**: A trained regression model (Random Forest or SVM) with specific hyperparameters, capable of predicting yield from fingerprints.
- **PerformanceMetric**: A record of model evaluation results (R², RMSE, MAE) for a specific dataset split or reaction class.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The best-performing model achieves an R² ≥ 0.40 on the held-out test set to demonstrate sufficient signal in classical fingerprints for yield prediction (See US-2).
- **SC-002**: The generalization gap (difference in R² between training and test sets) must be ≤ 0.10 for all reaction classes with n > 20 samples to ensure model robustness (See US-3).
- **SC-003**: The top 3 predictive molecular substructures must be present in >80% of high-yield reactions within a held-out validation set to validate interpretability against empirical data (See US-3).
- **SC-004**: The computational resource usage (RAM peak, runtime) is measured against the ≤ 7.0 GB RAM and -hour time limit constraints to ensure feasibility on free-tier CI runners (See US-2).
- **SC-005**: The fraction of reactions excluded during preprocessing due to missing or malformed data is measured to assess data quality and potential bias in the final dataset (See US-1).

## Assumptions

- The USPTO reaction yield dataset is accessible via the provided DOI link and can be downloaded using `wget` without authentication barriers.
- The RDKit library is available in the CI environment and supports all required fingerprint generation functions (ECFP4, MACCS) without additional compilation steps.
- The dataset contains sufficient reactions per class to allow meaningful scaffold-based splitting; classes with insufficient samples will be merged or excluded from per-class analysis.
- Yield values in the dataset are reported as single numeric values or can be reliably parsed from ranges; entries with unparseable yields will be excluded.
- The computational complexity of Random Forest and SVM training on the full dataset (after fingerprint generation) will not exceed the specified runtime limit on a multi-core CPU runner..
- The scaffold-based split strategy (FR-004) is sufficient to prevent data leakage from identical reactions appearing in both training and test sets.
- The "reaction class" labels in the dataset are sufficiently granular to enable meaningful generalization analysis but not so granular that some classes become empty after splitting.