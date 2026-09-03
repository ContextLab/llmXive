# Sync Impact Report: Constitution Amendment (Statistical Methods)

**Amendment ID**: T000a
**Status**: Pending Human Ratification
**Target**: `constitutions/FR-030.md`

## Overview

This report details the technical and operational impact of the proposed amendment to Principle VI of the Constitution, which changes the statistical methodology from Pearson/McNemar to Point-Biserial/Permutation.

## Affected Artifacts

The following files and modules require modification to align with the amended Constitution:

| File/Module | Current Implementation | Required Change | Severity |
|:--- |:--- |:--- |:--- |
| `code/src/analysis.py` | Uses `scipy.stats.pearsonr` | Replace with `scipy.stats.pointbiserialr` | High |
| `code/src/analysis.py` | N/A | Implement Paired Permutation Test logic | High |
| `code/src/modeling.py` | Outputs standard metrics | Ensure compatibility with permutation inputs | Low |
| `code/data/results/correlation_report.json` | Keys: `pearson_r`, `pearson_p` | Keys: `point_biserial_r`, `point_biserial_p` | Medium |
| `code/data/results/statistical_significance_report.json` | N/A (McNemar logic) | Keys: `p_value` (from permutation) | Medium |
| `code/src/validate_metrics.py` | Validates schema | Update schema validation if keys change | Low |

## Dependency Chain

1. **Constitution Update**: The amendment must be ratified and merged into `constitutions/FR-030.md` before code changes are considered compliant.
2. **Code Implementation**: Tasks T021 (Correlation) and T031 (Significance Testing) depend on this amendment.
3. **Execution**: The pipeline will fail validation if the Constitution is not updated but the code attempts to use the new methods, or vice versa.

## Risk Assessment

- **Low Risk**: The change is a direct substitution of statistical methods. No data ingestion or feature extraction logic is affected.
- **Medium Risk**: The output schema for `correlation_report.json` and `statistical_significance_report.json` will change. Downstream visualization or reporting tools (e.g., T034) must be updated to handle the new keys.
- **Mitigation**: All schema changes are backward-incompatible but clearly defined. The `validate_schema` module will need to be updated to expect the new keys.

## Verification Steps

Upon implementation, the following steps will verify compliance:

1. **Schema Check**: Confirm `code/data/results/correlation_report.json` contains `point_biserial_r` and `point_biserial_p`.
2. **Logic Check**: Confirm `code/src/analysis.py` imports `pointbiserialr` and contains a `permutation_test` function.
3. **Constitution Check**: Confirm `constitutions/FR-030.md` contains the text "Point-Biserial" and "Permutation".

## Conclusion

This amendment is critical for the scientific validity of the project. The impact is localized to the analysis phase and is straightforward to implement. No re-ingestion of data is required.

**Next Steps**:
1. Human reviewer merges PR.
2. Create marker file `amendment_ratified.md`.
3. Proceed with T000c (Verification) and subsequent analysis tasks.