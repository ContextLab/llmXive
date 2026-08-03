# Specification: Predicting Molecular Properties from Quantum Chemical Calculations

## User Stories

### US1: Semi-Empirical Descriptor Generation
As a researcher, I want to compute HOMO/LUMO/Mayer descriptors using DFTB+ on the full dataset so that I can establish a baseline model with reasonable computational cost.
- **Acceptance Criteria**:
 - Geometry optimization performed for all valid molecules.
 - Output CSV contains HOMO, LUMO, Mayer bond orders.
 - Convergence failures are logged and skipped, not halting the pipeline.
 - Optimized geometries exported to XYZ format.

### US2: High-Level DFT Baseline & Comparative Modeling
As a researcher, I want to compute DFT descriptors for a subset and compare model performance against the semi-empirical baseline so that I can quantify the accuracy trade-off.
- **Acceptance Criteria**:
 - A subset of valid samples processed with Psi4 B3LYP/def2-SVP.
 - Identical geometries used for both methods (imported from US1).
 - Two Random Forest models trained and evaluated via 5-fold CV.
 - Paired t-test performed; semi-MAE ≤ 2.0 kcal/mol verified.

### US3: Feature Importance & Sensitivity Analysis
As a researcher, I want to identify top descriptors and sweep numerical thresholds so that I can understand model stability and physical relevance.
- **Acceptance Criteria**:
 - Top descriptors identified by feature importance.
 - Sensitivity sweep over thresholds (, 1.0, 2.0 eV).
 - MAE degradation reported for each threshold.
 - Top descriptors stability checked (change < 1 time).

## Edge Cases
- **Convergence Failure**: Log to `logs/convergence_failures.log`, skip molecule.
- **OOM**: Detect via `utils/memory_monitor.py`, kill process, log, skip.
- **Physical Range Violation**: If HOMO > LUMO, log to `logs/structural_failures.log`, skip.

## Data Model
- **Input**: CSV with `SMILES`, `experimental_barrier` (kcal/mol).
- **Output**: CSV with `SMILES`, `HOMO_energy`, `LUMO_energy`, `Mayer_Bond_Order`, `predicted_barrier`.

## Constraints
- Runtime < 6 hours for full pipeline on subset.
- Reproducibility: Pin dependencies, generate checksums.
- Physical Validity: Verify units (eV) and physical relationships (HOMO < LUMO).
