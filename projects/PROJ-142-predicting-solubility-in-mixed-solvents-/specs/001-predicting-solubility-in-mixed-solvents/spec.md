# Feature Specification: Predicting Solubility in Mixed Solvents with Machine Learning

**Feature Branch**: `001-predicting-solubility-mixed-solvents`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Predicting Solubility in Mixed Solvents with Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1)

As a computational chemist, I need to ingest raw solubility data from MoleculeNet and EPA DSSTox, compute molecular descriptors using RDKit, and generate composition-weighted solvent descriptors for binary and ternary mixtures so that I have a clean, structured dataset ready for model training.

**Why this priority**: This is the foundational step; without a validated dataset containing solute fingerprints, solvent properties, and interaction terms, no modeling or evaluation can occur. It directly addresses the "Data acquisition" and "Feature engineering" phases of the methodology.

**Independent Test**: The pipeline can be tested by running the data processing script on a small subset of the input files and verifying that the output CSV contains the expected columns (solute SMILES, solvent descriptors, mixture composition, calculated interaction terms) and that the row count matches the filtered dataset size (MW < 500 Da, valid mixtures).

**Acceptance Scenarios**:
1. **Given** raw CSV files from MoleculeNet and DSSTox, **When** the ingestion script filters for molecules with MW < 500 Da and valid binary/ternary mixtures, **Then** the output dataset contains only valid rows and excludes entries with missing composition ratios.
2. **Given** a valid mixture entry, **When** the system calculates composition-weighted solvent descriptors, **Then** the resulting values are mathematically consistent with the input solvent properties and mole fractions (e.g., weighted average equals sum of (property * fraction)).
3. **Given** the processed dataset, **When** the system generates interaction terms (e.g., product of solute-solvent polarity), **Then** these new columns are present and contain non-null numeric values for all rows.

---

### User Story 2 - Model Training and Baseline Comparison (Priority: P2)

As a researcher, I need to train Gradient Boosting and Random Forest models on the engineered features and compare their performance against a baseline Abraham solvation parameter model so that I can determine if non-linear mixing effects improve prediction accuracy.

**Why this priority**: This addresses the core research question regarding the effectiveness of interaction terms and non-linear models versus traditional linear approaches. It is the primary mechanism for generating the "Expected results" (RMSE, R²).

**Independent Test**: The training pipeline can be tested by executing the model training script with a fixed random seed and a small hyperparameter grid, verifying that the output includes trained model artifacts and a comparison report showing RMSE and R² for both the ML models and the Abraham solvation parameter model baseline.

**Acceptance Scenarios**:
1. **Given** the preprocessed training dataset, **When** the system trains the XGBoost and Random Forest models with 5-fold cross-validation, **Then** the training completes within the 6-hour CI limit and produces model files.
2. **Given** the hold-out test set, **When** the system evaluates the trained models and the Abraham solvation parameter model baseline, **Then** the output report includes RMSE, MAE, and R² metrics for all three approaches.
3. **Given** the evaluation results, **When** the system performs a Wilcoxon signed-rank test on absolute errors, **Then** the report indicates statistical significance (p < 0.05) or non-significance clearly.

---

### User Story 3 - Interpretability and Interaction Term Analysis (Priority: P3)

As a process engineer, I need to visualize feature importances (SHAP values) and identify which specific interaction terms (e.g., polarity-polarity products) most significantly drive solubility predictions so that I can understand the physical mechanisms of non-linear mixing.

**Why this priority**: This addresses the "How" part of the research question, providing the mechanistic insight required to fill the literature gap. It transforms a "black box" prediction into actionable chemical knowledge.

**Independent Test**: The analysis can be tested by generating SHAP summary plots and feature importance tables from the trained best-performing model, verifying that specific interaction terms are ranked and visualized.

**Acceptance Scenarios**:
1. **Given** a trained model, **When** the system computes SHAP values, **Then** the output includes a summary plot and a table ranking features by absolute mean SHAP value.
2. **Given** the ranked features, **When** the system filters for interaction terms, **Then** the report explicitly lists the top 5 interaction terms contributing to the model's variance.
3. **Given** the top interaction terms, **When** the system visualizes predicted vs. experimental solubility for mixtures dominated by these terms, **Then** the visualization shows the model's ability to capture non-linear trends in these specific subsets.

---

### Edge Cases

