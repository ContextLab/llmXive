# Specification: Predicting Molecular Properties from Quantum Chemical Calculations

## User Stories

### US1: Semi-Empirical Descriptor Generation
As a researcher, I want to compute HOMO/LUMO/Mayer descriptors using DFTB+ on the full dataset with geometry optimization so that I can establish a baseline for molecular properties.
- **Acceptance Criteria**:
 - `data/descriptors_semi.csv` contains HOMO, LUMO, Mayer bond orders.
 - `data/optimized_geometries/` contains XYZ files for all valid molecules.
 - Convergence failures are logged to `logs/convergence_failures.log` with a schema: `molecule_id, timestamp, error_code, error_message`.
 - Molecules failing after one retry are logged as `failed_after_retry` with the same schema.
- **Linked Requirements**: FR-001, FR-002, FR-003 (See US1)
- **Linked Success Criteria**: SC-001 (See US1)

### US2: High-Level DFT Baseline & Comparative Modeling
As a researcher, I want to compute DFT descriptors for a stratified subset (50 samples) using the same optimized geometries as US1, train two Random Forest models, and compare their performance against experimental data using a paired t-test.
- **Acceptance Criteria**:
 - `data/descriptors_dft.csv` generated for the 50-sample subset.
 - `reports/evaluation.json` contains MAE for both models (Semi-Empirical RF vs DFT RF) and a paired t-test result.
 - The paired t-test report must specify: Null Hypothesis (no difference in error distribution), Significance Level (α=0.05), and the models compared.
 - The Semi-Empirical MAE is reported as a measured value (not verified against a fixed threshold).
- **Linked Requirements**: FR-004, FR-005, FR-008 (See US2)
- **Linked Success Criteria**: SC-002 (See US2)

### US3: Feature Importance & Sensitivity Analysis
As a researcher, I want to identify top descriptors and perform a sensitivity sweep to understand model stability.
- **Acceptance Criteria**:
 - `reports/sensitivity.csv` lists top descriptors and cumulative importance.
 - Stability check confirms top 3 descriptors do not change (rank correlation ≥ 0.9) across thresholds: feature importance cutoffs {0.01, 0.05, 0.1} and noise injection levels {σ=0.01, 0.05}.
- **Linked Requirements**: FR-006, FR-007 (See US3)
- **Linked Success Criteria**: SC-003 (See US3)

## Data Model
- **Input**: Experimental barrier dataset from Zenodo (CSV).
  - **Source Reference**: See `idea/predicting-molecular-properties-from-qua.md` for the specific Zenodo Accession ID and URL.
  - **Verification**: Dataset must be verified for provenance and checksummed before processing (See FR-001).
- **Columns**: `smiles`, `experimental_barrier`, `molecule_id`.
- **Descriptors**: `HOMO_energy` (eV), `LUMO_energy` (eV), `mayer_bond_order` (dimensionless).

## Edge Cases
- **Convergence Failure**: 
  1. Attempt geometry optimization.
  2. If it fails, attempt one re-calculation with a different initial guess.
  3. If the retry fails, skip the molecule and log to `logs/convergence_failures.log` with status `failed_after_retry` and include `molecule_id`, `timestamp`, `error_code`, `error_message`.
- **OOM**: Detect via memory monitor, kill process, log to `logs/oom_failures.log`.
- **Physical Invalidity**: If `HOMO >= LUMO`, attempt one re-calculation. If it still fails, skip and log to `logs/structural_failures.log` with status `failed_after_retry`. Do not blindly skip without retry to avoid selection bias on transition states.

## Requirements

### Functional Requirements

- **FR-001**: System MUST fetch the input dataset from the verified Zenodo source defined in the Idea.md, verify its checksum, and log the verification status before processing (See US1).
- **FR-002**: System MUST perform geometry optimization on all molecules using DFTB+ and save the resulting XYZ files to `data/optimized_geometries/` (See US1).
- **FR-003**: System MUST compute HOMO, LUMO, and Mayer bond order descriptors from the optimized geometries and save them to `data/descriptors_semi.csv` (See US1).
- **FR-004**: System MUST compute DFT descriptors using Psi for a stratified random subset of molecules. These calculations MUST use the exact same optimized geometries generated in FR-002. The system MUST train two Random Forest models (Semi-Empirical and DFT-based) using the exact same training and test splits (the 50-sample subset) to enable a fair paired t-test comparison (See US2).
- **FR-005**: System MUST perform a paired t-test comparing the error distributions of the Semi-Empirical RF and DFT RF models on the test set, reporting the p-value, null hypothesis, and significance level (α=0.05) (See US2).
- **FR-006**: System MUST identify top descriptors based on feature importance and save them to `reports/sensitivity.csv` (See US3).
- **FR-007**: System MUST perform a sensitivity analysis sweeping feature importance cutoffs {0.01, 0.05, 0.1} and noise injection levels {σ=0.01, 0.05} to verify the stability of the top 3 descriptors (See US3).
- **FR-008**: System MUST analyze and log potential confounding variables (molecular size, functional groups) to ensure the feature space coverage matches the chemical diversity of the target dataset (See US2).

### Key Entities
- **Molecule**: Represents a chemical structure defined by SMILES and ID.
- **Descriptor**: Represents a computed quantum chemical property (HOMO, LUMO, Mayer).
- **Model**: Represents a trained Random Forest regressor.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The number of successfully optimized geometries and computed semi-empirical descriptors is measured against the total count of valid input molecules (See US1).
- **SC-002**: The Mean Absolute Error (MAE) of the Semi-Empirical RF and DFT RF models is measured against the experimental barrier values from the Zenodo dataset, and the difference is evaluated via a paired t-test with α=0.05 (See US2).
- **SC-003**: The rank correlation of the top 3 descriptors is measured across the specified sensitivity thresholds (cutoffs: 0.01, 0.05, 0.1; noise: σ=0.01, 0.05) to confirm stability (See US3).

## Assumptions

- Users have access to the DFTB+ and Psi4 software packages.
- The Zenodo dataset contains valid SMILES strings for all entries.
- The computational resources are sufficient to handle the full dataset for semi-empirical calculations and the 50-sample subset for DFT calculations.
- The experimental barrier dataset is the ground truth for validation.