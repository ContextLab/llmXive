# Spec Override: FR-007 Rejection and Correction

## Overview
This document formally documents the rejection of Functional Requirement **FR-007** regarding the imputation strategy for the `Sex` column and defines the corrected requirement to ensure methodological validity.

## Original Requirement (FR-007)
**Status**: **REJECTED**

**Original Text**:
> "The system MUST impute missing values in the `Sex` column using the **Median**."

**Reason for Rejection**:
The `Sex` column is a **categorical** (nominal) variable, typically encoded as 'M' (Male) or 'F' (Female).
1. **Mathematical Invalidity**: The concept of a "Median" requires an ordered, numerical domain. Applying a median function to categorical strings results in a type error or an arbitrary, non-meaningful selection that does not represent the central tendency of the distribution.
2. **Statistical Correctness**: For categorical data, the central tendency is defined by the **Mode** (the most frequently occurring value), not the median or mean.
3. **Methodological Error**: Using a median imputation strategy for sex would introduce data corruption or pipeline failures, violating the Data Hygiene Principle III (Provenance and Correctness).

## Corrected Requirement
**Status**: **APPROVED**

**New Requirement**:
> "The system MUST impute missing values in the `Sex` column using the **Mode** (the most frequent category)."

### Implementation Details
- **Algorithm**: Calculate the frequency count of non-null values in the `Sex` column. Select the value with the highest count.
- **Tie-Breaking**: If two categories have equal frequency (e.g., 50% 'M', 50% 'F'), the system MUST default to the first category encountered or raise a warning and select 'M' (standard biological default) to ensure deterministic behavior.
- **Logging**: The imputation strategy (Mode) and the specific value used (e.g., "Imputed Sex using Mode: 'M'") MUST be logged to `provenance.log` as per Data Hygiene Principle III.
- **Code Location**: This logic is implemented in `code/data_ingestion.py` within the `impute_missing_values` function.

## Validation
To verify this override:
1. Run `code/data_ingestion.py` with a dataset containing null `Sex` values.
2. Inspect `provenance.log` for the entry confirming "Mode" strategy.
3. Verify `data/processed/cleaned_data.csv` contains no null values in the `Sex` column and that the imputed values match the most frequent category from the original data.

## Traceability
- **Related Task**: T047 (Spec Override Implementation)
- **Related Task**: T013 (Imputation Logic Implementation)
- **Plan Reference**: Phase 3.5 - Spec Override & Correction Tasks