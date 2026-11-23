# Edge Case Handling

## Overview

This document describes how the pipeline handles edge cases that may arise during simulation.

## Detected Edge Cases

### 1. Insufficient Sample Size ($N < 50$)

**Detection**: Checked during data validation (T035)

**Handling**:
- Dataset is skipped
- Logged to `results/validation_report.json`
- Pipeline continues with remaining datasets

**Rationale**: Statistical power is too low for reliable error rate estimation

### 2. Highly Correlated Variables

**Detection**: Checked during null hypothesis construction (T040)

**Handling**:
- Attempt single replication test
- If p-values are all 0 or all 1, flag as edge case
- Logged to `results/edge_case_report.json`
- Configuration is skipped for full run

**Rationale**: Null hypothesis cannot be cleanly constructed

### 3. Normality Violations

**Detection**: Shapiro-Wilk test on residuals (T058)

**Threshold**: $p < 0.01$

**Handling**:
- Configuration is flagged
- Logged to `results/edge_case_report.json`
- Results marked as potentially invalid for parametric tests
- Pipeline continues (results preserved but flagged)

**Rationale**: Parametric tests (t-test, ANOVA) assume normality

### 4. Failed Spatial Proxy Generation

**Detection**: Silhouette score validation (T041, T053)

**Threshold**: silhouette score $< 0.25$

**Handling**:
- Spatial injection is skipped for this dataset
- Logged to `data/manifests/spatial_proxy_report.json`
- Pipeline continues with other injection methods

**Rationale**: Proxy does not capture meaningful structure

### 5. Memory Constraints

**Detection**: Pre-flight check (T052)

**Threshold**: Estimated memory > 6GB

**Handling**:
- Dataset is skipped
- Logged to `results/perf_log.json`
- Pipeline continues with remaining datasets

**Rationale**: Ensure sufficient replications can complete

### 6. Data Fetch Failures

**Detection**: During dataset loading (T056b)

**Handling**:
- Raise `DataFetchError`
- Pipeline halts with clear error message
- No synthetic fallback (per T056b)

**Rationale**: Real data fetch must not silently fall back to synthetic

### 7. Failed Null Construction

**Detection**: During permutation step (T012d)

**Handling**:
- Logged to `results/edge_case_report.json`
- Configuration is skipped
- Pipeline continues with remaining configurations

**Rationale**: Cannot proceed without valid null hypothesis

### 8. Extreme Dependency Strength

**Detection**: During AR(1) injection validation (T006a)

**Handling**:
- Verify injected autocorrelation within 5% tolerance
- If tolerance exceeded, flag configuration
- Logged to `results/edge_case_report.json`

**Rationale**: Ensure injected dependency matches target

### 9. Chi-Squared Binning Issues

**Detection**: During contingency table construction (T020a)

**Handling**:
- Enforce minimum 2 bins, maximum 30 bins
- Logged to `results/edge_case_report.json`
- Proceed with adjusted bin count

**Rationale**: Ensure valid Chi-squared test conditions

## Logging Format

All edge cases are logged in JSON format:

```json
{
 "edge_case_id": "EC001",
 "dataset_id": "wine",
 "config": {
 "test_type": "t-test",
 "dependency_structure": "ar1",
 "r": 0.3
 },
 "failure_mode": "insufficient_sample_size",
 "details": "N=45 < 50 threshold",
 "action": "skipped",
 "timestamp": "2024-01-15T10:30:00Z"
}
```

## Impact on Results

- **Skipped Datasets**: Not included in aggregated results
- **Flagged Configurations**: Included but marked in `aggregated_unified.csv`
- **Halted Pipeline**: Clear error message, no partial results

## Validation

Edge case handling is validated through:
1. **Unit Tests**: Verify detection logic
2. **Integration Tests**: Ensure proper logging and continuation
3. **Manual Review**: Check edge case reports for expected behavior

## Future Improvements

- Automatic parameter adjustment for edge cases
- Alternative methods for problematic configurations
- More granular edge case categorization
