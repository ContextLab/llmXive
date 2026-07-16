# Specification: Molecular Property Prediction Pipeline

## Functional Requirements
- **FR-001**: System must download real molecular data (SMILES + properties) from verified sources.
- **FR-002**: System must preprocess data to handle missing values and ensure high confidence.
- **FR-003**: System must generate Open Babel fingerprints via CLI subprocess.
- **FR-004**: System must train Random Forest models with nested cross-validation.
- **FR-005**: System must perform statistical comparison (Wilcoxon signed-rank) between baseline and RF.
- **FR-006**: System must generate SHAP interaction values for explainability.
- **FR-007**: System must map SHAP bits back to chemical substructures.
- **FR-008**: System must log data quality metrics including missing covariates.

## Non-Functional Requirements
- **NFR-001**: All code must be Python 3.10+.
- **NFR-002**: Data artifacts must be stored in `data/` directory.
- **NFR-003**: Scripts must fail loudly if real data sources are unreachable.
- **NFR-004**: Analysis must be reproducible via random seed management.

## Data Model
- **Input**: SMILES strings, experimental logP, solubility, boiling point.
- **Intermediate**: Fingerprint arrays (MACCS, ECFP4, FP2).
- **Output**: Predictions CSV, residual plots, SHAP heatmaps, statistical reports.

## Validation Protocol
- Data split: 80% train, 20% test (held out).
- Metric: MAE, RMSE.
- Statistical Test: Paired Wilcoxon signed-rank test on absolute errors.
