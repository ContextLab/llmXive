# Feature Specification: Predicting Molecular Properties from Quantum Chemical Calculations with Limited Computational Resources

**Feature Branch**: `001-predicting-molecular-properties`
**Created**: 2026-06-24
**Status**: Draft
**Input**: User description: "Predicting Molecular Properties from Quantum Chemical Calculations with Limited Computational Resources"

## User Scenarios & Testing

### User Story 1 - Semi-Empirical Descriptor Generation (Priority: P1)

The system must compute electronic structure descriptors (HOMO/LUMO energies, Mulliken charges, Mayer bond orders) for a dataset of molecules using semi-empirical quantum methods (DFTB/PM6) to create a lightweight feature matrix. Geometries must be optimized at the DFTB level for these calculations.

**Why this priority**: This is the foundational data generation step. Without these descriptors, no predictive modeling can occur. It addresses the core constraint of computational efficiency while providing the primary input for the research question.

**Independent Test**: Can be fully tested by running the descriptor generation script on a small subset (e.g., 50 molecules) and verifying that the output CSV contains the expected columns (HOMO, LUMO, Mayer bond orders) with numerical values within physically plausible ranges, without requiring the high-level DFT baseline or the machine learning model.

**Acceptance Scenarios**:

1. **Given** a CSV file containing SMILES strings for 50 nucleophilic substitution substrates, **When** the DFTB+ descriptor generation script is executed, **Then** a `descriptors_semi.csv` file is produced containing exactly 50 rows and the required electronic structure columns with no NaN values.
2. **Given** the generated `descriptors_semi.csv`, **When** the values are inspected, **Then** the HOMO/LUMO energies are in electron-volts (eV) and Mulliken charges sum to the net charge of the molecule within a tolerance of ±0.01.

---

### User Story 2 - High-Level DFT Baseline & Comparative Modeling (Priority: P2)

The system must compute the same descriptors using a high-level DFT method (B3LYP/def2-SVP) for a representative subset (minimum 30 molecules or [deferred] of the dataset, whichever is larger) of molecules. Geometries for these calculations must be optimized at the DFT level. Two separate Random Forest models are trained: one on the semi-empirical data (restricted to the subset) and one on the DFT data (restricted to the subset). Both models are evaluated against the *same* experimental ground truth to compare their predictive accuracy.

**Why this priority**: This step establishes the performance of the high-level method against experimental data and determines if the cheaper method (P1) is "good enough" by providing a direct statistical comparison. It ensures the comparison is scientifically valid by using aligned test sets.

**Independent Test**: Can be tested by running the modeling pipeline on the subset of molecules with both descriptor sets. The test passes if the script outputs two MAE values (one for semi-empirical, one for DFT) and a p-value from a paired t-test comparing the two error distributions on the *same* test folds.

**Acceptance Scenarios**:

1. **Given** a dataset of molecules where a representative subset (minimum 30 molecules) has both semi-empirical and DFT descriptors, **When** the Random Forest training and evaluation script runs, **Then** the output log reports the Mean Absolute Error (MAE) for the semi-empirical model and the DFT model, along with a p-value from a paired t-test comparing the two error distributions on the same test folds.
2. **Given** the experimental barrier values and the predicted values from the semi-empirical model, **When** the error analysis runs, **Then** the system flags if the semi-empirical MAE exceeds the DFT MAE by more than 20%, indicating a potential failure of the low-cost approximation relative to the high-level baseline.

---

### User Story 3 - Feature Importance & Sensitivity Analysis (Priority: P3)

The system must identify the top 5 most influential descriptors from the semi-empirical model and perform a sensitivity analysis by sweeping key decision thresholds (e.g., feature importance cutoff) to ensure the model's conclusions are robust. The cumulative importance of the top 5 descriptors must be reported.

**Why this priority**: This adds scientific rigor by explaining *why* the model works and ensuring the results are not artifacts of a single arbitrary threshold. It addresses the reviewer's concern about "speculation" by providing a robust, data-driven explanation of the predictive signal.

**Independent Test**: Can be tested by running the feature importance extraction and the sensitivity sweep on the trained model. The test verifies that the output includes a ranked list of descriptors and a table showing how the model's MAE changes when the feature selection threshold is varied.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model using semi-empirical descriptors, **When** the feature importance analysis runs, **Then** the output lists the top 5 descriptors with their importance scores and the cumulative sum of these scores.
2. **Given** a specific feature importance threshold, **When** the sensitivity analysis sweeps the threshold over 5 equally spaced percentiles of the importance distribution, **Then** the system reports the resulting MAE for each threshold, confirming that the top descriptors remain stable or quantifying the degradation in performance.

