# Specification: Predicting Molecular Properties from Quantum Chemical Calculations

## User Stories

### US1: Semi-Empirical Descriptor Generation
As a researcher, I want to compute HOMO, LUMO, and Mayer bond order descriptors using DFTB+ on the full dataset with geometry optimization, so that I can generate a baseline feature set efficiently.

### US2: High-Level DFT Baseline & Comparative Modeling
As a researcher, I want to compute DFT descriptors for a subset and train two Random Forest models (one on semi-empirical, one on DFT data) to compare their predictive accuracy (MAE) via a paired t-test, so that I can quantify the trade-off between speed and accuracy.

### US3: Feature Importance & Sensitivity Analysis
As a researcher, I want to identify the top 5 descriptors driving the model predictions and perform a sensitivity sweep over importance thresholds, so that I can understand which physical properties are most critical for predicting barrier heights.

## Functional Requirements

### FR-001: Data Ingestion
The system must fetch the experimental barrier dataset from a verified Zenodo repository and validate the presence of required columns (SMILES, experimental_barrier).

### FR-002: Semi-Empirical Workflow
The system must invoke DFTB+ to perform geometry optimization and extract HOMO, LUMO, and Mayer bond orders. Units must be normalized to eV for energies.

### FR-003: High-Level DFT Workflow
The system must invoke Psi4 to perform B3LYP/def2-SVP calculations on a defined subset (minimum 30 molecules) and extract equivalent descriptors.

### FR-004: Model Training
The system must train two Random Forest models using 5-fold cross-validation: one trained on semi-empirical descriptors and one on DFT descriptors.

### FR-005: Comparative Evaluation
The system must compute Mean Absolute Error (MAE) for both models and perform a paired t-test to determine statistical significance of the difference.

### FR-006: Feature Importance
The system must extract feature importance scores from the semi-empirical Random Forest model.

### FR-007: Sensitivity Sweep
The system must evaluate model performance across 5 different percentiles of the feature importance distribution.

### FR-008: Accuracy Threshold Flagging
The system must flag if the semi-empirical MAE exceeds the DFT MAE by more than 20%.

### FR-009: Cumulative Importance
The system must calculate and report the cumulative importance of the top 5 descriptors.

### FR-010: Validation Threshold
The system must verify that the semi-empirical MAE is within 2.0 kcal/mol of the experimental values.

## Edge Cases & Constraints

### EC-001: Convergence Failures
Molecules that fail to converge in DFTB+ or Psi4 must be skipped, logged, and excluded from the final dataset without halting the pipeline.

### EC-002: Out of Memory (OOM)
The system must detect when a subprocess exceeds 6.5GB of RSS memory, terminate it, and suggest reducing the subset size.

### EC-003: Data Validation
All input and output CSVs must be validated for column presence, data types, and physical ranges (e.g., HOMO < LUMO, charge sums).

### SC-001: Performance
The semi-empirical workflow must be at least 10x faster than the DFT workflow on average.

### SC-002: Reproducibility
All random seeds must be fixed, and dependency versions pinned in `requirements.txt`.

## Data Model

### Raw Data
- Source: Zenodo (Experimental Barrier Dataset)
- Format: CSV (SMILES, experimental_barrier)

### Processed Data
- `descriptors_semi.csv`: SMILES, HOMO (eV), LUMO (eV), Mayer_Bond_Order, Net_Charge
- `descriptors_dft.csv`: SMILES, HOMO (eV), LUMO (eV), Mayer_Bond_Order, Net_Charge

### Output Reports
- `reports/evaluation.json`: MAE_semi, MAE_dft, p_value, threshold_flags
- `reports/sensitivity.csv`: Percentile, MAE, Top_Descriptors
