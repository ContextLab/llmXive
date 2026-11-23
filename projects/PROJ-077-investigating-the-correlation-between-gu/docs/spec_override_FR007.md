# Spec Override: FR-007 (Imputation Strategy Correction)

**Date**: 2023-10-27
**Status**: REJECTED (Original Requirement) / CORRECTED (New Requirement)
**Related Task**: T047
**Dependency**: T056

## Original Requirement (FR-007)

The original functional requirement stated:
> "System MUST impute missing numeric covariate values (age, BMI, DQS) using the median of the available data, and missing categorical values (sex) using the mode."

**Note**: While the original text actually described the correct behavior (Median for numeric, Mode for categorical), the execution and previous implementation attempts incorrectly applied the Median strategy to the categorical 'sex' column, leading to invalid data types (floats) and statistical errors. This override explicitly rejects any implementation that uses Median for 'sex' and enforces the Mode strategy.

## Correction Rationale

Using the **Median** for the categorical variable `sex` (values: 'M', 'F', 'O') is mathematically invalid.
1. **Type Mismatch**: Median requires ordered numerical data. Applying it to strings results in a TypeError or a fallback to a non-meaningful default.
2. **Statistical Validity**: The median of a categorical distribution does not represent the "most likely" value. The **Mode** (most frequent value) is the only appropriate measure of central tendency for nominal data.
3. **Pipeline Integrity**: Previous runs using Median for 'sex' resulted in non-string values in the 'sex' column, breaking downstream regression models that expect categorical encoding.

## Corrected Requirement

The system MUST adhere to the following imputation logic:

> **FR-007 (Corrected)**: System MUST impute missing numeric covariate values (age, BMI, DQS) using the **median** of the available data, and missing categorical values (**sex**) using the **mode** (most frequent value) of the available data.

## Implementation Constraints

1. **Numeric Columns** (`age`, `bmi`, `dqs`):
 - Strategy: `Series.median()`
 - Type: Must remain float/numeric.
2. **Categorical Columns** (`sex`):
 - Strategy: `Series.mode().iloc[0]`
 - Type: Must remain string/object or categorical dtype.
 - **CRITICAL**: If `mode()` returns an empty series (all values missing), the system MUST raise a `ValueError` and halt, rather than imputing a placeholder string.

## Verification

The implementation in `code/data_ingestion.py` (function `impute_missing_values`) must be verified to:
- Call `df['sex'].fillna(df['sex'].mode()[0])` (or equivalent).
- NOT call `df['sex'].fillna(df['sex'].median())`.
- Log the specific imputation strategy used for 'sex' to `provenance.log`.

## References

- Plan Correction: "System MUST impute Sex using Mode."
- Spec Override T045 (FR-003): Clarifies raw counts for Shannon.
- Spec Override T046 (SC-001): Clarifies Raw Shannon correlation target.