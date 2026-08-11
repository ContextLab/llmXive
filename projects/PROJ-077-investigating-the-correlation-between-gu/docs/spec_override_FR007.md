# Spec Override: FR-007 Correction for Categorical Data Imputation

## Original Requirement (REJECTED)
**FR-007 (Original)**: "System MUST impute missing numeric covariate values (age, BMI, DQS) using the median of the available data, and missing categorical values (sex) using the median."

## Reason for Rejection
The original specification contained a methodological error: it requested the use of the **median** for imputing the categorical variable `sex`. The median is a statistical measure applicable only to ordinal or continuous numeric data. Applying a median operation to categorical data (e.g., 'M', 'F') is mathematically undefined and would result in runtime errors or nonsensical data values in the pipeline.

## Corrected Requirement
**FR-007 (Corrected)**: "System MUST impute missing numeric covariate values (age, BMI, DQS) using the median of the available data, and missing categorical values (sex) using the mode."

## Implementation Details
- **Numeric Covariates**: Age, BMI, and Diet Quality Score (DQS) will continue to use the `median` strategy.
- **Categorical Covariates**: The `sex` column will now use the `mode` (most frequent value) strategy for imputation.

## Validation
The `code/data_ingestion.py` module has been updated to explicitly apply `strategy='mode'` for the `sex` column and `strategy='median'` for numeric columns. Unit tests confirm that the most frequent category is correctly assigned to missing entries in the `sex` column.

## References
- Project Plan: Phase 2, Spec Override Tasks
- Related Task: T047
- Implementation Module: `code/data_ingestion.py` (function: `impute_missing_values`)
