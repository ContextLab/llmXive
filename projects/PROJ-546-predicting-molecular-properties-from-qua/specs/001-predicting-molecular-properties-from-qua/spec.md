# Feature Specification: Predicting Molecular Properties from Quantum Chemical Calculations with Limited Computational Resources

**Feature Branch**: `001-predicting-molecular-properties`
**Created**: 2026-06-24
**Status**: Draft
**Input**: User description: "Predicting Molecular Properties from Quantum Chemical Calculations with Limited Computational Resources"

## User Scenarios & Testing

### User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1)

The system must compute electronic structure descriptors (HOMO/LUMO energies, Mulliken charges, bond orders) for a dataset of molecules using semi-empirical quantum methods (DFTB/PM6) to create a lightweight feature matrix.

**Why this priority**: This is the foundational data generation step. Without these descriptors, no predictive modeling can occur. It addresses the core constraint of computational efficiency while providing the primary input for the research question.

**Independent Test**: Can be fully tested by running the descriptor generation script on a small subset (e.g., 50 molecules) and verifying that the output CSV contains the expected columns (HOMO, LUMO, charges) with numerical values within physically plausible ranges, without requiring the high-level DFT baseline or the machine learning model.

**Acceptance Scenarios**:

1. **Given** a CSV file containing SMILES strings for 50 nucleophilic substitution substrates, **When** the DFTB+ descriptor generation script is executed, **Then** a `descriptors_semi.csv` file is produced containing exactly 50 rows and the required electronic structure columns with no NaN values.
2. **Given** the generated `descriptors_semi.csv`, **When** the values are inspected, **Then** the HOMO/LUMO energies are in electron-volts (eV) and Mulliken charges sum to the net charge of the molecule within a tolerance of ±0.01.

---

### User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

The system must compute the same descriptors using a high-level DFT method (B3LYP/def2-SVP) for a representative subset ([deferred]) of molecules and train a Random Forest model on both the semi-empirical and high-level datasets to compare their predictive accuracy against experimental barriers.

**Why this priority**: This step establishes the "ground truth" performance ceiling. It allows the system to determine if the cheaper method (P1) is "good enough" by providing a direct statistical comparison, which is the primary scientific output of the project.

**Independent Test**: Can be tested by running the modeling pipeline on the subset of molecules with both descriptor sets. The test passes if the script outputs two MAE values (one for semi-empirical, one for DFT) and a p-value from a paired t-test, demonstrating that the comparison logic works even if the full dataset is not yet processed.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 molecules where 30 have both semi-empirical and DFT descriptors, **When** the Random Forest training and evaluation script runs, **Then** the output log reports the Mean Absolute Error (MAE) for the semi-empirical model and the DFT model, along with a p-value from a paired t-test comparing the two error distributions.
2. **Given** the experimental barrier values and the predicted values from the semi-empirical model, **When** the error analysis runs, **Then** the system flags if the semi-empirical MAE exceeds the DFT MAE by more than 10%, indicating a potential failure of the low-cost approximation.

---

### User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

The system must identify the top 5 most influential descriptors from the semi-empirical model and perform a sensitivity analysis by sweeping key decision thresholds (e.g., feature importance cutoff) to ensure the model's conclusions are robust.

**Why this priority**: This adds scientific rigor by explaining *why* the model works and ensuring the results are not artifacts of a single arbitrary threshold. It addresses the reviewer's concern about "speculation" by providing a robust, data-driven explanation of the predictive signal.

**Independent Test**: Can be tested by running the feature importance extraction and the sensitivity sweep on the trained model. The test verifies that the output includes a ranked list of descriptors and a table showing how the model's MAE changes when the feature selection threshold is varied.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model using semi-empirical descriptors, **When** the feature importance analysis runs, **Then** the output lists the top 5 descriptors with their importance scores summing to ≥ 0.8 of the total importance.
2. **Given** a specific feature importance threshold (e.g., 0.05), **When** the sensitivity analysis sweeps the threshold over the set {0.01, 0.05, 0.1}, **Then** the system reports the resulting MAE for each threshold, confirming that the top descriptors remain stable or quantifying the degradation in performance.

---

### Edge Cases

- **What happens when** a molecule in the input dataset fails to converge in the DFTB+ or Psi4 calculation? The system must log the failure, skip the molecule, and continue processing the remaining dataset without crashing.
- **How does the system handle** a scenario where the experimental barrier dataset contains outliers (e.g., >3 standard deviations from the mean) that skew the regression? The system must apply a robust scaling method or flag these outliers for exclusion in the sensitivity analysis.
- **What happens when** the computational resources (RAM) are exceeded during the DFT calculation for a large molecule? The job must fail gracefully with a clear error message indicating "Out of Memory" and suggest reducing the subset size, rather than hanging or corrupting the output.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the experimental reaction barrier dataset from the specified Zenodo URL and parse SMILES strings into a structured dataframe (See US-1).
- **FR-002**: System MUST invoke DFTB+ to compute HOMO, LUMO, and Mulliken charges for all molecules in the dataset (See US-1).
- **FR-003**: System MUST invoke Psi4 to compute the same descriptors for a [deferred] random subset of molecules at the B3LYP/def2-SVP level (See US-2).
- **FR-004**: System MUST train two separate Random Forest regressors (one on semi-empirical data, one on DFT data) using 5-fold cross-validation and record per-fold MAE (See US-2).
- **FR-005**: System MUST perform a paired t-test on the per-fold MAE values to determine if the performance difference is statistically significant (p < 0.05) (See US-2).
- **FR-006**: System MUST extract feature importance scores and identify the top 5 descriptors that contribute to the predictive signal (See US-3).
- **FR-007**: System MUST execute a sensitivity analysis sweeping the feature importance threshold over the set {0.01, 0.05, 0.1} and report the resulting MAE for each sweep (See US-3).

### Key Entities

- **Molecule**: Represents a chemical entity defined by a SMILES string and its associated experimental reaction barrier value.
- **Descriptor**: A numerical electronic structure property (e.g., HOMO energy, bond order) calculated for a molecule.
- **Model**: A trained Random Forest regressor instance mapping descriptors to experimental barriers.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the semi-empirical model is measured against the MAE of the high-level DFT model to determine if the difference is within 10% (See US-2).
- **SC-002**: The statistical significance of the performance difference is measured against the p-value threshold of 0.05 from the paired t-test (See US-2).
- **SC-003**: The stability of the top 5 descriptors is measured against the results of the sensitivity analysis sweeping thresholds {0.01, 0.05, 0.1} (See US-3).
- **SC-004**: The computational cost (CPU time) of the semi-empirical pipeline is measured against the high-level DFT pipeline to confirm the "orders of magnitude" speedup claim (See US-1).
- **SC-005**: The feature importance distribution is measured against the total variance explained to ensure the top 5 descriptors capture ≥ 80% of the signal (See US-3).

## Assumptions

- The Zenodo dataset URL provided in the idea (`) is accessible and contains valid SMILES strings and experimental barrier values.
- The DFTB+ and Psi4 software packages are pre-installed and configured on the GitHub Actions runner environment with CPU-only execution enabled.
- The "[deferred] subset" for high-level DFT calculations is selected randomly to ensure representativeness, and the remaining [deferred] rely solely on semi-empirical data.
- The experimental barrier dataset does not contain systematic errors that would invalidate the comparison between computational and experimental values.
- The Random Forest hyperparameters (number of trees, max depth) are set to default values in scikit-learn to ensure reproducibility and avoid overfitting on small datasets.
- The "[deferred] accuracy" target is a community-standard benchmark for acceptable approximation in virtual screening, as implied by the idea's expected results.
