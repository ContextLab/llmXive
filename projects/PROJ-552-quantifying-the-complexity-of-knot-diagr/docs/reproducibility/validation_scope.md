# Validation Scope Documentation

## Overview

This document defines and documents the validation scope for the crossing
number data in the Knot Atlas dataset, specifically validating against the
OEIS A002863 sequence.

## Validation Target: OEIS A002863

**Sequence**: A002863 - Number of prime knots with n crossings

**Reference URL**: https://oeis.org/A002863

**Description**: This sequence enumerates the number of distinct prime knots
for each crossing number n. The values are well-established in knot theory
literature and serve as the definitive reference for crossing number counts.

## Reference Values (n ≤ 13)

| Crossing Number (n) | Prime Knot Count |
|---------------------|------------------|
| 0 | 1 |
| 1 | 0 |
| 2 | 0 |
| 3 | 1 |
| 4 | 1 |
| 5 | 2 |
| 6 | 3 |
| 7 | 7 |
| 8 | 21 |
| 9 | 49 |
| 10 | 165 |
| 11 | 552 |
| 12 | 2176 |
| 13 | 9988 |

## Validation Methodology

1. **Data Source**: Cleaned knot data from `data/processed/knots_cleaned.csv`
2. **Validation Module**: `code/analysis/oeis_validation.py`
3. **Validation Process**:
 - Load all knots from the cleaned dataset
 - Group knots by crossing number
 - Compare counts against OEIS A002863 reference values
 - Record matches and mismatches
 - Calculate deviation for each crossing number

## Validation Scope Boundaries

### Included
- All prime knots with crossing number 0 through 13
- Full dataset from Knot Atlas
- Hyperbolic and non-hyperbolic knots (before filtering)

### Excluded
- Composite knots (not prime)
- Knots with crossing number > 13
- Virtual knots
- Non-classical knot types

## Validation Criteria

**Pass Condition**: All crossing number counts match OEIS A002863 exactly

**Fail Condition**: Any crossing number count deviates from OEIS A002863

**Tolerance**: Zero tolerance for count deviations (exact match required)

## Implementation Details

The validation is implemented in `code/analysis/oeis_validation.py` with the
following key components:

- `OeisValidator`: Main validator class
- `ValidationEntry`: Per-crossing-number comparison record
- `ValidationResult`: Aggregate validation results
- `validate_oeis_a002863()`: Main validation function
- `main()`: Command-line entry point

## Output Artifacts

- **JSON Results**: `data/processed/oeis_validation_results.json`
 Contains detailed per-crossing-number validation entries

- **This Document**: `docs/reproducibility/validation_scope.md`
 Documents the validation scope, methodology, and criteria

## Relationship to Other Validations

This OEIS validation is distinct from:
- **T019**: Hyperbolic volume filtering (excludes non-hyperbolic knots)
- **T040**: KnotInfo cross-validation for hyperbolic volume
- **T026**: Core invariant tabulation accuracy (crossing number, braid index)

The OEIS A002863 validation specifically validates the **count** of knots at
each crossing number, not the individual knot properties.

## Reproducibility Notes

- Validation script: `code/analysis/oeis_validation.py`
- Input data: `data/processed/knots_cleaned.csv`
- Reference: OEIS A002863 (static, no versioning required)
- Execution: `python code/analysis/oeis_validation.py`
- Exit code: 0 for pass, 1 for fail

## Version History

| Date | Version | Author | Notes |
|------------|---------|--------|-------|
| 2026-01-01 | 1.0 | System | Initial validation scope document for T020 |

## References

1. OEIS Foundation Inc. (2026). A002863 - Number of prime knots with n crossings.
 https://oeis.org/A002863

2. Hoste, J., Thistlethwaite, M., & Weeks, J. (1998). The first 1,701,936 knots.
 Experimental Mathematics, 7(4), 293-318.

3. Knot Atlas. (2026). Prime Knot Census. http://katlas.org
