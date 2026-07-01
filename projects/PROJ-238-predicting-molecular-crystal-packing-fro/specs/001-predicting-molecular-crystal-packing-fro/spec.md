# Feature Specification: Predicting Molecular Crystal Packing from Structural Descriptors

**Feature Branch**: `001-predicting-crystal-packing`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Can machine learning models accurately predict key molecular crystal packing features—specifically the packing coefficient and dominant intermolecular interaction types—using only readily computable molecular descriptors as input?"

## User Scenarios & Testing

### User Story 1 - Data Pipeline and Descriptor Computation (Priority: P1)

The researcher needs to ingest raw crystal structure data from the Crystallography Open Database (COD), filtering for valid organic small molecules, and compute a standardized set of molecular descriptors (volume, surface area, dipole moment, H-bond counts, polar surface area) using RDKit to create the foundational dataset for modeling. The packing coefficient is derived from the unit cell volume and molecular volume, not fetched as a raw field.

**Why this priority**: Without a clean, reproducible dataset with computed descriptors and derived targets, no modeling or analysis can occur. This is the prerequisite for all subsequent research steps.

**Independent Test**: Can be fully tested by running the data ingestion script on a sample of COD entries and verifying the output CSV contains non-null values for all 6 required descriptors and the derived packing coefficient.

**Acceptance Scenarios**:

1. **Given** a list of valid COD IDs for organic molecules, **When** the ingestion script runs, **Then** the output dataset contains a sufficient number of rows with no missing values in the `packing_coefficient` column (derived from unit cell and molecular volume).
2. **Given** a crystal structure file (CIF) with missing hydrogen atoms, **When** the descriptor computation step runs, **Then** the system adds hydrogens geometrically before calculating descriptors and logs the integer count of entries requiring hydrogen addition.
3. **Given** a dataset of N molecules where N ≥ 100, **When** the stratified split (70/15/15) is applied by molecular weight, **Then** the distribution of molecular weights in the training, validation, and test sets has a Kolmogorov-Smirnov distance < 0.05.

---

### User Story 2 - Model Training and Baseline Comparison (Priority: P2)

The researcher needs to train Random Forest and Gradient Boosting regressors to predict the packing coefficient and compare their performance against a simple mean-predictor baseline to determine if molecular descriptors provide predictive value.

**Scientific Context**: The packing coefficient is defined as (Molecular Volume / Unit Cell Volume). While Molecular Volume is a direct input feature, the Unit Cell Volume is unknown and must be inferred. The model effectively predicts the denominator, making this a non-trivial physical inference rather than a tautology. The relationship is an association, not causation.

**Why this priority**: This validates the core hypothesis that single-molecule descriptors contain information about crystal packing. It establishes the baseline scientific finding.

**Independent Test**: Can be fully tested by executing the training pipeline on the training set, evaluating on the test set, and verifying that the Random Forest model achieves a statistically significant improvement over the mean-predictor baseline (p < 0.05).

**Acceptance Scenarios**:

1. **Given** the training dataset, **When** the Random Forest model is trained with default hyperparameters, **Then** the model converges within 30 minutes on a 2-CPU environment.
2. **Given** the test dataset, **When** predictions are generated, **Then** the system reports the R² and MAE scores, and a paired t-test against the mean baseline yields a p-value < 0.05.
3. **Given** a paired t-test between the Random Forest predictions and the mean baseline, **Then** the p-value is < 0.05, indicating statistically significant improvement.

---

### User Story 3 - Feature Importance, Sensitivity Analysis, and Interaction Classification (Priority: P3)

The researcher needs to identify which molecular descriptors most influence packing predictions, perform a sensitivity analysis on the model's performance, and classify dominant intermolecular interaction types using geometric criteria extracted from the crystal structure.

**Why this priority**: Understanding *why* the model works (feature importance) and *how stable* the results are (sensitivity) is critical for scientific interpretation. Additionally, classifying interaction types is required to answer the full research question regarding "dominant intermolecular interaction types" mentioned in the original idea.

**Independent Test**: Can be fully tested by generating a feature importance plot, a sensitivity report showing R² stability, and a classification report for interaction types derived from geometric extraction.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** feature importance is calculated, **Then** the top 3 features are identified and their cumulative importance accounts for > 60% of the total.
2. **Given** the top 5 most important features, **When** a sensitivity analysis sweeps the inclusion threshold, **Then** the report explicitly documents the R² variation across the sweep (e.g., ±0.02).
3. **Given** a classification task for interaction types derived from geometric criteria (e.g., H-bond angles > 150°), **When** the model is evaluated, **Then** the accuracy is reported with a 95% confidence interval derived from bootstrapping (multiple resamples).

