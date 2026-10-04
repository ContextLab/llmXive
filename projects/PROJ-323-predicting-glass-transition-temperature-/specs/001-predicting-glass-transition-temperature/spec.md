# Feature Specification: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

**Feature Branch**: `001-predict-tg-from-composition`  
**Created**: 2026-07-22  
**Status**: Draft  
**Input**: User description: "Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines"

## Constitution

To ensure scientific rigor and data integrity, this project adheres to the following principles:

- **Principle I (Data Integrity)**: All raw data must be downloaded from primary sources (Polymer Genome Project, NIST) and checksummed before processing.
- **Principle II (Verified Accuracy)**: Any literature values used for validation must be sourced from a curated `data/` directory populated from primary literature, not hardcoded in code.
- **Principle III (Local Data)**: All validation datasets (e.g., WLF constants, physical properties) must reside in the project's `data/` directory and be version-controlled.
- **Principle IV (Independent Validation)**: Validation metrics must be derived from physical properties independent of the target variable ($T_g$) to avoid circular reasoning.
- **Principle V (Reproducibility)**: All calculations, including derived physical properties, must be reproducible via documented algorithms (e.g., Van Krevelen group contribution).
- **Principle VI (Physical Consistency Validation)**: Feature importance MUST be validated against independent physical properties (Fractional Free Volume, Chain Stiffness) calculated via group contribution methods, ensuring the model learns physical constraints rather than statistical artifacts.

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Descriptor Engineering (Priority: P1)

The researcher MUST be able to download raw polymer data from the Polymer Genome Project and NIST WebBook, filter for amorphous homopolymers and binary blends, and convert SMILES strings into a structured feature matrix containing elemental mass fractions, functional group counts, and estimated molecular weight averages.

**Why this priority**: Without a clean, engineered dataset, no modeling can occur. This is the foundational step that transforms unstructured chemical data into the inputs required for the EBM. It is independently testable by verifying the existence of the feature matrix and the correctness of the descriptor calculations against a known subset of polymers.

**Independent Test**: Run the data ingestion script on a small, hardcoded subset of 10 known polymers and verify that the output CSV contains the correct calculated descriptors (e.g., verify elemental mass fraction sums to ~1.0), that rows with missing $T_g$ values are correctly filtered out, and that features are normalized using StandardScaler.

**Acceptance Scenarios**:

1. **Given** a list of polymer IDs from the Polymer Genome Project, **When** the ingestion script executes, **Then** the system downloads the data, filters for amorphous homopolymers, and outputs a CSV with $T_g$ values and SMILES strings.
2. **Given** a CSV of SMILES strings, **When** the descriptor engine runs, **Then** the system calculates elemental mass fractions, functional group counts, and molecular weight averages, storing them in a normalized feature matrix.
3. **Given** a dataset with missing values, **When** the preprocessing step runs, **Then** the system imputes missing numerical features using the median strategy, normalizes features using StandardScaler, and logs the number of imputed values per feature.

---

### User Story 2 - EBM Training and Feature Interaction Discovery (Priority: P2)

The researcher MUST be able to train an Explainable Boosting Machine (EBM) on the engineered dataset to identify non-linear main effects and second-order interactions, producing a model that explains the variance in $T_g$ and generates interpretable shape functions.

**Why this priority**: This is the core analytical engine. While the data (US-1) is necessary, the value proposition lies in the *interpretability* of the EBM compared to black-box models. This can be tested independently by training the model on the P1 output and verifying that the resulting model object contains interpretable main effect and interaction terms.

**Independent Test**: Train the EBM on the P1 dataset using 5-fold cross-validation; verify that the model converges within the 6-hour time limit, that the R² score on the validation set is > 0.0 (indicating non-random performance), and that the model object exposes a method to retrieve the top 5 feature interactions.

**Acceptance Scenarios**:

1. **Given** the preprocessed feature matrix and target vector, **When** the EBM training script runs with 5-fold cross-validation, **Then** the system selects the optimal regularization parameter ($\lambda$) and interaction depth, saving the best model to disk.
2. **Given** the trained EBM model, **When** the system generates partial dependence plots, **Then** the system outputs visualizations showing the non-linear relationship between specific compositional descriptors and $T_g$.
3. **Given** the trained model, **When** the system calculates permutation importance, **Then** the system ranks the top 3-5 descriptors and reports their contribution to the model's predictive power.

---

### User Story 3 - Validation Against Physical Metrics and Sensitivity Analysis (Priority: P3)

The researcher MUST be able to validate the EBM's feature importance rankings against independent physical properties (Fractional Free Volume and Chain Stiffness) derived from group contribution methods and perform a sensitivity analysis on the top descriptors to ensure robustness against noise.

**Why this priority**: This step ensures scientific validity and distinguishes the project from a simple curve-fitting exercise. It confirms that the "explanations" provided by the EBM align with established physical chemistry principles (Free Volume Theory) without circular validation against the target variable. It is independently testable by comparing the model's top features against the external physical property dataset and observing the variance in predictions under perturbation.

**Independent Test**: Load the top 3 features identified by the EBM, cross-reference them with the `data/physical_properties.csv` dataset (containing FFV and Chain Stiffness calculated via Van Krevelen methods), and verify that a $\pm 10\%$ perturbation of these features results in a predictable, monotonic shift in predicted $T_g$ without catastrophic failure.

**Acceptance Scenarios**:

1. **Given** the ranked feature importance list from the EBM, **When** the validation script runs, **Then** the system correlates the top features with the FFV and Chain Stiffness values in `data/physical_properties.csv` and reports a correlation coefficient.
2. **Given** the trained EBM model, **When** the sensitivity analysis script perturbs the top 3 descriptors by $\pm 10\%$, **Then** the system reports the standard deviation of the predicted $T_g$ shifts and confirms the model remains stable (no NaNs or infinite values).
3. **Given** the final model, **When** the system generates a report, **Then** the report includes a statement on whether the identified structure-property relationships are consistent with Free Volume Theory expectations.

---

### Edge Cases

- **What happens when** the Polymer Genome Project API or NIST WebBook is temporarily unavailable? The system MUST retry the download up to 3 times with a 30-second backoff before failing gracefully with a clear error message indicating which dataset was unreachable.
- **How does the system handle** polymers in the dataset with SMILES strings that RDKit fails to parse? The system MUST log the specific SMILES string and the parsing error, exclude the row from the feature matrix, and continue processing the remaining valid rows without crashing.
- **What happens when** the dataset size exceeds the 7 GB RAM limit of the GitHub Actions runner? The system MUST implement chunked processing or random sampling (e.g., retaining a representative subset) to ensure the analysis completes within the 6-hour time limit.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download polymer $T_g$ data from the Polymer Genome Project and NIST WebBook, filtering specifically for amorphous homopolymers and binary blends, and output a clean CSV with SMILES and $T_g$ values (See US-1).
- **FR-002**: System MUST convert SMILES strings to molecular graphs using RDKit (CPU-only) and compute compositional descriptors including elemental mass fractions, functional group counts, and estimated molecular weight averages (See US-1).
- **FR-003**: System MUST train an Explainable Boosting Machine (EBM) with main effects and second-order interactions enabled, performing 5-fold cross-validation to tune regularization ($\lambda$) and interaction depth (See US-2).
- **FR-004**: System MUST generate partial dependence plots and shape functions for all main effects and top interactions to visualize non-linear structure-property relationships (See US-2).
- **FR-005**: System MUST validate the model's feature importance rankings against independent physical properties (Fractional Free Volume and Chain Stiffness) sourced from `data/physical_properties.csv` and perform a sensitivity analysis by perturbing top features by $\pm 10\%$ (See US-3).
- **FR-006**: System MUST handle missing values in the dataset using a median imputation strategy and normalize features using StandardScaler before training (See US-1).
- **FR-007**: System MUST enforce a hard time limit of 6 hours and memory limit of 7 GB RAM, automatically switching to a sampled subset if the full dataset exceeds these constraints (See US-1, US-2).
- **FR-008**: System MUST calculate Fractional Free Volume (FFV) and Chain Stiffness metrics for all polymers in the dataset using the Van Krevelen group contribution method, storing the results in `data/physical_properties.csv` with a checksum to ensure data integrity (See US-3).

### Key Entities

- **PolymerRecord**: Represents a single polymer entry, containing attributes: `smiles_string`, `experimental_tg`, `polymer_class`, `source_id`.
- **CompositionalDescriptor**: Represents the engineered feature set for a polymer, containing attributes: `elemental_mass_fractions` (map), `functional_group_counts` (map), `estimated_mw`, `normalized_features` (vector).
- **EBMModel**: Represents the trained machine learning model, containing attributes: `main_effects` (list of functions), `interactions` (list of pairs), `hyperparameters`, `performance_metrics` (R², RMSE).
- **PhysicalProperty**: Represents derived physical metrics, containing attributes: `polymer_id`, `ffv` (float), `chain_stiffness` (float), `calculation_method` (string).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The predictive performance (R²) of the EBM on the held-out test set is measured against the baseline of a simple linear regression model; the EBM R² must exceed the linear baseline by at least 0.05 (5 percentage points) to demonstrate added value (See FR-003, US-2).
- **SC-002**: The correlation coefficient between the EBM's top 3 feature importance rankings and the independent physical properties (FFV, Chain Stiffness) in `data/physical_properties.csv` is measured against the hypothesis that specific compositional descriptors align with Free Volume Theory (See FR-005, US-3).
- **SC-003**: The stability of the model's predictions is measured by calculating the standard deviation of $T_g$ shifts when top features are perturbed by $\pm 10\%$, ensuring the model does not overfit to noise (See FR-005, US-3).
- **SC-004**: The computational feasibility is measured by verifying the total runtime of the end-to-end pipeline (download, engineer, train, validate) is $\le$ 6 hours on a standard GitHub Actions free-tier runner (See FR-007, US-1).
- **SC-005**: The interpretability is measured by the successful generation of partial dependence plots for at least 3 identified key descriptors, confirming the presence of non-linear relationships (See FR-004, US-2).

## Assumptions

- **Assumption about data availability**: The Polymer Genome Project and NIST Chemistry WebBook provide sufficient data points (N > 500) for amorphous homopolymers and binary blends with reported $T_g$ values to train a statistically significant EBM model.
- **Assumption about variable fit**: The compositional descriptors derived from SMILES (elemental fractions, functional groups) contain the necessary information to predict $T_g$; if the dataset lacks specific dynamic properties (e.g., chain entanglement density) that are critical for $T_g$, the model may only capture partial variance, which is acceptable for this exploratory study.
- **Assumption about computational resources**: The `interpret` Python package and RDKit can run efficiently on a CPU-only environment with a limited number of cores and moderate RAM without requiring GPU acceleration or quantization, provided the dataset is sampled if necessary.
- **Assumption about validation independence**: The FFV and Chain Stiffness values in `data/physical_properties.csv` are calculated using the Van Krevelen group contribution method, which relies solely on molecular structure and group contributions, ensuring they are independent of the $T_g$ target variable used for training.
- **Assumption about threshold justification**: The perturbation magnitude for sensitivity analysis is chosen as a standard community default for robustness testing in materials informatics, representing a realistic range of experimental uncertainty.