---

### Edge Cases

- **What happens when** a molecule in the input dataset fails to converge in the DFTB+ or Psi4 calculation? The system must log the failure, skip the molecule, and continue processing the remaining dataset without crashing.
- **How does the system handle** a scenario where the experimental barrier dataset contains outliers (e.g., >1.5 IQR above the third quartile) that skew the regression? The system must apply the Interquartile Range (IQR) method to identify and flag these outliers for exclusion in the sensitivity analysis.
- **What happens when** the computational resources (RAM) are exceeded during the DFT calculation for a large molecule? The job must fail gracefully with a clear error message indicating "Out of Memory" and suggest reducing the subset size, rather than hanging or corrupting the output.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the experimental reaction barrier dataset from the specified Zenodo URL and parse SMILES strings into a structured dataframe (See US-1).
- **FR-002**: System MUST invoke DFTB+ to compute HOMO, LUMO, and Mayer bond orders for all molecules in the dataset, using geometries optimized at the DFTB level (See US-1).
- **FR-003**: System MUST invoke Psi4 to compute the same descriptors for a subset of molecules (minimum 30 molecules or [deferred] of the dataset, whichever is larger) at the B3LYP/def2-SVP level, using geometries optimized at the DFT level (See US-2).
- **FR-004**: System MUST train two separate Random Forest regressors (one on semi-empirical data restricted to the subset, one on DFT data restricted to the subset) using 5-fold cross-validation and record per-fold MAE (See US-2).
- **FR-005**: System MUST perform a paired t-test on the per-fold MAE values (restricted to the same test folds) to determine if the performance difference is statistically significant (p < 0.05) (See US-2).
- **FR-006**: System MUST extract feature importance scores and identify the top 5 descriptors that contribute to the predictive signal (See US-3).
- **FR-007**: System MUST execute a sensitivity analysis sweeping the feature importance threshold over 5 equally spaced percentiles of the importance distribution and report the resulting MAE for each sweep (See US-3).
- **FR-008**: System MUST flag the result if the semi-empirical MAE exceeds the DFT MAE by more than 20% (See US-2).
- **FR-009**: System MUST report the cumulative importance score of the top 5 descriptors (See US-3).
- **FR-010**: System MUST verify that the semi-empirical model's absolute MAE is ≤ 2.0 kcal/mol against the experimental ground truth (See US-2).

### Key Entities

- **Molecule**: Represents a chemical entity defined by a SMILES string and its associated experimental reaction barrier value.
- **Descriptor**: A numerical electronic structure property (e.g., HOMO energy, Mayer bond order) calculated for a molecule.
- **Model**: A trained Random Forest regressor instance mapping descriptors to experimental barriers.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the semi-empirical model is measured against the MAE of the high-level DFT model to determine if the difference is ≤ 20% (See US-2).
- **SC-002**: The statistical significance of the performance difference is measured against the p-value threshold of 0.05 from the paired t-test (See US-2).
- **SC-003**: The stability of the top 5 descriptors is measured against the results of the sensitivity analysis sweeping 5 equally spaced percentiles (See US-3).
- **SC-004**: The computational cost (CPU time) of the semi-empirical pipeline is measured against the high-level DFT pipeline to confirm a speedup of at least 10x (See US-1).
- **SC-005**: The feature importance distribution is measured to report the cumulative importance of the top 5 descriptors (See US-3).
- **SC-006**: The semi-empirical model's absolute MAE is measured against the experimental ground truth to verify it is ≤ 2.0 kcal/mol (See US-2).
- **SC-007**: The statistical significance of the semi-empirical model's absolute MAE being ≤ 2.0 kcal/mol is measured using a one-sided t-test against the 2.0 kcal/mol threshold (See US-2).

## Assumptions

- The Zenodo dataset URL provided in the idea is accessible and contains valid SMILES strings and experimental barrier values.
- The DFTB+ and Psi4 software packages are pre-installed and configured on the GitHub Actions runner environment with CPU-only execution enabled.
- The subset for high-level DFT calculations is selected to ensure representativeness (minimum 30 molecules or [deferred] of the dataset), and the remaining molecules rely solely on semi-empirical data.
- The experimental barrier dataset does not contain systematic errors that would invalidate the comparison between computational and experimental values.
- The Random Forest hyperparameters (number of trees, max depth) are set to default values in scikit-learn to ensure reproducibility and avoid overfitting on small datasets.
- The [deferred] MAE difference target is the benchmark for acceptable approximation relative to the high-level baseline, as implied by the idea's expected results.
- The absolute MAE threshold for chemical accuracy in this context represents a standard benchmark.