# Specification: Predicting Molecular Properties from Quantum Chemical Calculations

## User Stories

### US1: Semi-Empirical Descriptor Generation
As a researcher, I want to generate HOMO, LUMO, and Mayer descriptors using DFTB+ on the full dataset with geometry optimization so that I can establish a baseline for molecular properties efficiently.

### US2: High-Level DFT Baseline & Comparative Modeling
As a researcher, I want to compute DFT descriptors for a subset and train two Random Forest models (one on semi-empirical, one on DFT data) so that I can compare their predictive accuracy against experimental barriers.

### US3: Feature Importance & Sensitivity Analysis
As a researcher, I want to identify the top descriptors contributing to the model predictions and perform a sensitivity analysis so that I can understand which physical features are most critical for barrier height prediction.

## Functional Requirements

- FR-001: Download experimental barrier dataset from Zenodo.
- FR-002: Invoke DFTB+ for geometry optimization and descriptor extraction.
- FR-003: Invoke Psi4 for B3LYP/def2-SVP calculations on a subset.
- FR-004: Train Random Forest models using 5-fold cross-validation.
- FR-005: Compute MAE and run paired t-tests for model comparison.
- FR-006: Extract feature importance from the semi-empirical model.
- FR-007: Perform sensitivity sweep over descriptor thresholds.
- FR-008: Flag if semi-empirical MAE exceeds DFT MAE by >20%.
- FR-009: Report cumulative importance of top descriptors.
- FR-010: Verify semi-empirical MAE ≤ 2.0 kcal/mol.

## Edge Cases

- Convergence failures in quantum calculations: Skip molecule, log failure, continue.
- OOM (Out of Memory) during calculation: Detect, kill process, suggest subset reduction.
- Missing columns in input data: Raise validation error.