- **What happens when** a mixture composition sum does not equal 1.0 (within floating point tolerance)? **The system** must reject the row or normalize the composition and log a warning, ensuring no invalid stoichiometry propagates to the model.
- **How does the system handle** missing solvent property data (e.g., dielectric constant) for a specific solvent in the CRC Handbook? **The system** must trigger KNN imputation; if KNN fails due to insufficient neighbors, the row must be dropped and logged.
- **What happens when** the dataset size is too small to support a meaningful 80/20 split while maintaining stratification by solvent system? **The system** must fallback to a leave-one-out or k-fold cross-validation strategy for the final evaluation and record this deviation in the assumptions log.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest solubility data from MoleculeNet and EPA DSSTox, filter for molecules with MW < 500 Da, and retain only binary/ternary mixtures with known composition ratios (See US-1).
- **FR-002**: System MUST compute molecular descriptors (Morgan fingerprints, topological indices) using RDKit and generate composition-weighted solvent descriptors for each mixture entry (See US-1).
- **FR-003**: System MUST append explicit interaction terms (e.g., polynomial, ratio, or learned combinations of solute-solvent descriptors) to the feature set to capture non-linear mixing effects, and report the specific forms used (See US-1).
- **FR-004**: System MUST train Gradient Boosting (XGBoost) and Random Forest regressors using scikit-learn with 5-fold cross-validation and a hyperparameter grid limited to ≤30 minutes per trial (See US-2).
- **FR-005**: System MUST evaluate models against an Abraham solvation parameter model baseline and perform a Wilcoxon signed-rank test on absolute errors with α = 0.05 (See US-2).
- **FR-006**: System MUST generate SHAP-based feature importance plots and identify top interaction terms driving predictions (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on the SHAP magnitude cutoff (thresholds ∈ {0.01, 0.05, 0.1}) by identifying the top 5 interaction terms at each threshold, calculating the Jaccard similarity between every pair of these sets, and reporting the minimum Jaccard similarity observed (See US-3).
- **FR-008**: System MUST log a warning and abort the job if peak memory usage exceeds 7 GB or if disk usage exceeds 14 GB (See US-2).

### Key Entities

- **SolubilityRecord**: Represents a single experimental measurement; key attributes include solute SMILES, solvent identities, mixture composition (mole fractions), experimental solubility value (logS), and source dataset ID.
- **MolecularDescriptor**: Represents computed features for a molecule; key attributes include Morgan fingerprint bit vector, topological indices, and molecular weight.
- **InteractionTerm**: Represents a derived feature capturing non-linear mixing; key attributes include the two parent descriptors being combined and the mathematical operation (e.g., product, ratio, polynomial).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model prediction accuracy (RMSE and R²) is measured against the Abraham solvation parameter model baseline on the hold-out test set. Success requires a relative RMSE improvement ≥ 5% and statistical significance (p < 0.05) via Wilcoxon signed-rank test (See US-2).
- **SC-002**: Feature importance stability is measured by comparing SHAP values across different cross-validation folds using Spearman rank correlation; success requires a correlation coefficient > 0.8 (See US-3).
- **SC-003**: Computational feasibility is measured by verifying total runtime and peak memory usage against the GitHub Actions free-tier limits (≤6 hours, ≤7 GB RAM) to ensure the analysis is reproducible in CI (See US-2).
- **SC-004**: Methodological soundness is measured by the sensitivity analysis on SHAP thresholds, requiring the minimum Jaccard similarity between the top-5 interaction term sets (across thresholds {0.01, 0.05, 0.1}) to be ≥ 0.6 (See US-3).
- **SC-005**: Data integrity is measured by the percentage of rows successfully imputed via KNN versus dropped; success requires an imputation rate < 15% (See US-1).

## Assumptions

- The MoleculeNet and EPA DSSTox datasets contain sufficient overlap of small organic molecules (MW < 500 Da) with binary/ternary mixture data to support a meaningful train/test split without extreme class imbalance.
- The CRC Handbook solvent property tables (dielectric constant, dipole moment) are complete for all solvents appearing in the solubility datasets; any missing values are amenable to KNN imputation without introducing significant bias.
- The "Abraham solvation parameter model" baseline can be implemented using the `solv` Python package or a comparable open-source library without requiring proprietary data or GPU acceleration.
- The non-linear mixing effects are sufficiently captured by the interaction terms defined in FR-003 (polynomial, ratio, or learned); the model will report the specific forms used to allow for physical interpretation.
- The dataset size, even after filtering for MW < 500 Da and valid mixtures, is large enough (N > 100) to support 5-fold cross-validation and a separate hold-out test set without severe overfitting risks.
- All required Python libraries (RDKit, XGBoost, scikit-learn, SHAP) are available in the GitHub Actions environment or can be installed within the standard 6-hour job window.
- The sensitivity analysis (FR-007) is a robustness check to ensure that the identification of "top interaction terms" is not an artifact of a single arbitrary SHAP magnitude cutoff; success is defined by a minimum Jaccard similarity of 0.6 between the sets of top-5 terms found at different thresholds.