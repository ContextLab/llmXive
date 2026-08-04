# Specification: Predicting Molecular Properties from Quantum Chemical Calculations

## User Stories

### US1: Semi-Empirical Descriptor Generation
As a researcher, I want to compute HOMO/LUMO/Mayer descriptors using DFTB+ on the full dataset with geometry optimization so that I can establish a baseline for molecular properties.
- **Acceptance Criteria**:
 - `data/descriptors_semi.csv` contains HOMO, LUMO, Mayer bond orders.
 - `data/optimized_geometries/` contains XYZ files for all valid molecules.
 - Convergence failures are logged to `logs/convergence_failures.log`.

### US2: High-Level DFT Baseline & Comparative Modeling
As a researcher, I want to compute DFT descriptors for a subset and train two Random Forest models to compare their performance against experimental data.
- **Acceptance Criteria**:
 - `data/descriptors_dft.csv` generated for a stratified subset (50 samples).
 - `reports/evaluation.json` contains MAE for both models and a paired t-test p-value.
 - Semi-empirical MAE is verified to be ≤ 2.0 kcal/mol.

### US3: Feature Importance & Sensitivity Analysis
As a researcher, I want to identify top descriptors and perform a sensitivity sweep to understand model stability.
- **Acceptance Criteria**:
 - `reports/sensitivity.csv` lists top descriptors and cumulative importance.
 - Stability check confirms top 3 descriptors do not change across thresholds.

## Data Model
- **Input**: Experimental barrier dataset from Zenodo (CSV).
- **Columns**: `smiles`, `experimental_barrier`, `molecule_id`.
- **Descriptors**: `HOMO_energy` (eV), `LUMO_energy` (eV), `mayer_bond_order` (dimensionless).

## Edge Cases
- **Convergence Failure**: Skip molecule, log to `logs/convergence_failures.log`, continue pipeline.
- **OOM**: Detect via memory monitor, kill process, log to `logs/oom_failures.log`.
- **Physical Invalidity**: If `HOMO >= LUMO`, skip and log to `logs/structural_failures.log`.
