# Project Specification: Machine-Learned Potentials for Transition-Metal Catalysis

## Overview
This project develops a Graph Neural Network (GNN) based potential to predict barrier heights for transition-metal catalyzed reactions, specifically focusing on Pd, Ni, and Cu centers. The system ingests QM9-TS data, constructs molecular graphs, trains an ensemble of SchNet models, and performs rigorous error analysis.

## User Stories

### US1: Data Ingestion and Graph Construction
- Ingest QM9-TS dataset.
- Filter for Pd, Ni, Cu.
- Construct molecular graphs with edge attributes.
- Classify ligands (Group 13 vs. Conventional).
- Generate Leave-Ligand-Scaffold-Out (LLSO) splits.

### US2: GNN Training and Barrier Prediction
- Train ensemble of SchNet models.
- Perform 5-Fold LLSO cross-validation.
- Generate barrier height predictions.
- Compute MAE, RMSE, Pearson metrics.
- Analyze ensemble variance.

### US3: Error Analysis and Feature Attribution
- Analyze error residuals using SHAP/Integrated Gradients.
- Perform statistical testing on error distributions.
- Identify top descriptors influencing error.

## Functional Requirements

- **FR-001**: System must filter input data for specific metal centers (Pd, Ni, Cu).
- **FR-001b**: System must flag data scarcity if reaction count < 120.
- **FR-003**: System must train models with a hard cap on the number of epochs.
- **FR-004**: System must generate predictions for held-out test sets.
- **FR-005**: System must identify top descriptors explaining error variance.
- **FR-006**: System must perform statistical comparison of error distributions between ligand classes.
- **FR-007**: System must support ensemble predictions with variance estimation.
- **FR-008**: System must use 5-Fold Leave-Ligand-Scaffold-Out cross-validation.

## Non-Functional Requirements

- **SC-001**: Predictions must be generated within 1 second per sample.
- **SC-002**: Top descriptors must explain at least 60% of variance.
- **SC-003**: Cross-validation metrics must be aggregated and reported.
- **SC-004**: System must report speed-up factor compared to DFT.
- **SC-005**: Ensemble variance must correlate with error magnitude.

## Data Model

- **Input**: QM9-TS transition state geometries.
- **Intermediate**: Graph representations (nodes, edges, features).
- **Output**: Barrier height predictions, residuals, metrics.

## Contracts

- **DatasetGraphSchema**: Defines valid graph structure (nodes, edges, attributes).
- **PredictionSchema**: Defines valid prediction output format.

## Deviations & Spec Amendments

The following deviations from initial planning have been documented and approved:

| Deviation ID | Original Requirement | Modified Requirement | Justification | Status |
|:--- |:--- |:--- |:--- |:--- |
| FR-008-Mod | Leave-One-Out Cross-Validation (LOOCV) | 5-Fold Leave-Ligand-Scaffold-Out (LLSO) | LOOCV is computationally prohibitive and statistically unstable for this dataset size; LLSO provides a more robust estimate of generalization to unseen ligand scaffolds. | Implemented (T029c) |
| FR-006-Mod | Paired t-test for error comparison | Unpaired Welch's t-test for error comparison | Error distributions between Group 13 and Conventional ligand classes are independent and likely have unequal variances; Welch's t-test is the appropriate statistical method for this scenario. | Implemented (T034b) |

## Execution Plan

1. **Phase 1**: Setup and Infrastructure
2. **Phase 2**: Foundational Components (Config, Logging, Schemas)
3. **Phase 3**: US1 - Data Ingestion & Graph Construction
4. **Phase 4**: US2 - Model Training & Prediction
5. **Phase 5**: US3 - Error Analysis & Attribution
6. **Phase 6**: Polish & Final Validation

## Appendix: Configuration Defaults

- `THRESHOLD_DATA_SCARCITY`: 120
- `PSI4_BASIS`: "sto-3g"
- `CUTOFF_RANGE`: [3.0, 3.5, 4.0]
- `MAX_EPOCHS`: 30
- `EARLY_STOPPING_PATIENCE`: 5