### Edge Cases

- What happens when a crystal structure in the COD has a reported packing coefficient of 0 or > 1.0 (physically impossible)? The system must filter these out and log the count.
- How does the system handle molecules with extremely high molecular weight (> 1000 Da) that might skew the stratified split? The system must exclude them if they fall outside the high percentile of the training distribution.
- How does the system handle missing dipole moments in the source data? The system must impute using the median of the training set and flag the imputed rows. If the `packing_coefficient` (target) is missing, the system must flag the entry as excluded from training and log the count.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download crystal structure data from the Crystallography Open Database (COD) as the primary and mandatory source. If and only if COD yields an insufficient number of valid organic small molecules meeting the inclusion criteria, the system MAY fallback to the CSD Community subset to reach the minimum sample size threshold. The system MUST derive the `packing_coefficient` from unit cell volume and molecular volume (See US-1).
- **FR-002**: System MUST compute at least 6 distinct molecular descriptors (volume, surface area, dipole moment, H-bond donor count, H-bond acceptor count, polar surface area) using RDKit for every molecule in the dataset (See US-1).
- **FR-003**: System MUST split the dataset into training, validation, and test sets using stratification by molecular weight to prevent distributional drift (See US-1).
- **FR-004**: System MUST train at least two regression models (Random Forest and Gradient Boosting) and one baseline (mean predictor) using scikit-learn without GPU acceleration (See US-2).
- **FR-005**: System MUST evaluate model performance using R², MAE, and RMSE metrics and perform a paired t-test against the baseline to establish statistical significance (See US-2).
- **FR-006**: System MUST generate a feature importance report identifying the top contributing descriptors and a sensitivity analysis showing performance stability across feature subsets (See US-3).
- **FR-007**: System MUST handle missing data by imputing auxiliary descriptors (e.g., dipole) with the training set median and flagging the row. If the critical target (`packing_coefficient`) is missing, the system MUST exclude the entry from training and log the count (See US-1, US-2).
- **FR-008**: System MUST classify dominant intermolecular interaction types using geometric criteria (e.g., H-bond distance < 3.5Å and angle > 150°) extracted from the crystal structure data, as no pre-existing labels exist in the source (See US-3).

### Key Entities

- **Molecule**: Represents a single organic small molecule; attributes include molecular weight, molecular formula, computed descriptors (volume, dipole, etc.), and source ID.
- **CrystalStructure**: Represents the experimental lattice data; attributes include unit cell volume, space group, and dominant intermolecular interaction type (derived via geometric criteria).
- **ModelResult**: Represents the output of a training run; attributes include model type, hyperparameters, R² score, MAE, and feature importance vector.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive accuracy (R²) is measured against the baseline mean predictor to determine if molecular descriptors provide statistically significant value (See FR-005, US-2).
- **SC-002**: Computational feasibility is measured against the GitHub Actions free-tier limit (2 CPU, ~7 GB RAM, ≤6 hours) to ensure the entire pipeline completes without resource exhaustion (See FR-004, US-2).
- **SC-003**: Feature stability is measured against a sensitivity analysis where removing the top 2 least important features results in an R² drop of no more than 10% (See FR-006, US-3).
- **SC-004**: Dataset representativeness is measured against the Kolmogorov-Smirnov test to ensure the training, validation, and test sets have statistically similar molecular weight distributions (See FR-003, US-1).
- **SC-005**: Methodological rigor is measured by the presence of a multiple-comparison correction (e.g., Bonferroni or FDR) when comparing ≥2 models (RF and GB) against the baseline (See FR-005, US-2).

## Assumptions

- The Crystallography Open Database (COD) contains a sufficient number of organic small molecules (N ≥ 1,000) with both valid crystal structures and reported unit cell parameters to derive packing coefficients for training a machine learning model.
- The "dominant intermolecular interaction type" can be reliably extracted from the crystal structure data using geometric criteria (e.g., distance and angle cutoffs) without requiring additional experimental data not present in the source files.
- The relationship between single-molecule descriptors and crystal packing is sufficiently strong to be captured by non-linear models (Random Forest/Gradient Boosting) without requiring complex many-body simulations.
- The analysis assumes an observational design; therefore, all findings regarding "prediction" are framed as associational, not causal, as no randomization of crystal conditions is performed.
- The RDKit library is available in the standard Python environment and can compute all required descriptors (dipole moment, surface area, etc.) within the 6-hour job limit.
- If the source dataset lacks specific variables required for the interaction type classification (e.g., specific hydrogen bond angles), the project will proceed with the available variables and record the limitation in the final report.