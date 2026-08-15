# Imputation Threshold Decision

**Date**: 2023-10-27
**Task**: T013b
**Decision**: Define KNN imputation rate threshold.

## Context
The data ingestion pipeline (T013) performs KNN imputation for missing solvent properties.
Excessive imputation may indicate poor data quality or a mismatch between the training
distribution and the target application, potentially leading to model overfitting on
imputed values.

## Threshold Definition
A maximum allowable imputation rate of **15%** (`MAX_IMPUTATION_RATE = 0.15`) is established.

## Rationale
- **Data Integrity**: Above 15% imputation, the signal-to-noise ratio in the feature set
 becomes suspect.
- **Literature Precedent**: Common practice in cheminformatics pipelines suggests a
 10-20% cutoff for robust model training. 15% is chosen as a balanced conservative limit.
- **Pipeline Safety**: This threshold acts as a hard gate (T013) to prevent training on
 low-quality data.

## Action
If the calculated imputation rate exceeds 0.15, the pipeline must:
1. Write an error message to `data/artifacts/imputation_error.log`.
2. Exit with code 1.
3. NOT proceed to feature engineering or model training.

## References
- T013: Data Imputation Implementation
- T013b: Document Threshold
