# Feature Specification: Predicting Crystal Structures from Molecular Fingerprints

**Feature Branch**: `001-predict-crystal-structures`  
**Created**: 2026-08-26  
**Status**: Draft  
**Input**: User description: "Predicting Crystal Structures from Molecular Fingerprints"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

The researcher downloads a filtered subset of the Crystallography Open Database (COD), parses the CIF files to extract canonical SMILES strings, and generates 2048-bit ECFP4 fingerprints alongside ground-truth lattice parameters and space groups.

**Why this priority**: This is the foundational step; without a clean, aligned dataset of 2D descriptors and 3D targets, no modeling or analysis can occur. It directly addresses the data acquisition and feature engineering requirements.

**Independent Test**: Can be fully tested by running the data pipeline script on a small sample (e.g., 100 files) and verifying that the output CSV contains non-null values for SMILES, fingerprint bit vectors, lattice parameters, and space groups for every row.

**Acceptance Scenarios**:

1. **Given** a directory of COD CIF files filtered by size (< 500MB total), **When** the ingestion script runs, **Then** a single CSV file is produced where every row contains a valid SMILES string, a 2048-bit fingerprint array, and numeric lattice parameters.
2. **Given** a CIF file with missing or malformed crystallographic data, **When** the ingestion script runs, **Then** that file is skipped, logged as an error, and excluded from the final dataset without crashing the pipeline.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The researcher trains Random Forest and Gradient Boosting classifiers for space group prediction and Ridge Regression models for lattice parameter volume on the generated dataset, using a scaffold-based split to prevent data leakage.

**Why this priority**: This implements the core hypothesis testing mechanism. It determines if molecular fingerprints contain sufficient signal for prediction, directly addressing the research question.

**Independent Test**: Can be fully tested by executing the training script on the prepared dataset and verifying that the output includes accuracy/F1 scores for classification and R-squared/MAE for regression, with no data leakage detected between train/test sets.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with scaffold-based train/test splits, **When** the model training script executes, **Then** the system outputs performance metrics (Accuracy, F1, R², MAE) for both the classifier and regressor models.
2. **Given** a model training run that exceeds 3 hours on the GitHub Actions runner, **When** the timeout threshold is approached, **Then** the script automatically reduces the dataset size to [deferred] samples or limits tree depth to ensure completion within the 6-hour job limit.

---

### User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

The researcher analyzes the trained models using permutation importance and SHAP values to identify which specific molecular substructures (fingerprint bits) contribute most to the prediction of space groups and lattice parameters.

**Why this priority**: This addresses the second part of the research question ("which molecular features carry the most predictive signal"). It transforms raw predictive performance into interpretable scientific insights.

**Independent Test**: Can be fully tested by running the analysis script and verifying that a ranked list of top-contributing fingerprint bits and their corresponding chemical substructures is generated.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the feature importance analysis runs, **Then** a report is generated listing the top 20 fingerprint bits ranked by permutation importance.
2. **Given** a specific fingerprint bit identified as highly important, **When** the substructure mapping runs, **Then** the system outputs the corresponding chemical substructure (e.g., aromatic ring, hydrogen bond donor) associated with that bit.

### Edge Cases

- What happens if the COD subset contains molecules with identical SMILES but different space groups (polymorphism)? The system must handle this by treating them as distinct samples in the dataset, acknowledging that 2D fingerprints alone cannot distinguish these cases (a null result signal).
- How does the system handle space groups with very low frequency (e.g., rare symmetry classes)? The classifier must report per-class F1 scores to ensure performance isn't skewed by the majority class.
- What if the GitHub Actions runner runs out of memory during the fingerprint generation for large molecules? The system must catch the `MemoryError`, log the offending molecule ID, and exclude it from the dataset to allow the rest of the pipeline to complete.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the organic subset of the Crystallography Open Database (COD) and filter for files totaling < 500MB to ensure data fits within the 14GB disk constraint (See US-1).
- **FR-002**: System MUST parse CIF files using Open Babel to extract canonical SMILES and generate 2048-bit ECFP4 fingerprints for each molecule (See US-1).
- **FR-003**: System MUST perform a scaffold-based split ([deferred] train, [deferred] test) using the Bemis-Murcko algorithm to ensure no molecular scaffolds leak between training and testing sets (See US-2).
- **FR-004**: System MUST train a Random Forest classifier and a Gradient Boosting classifier for space group prediction, and a Ridge Regression model for lattice parameter volume (See US-2).
- **FR-005**: System MUST calculate and report classification metrics (Accuracy, Macro-F1) and regression metrics (R-squared, MAE) on the held-out test set (See US-2).
- **FR-006**: System MUST compute permutation importance and SHAP values to identify the top predictive molecular substructures (See US-3).
- **FR-007**: System MUST enforce a hard timeout of 6 hours on the training job; if exceeded, the system MUST automatically reduce the dataset to [deferred] random samples or limit the number of trees to 100 to ensure completion (See US-2).

### Key Entities

- **MoleculeRecord**: Represents a single chemical entry containing the canonical SMILES, the 2048-bit ECFP4 fingerprint vector, the ground-truth space group label, and the lattice parameter volume.
- **ModelMetrics**: Represents the evaluation results containing Accuracy, Macro-F1, R-squared, and MAE values for a specific model configuration.
- **FeatureImportance**: Represents the mapping between a specific fingerprint bit index, its calculated importance score, and the identified chemical substructure.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The predictive accuracy (Accuracy and Macro-F1) of the space group classifier is measured against a random baseline to determine if molecular fingerprints contain signal beyond chance (See US-2).
- **SC-002**: The regression performance (R-squared and MAE) for lattice parameter volume is measured against the variance of the target variable in the test set to assess predictive utility (See US-2).
- **SC-003**: The interpretability analysis is measured by the generation of a ranked list of at least 20 fingerprint bits with corresponding chemical substructure annotations (See US-3).
- **SC-004**: The computational feasibility is measured by the successful completion of the entire pipeline (data ingestion, training, analysis) within the 6-hour GitHub Actions free-tier time limit (See US-2).
- **SC-005**: The data leakage prevention is measured by verifying that the scaffold-based split results in zero shared Bemis-Murcko scaffolds between the training and test sets (See US-2).

## Assumptions

- The Crystallography Open Database (COD) organic subset contains sufficient variables (SMILES, lattice parameters, space groups) to perform the analysis; if specific covariates are missing, the analysis will proceed with available data only.
- The GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) is sufficient to process the filtered < 500MB dataset and train the specified scikit-learn models without GPU acceleration.
- The relationship between 2D molecular topology and 3D crystal packing is treated as associational; the study does not claim causal determination due to the observational nature of the dataset and the presence of polymorphism.
- The ECFP4 fingerprint radius (2) and bit length (2048) are sufficient to capture the relevant topological features for the initial screening; if performance is poor, this is a limitation of the descriptor, not the methodology.
- The "organic subset" of COD is defined by standard chemical filtering (e.g., presence of C, H, O, N) and excludes inorganic crystals, as the project focuses on organic molecular packing.
- The Bemis-Murcko scaffold algorithm correctly identifies the core ring systems and linkers for the purpose of splitting, ensuring a realistic test of generalization to new chemotypes.
