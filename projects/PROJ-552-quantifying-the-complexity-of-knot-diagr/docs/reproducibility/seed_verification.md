# Seed Verification Report

**Generated**: 2026-06-02 12:00:00
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Task**: T058 - Verify all random seeds are pinned

## Summary

| Metric | Value |
|--------|-------|
| Total Python files scanned | 47 |
| Files with random operations | 3 |
| Compliant files (all seeds pinned) | 3 |
| Non-compliant files | 0 |
| Total random operations found | 8 |
| Pinned operations | 8 |
| Unpinned operations | 0 |

## Compliance Status

**✓ ALL RANDOM OPERATIONS HAVE PINNED SEEDS**

Per Constitution Principle I, all stochastic operations have documented seed values.

## File-by-File Breakdown

| File | Random Ops | Pinned | Unpinned | Status |
|------|------------|--------|----------|--------|
| code/analysis/complexity_visualization.py | 2 | 2 | 0 | ✓ Compliant |
| code/analysis/regression.py | 4 | 4 | 0 | ✓ Compliant |
| code/analysis/residual_analysis.py | 2 | 2 | 0 | ✓ Compliant |
| code/download/knot_atlas_loader.py | 0 | 0 | 0 | ✓ Compliant |
| code/data/parser.py | 0 | 0 | 0 | ✓ Compliant |
| code/data/validator.py | 0 | 0 | 0 | ✓ Compliant |
| code/reproducibility/logs.py | 0 | 0 | 0 | ✓ Compliant |
| code/reproducibility/hashing.py | 0 | 0 | 0 | ✓ Compliant |
| code/reproducibility/checksums_recorder.py | 0 | 0 | 0 | ✓ Compliant |
| code/reproducibility/derivation_validator.py | 0 | 0 | 0 | ✓ Compliant |
| code/reproducibility/tie_breaking_validator.py | 0 | 0 | 0 | ✓ Compliant |
| code/reproducibility/validation_status_generator.py | 0 | 0 | 0 | ✓ Compliant |

## Violations Detail

No violations detected.

## Pinned Seed Values

The following seed values are documented in the codebase:

| Seed Value | Location(s) |
|------------|-------------|
| 42 | code/analysis/complexity_visualization.py, code/analysis/regression.py, code/analysis/residual_analysis.py |
| 12345 | code/analysis/regression.py |

## Notes

### Census Data Consideration

This project analyzes a **census dataset** (all prime knots with crossing number ≤13).
The primary data source is tabulated from the Knot Atlas ({{claim:c_3ea0f57a}}).
As census data, there is no sampling randomness - all knots are enumerated.

### Stochastic Operations

Found 8 potential random operations across the codebase.
All operations have proper seed pinning for reproducibility.

## Verification Procedure

1. Scanned all `code/**/*.py` files for random operation patterns
2. Checked for seed pinning patterns in each file
3. Extracted seed values and documented locations
4. Verified compliance with Constitution Principle I

## Conclusion

**VERIFICATION PASSED**: All 8 random operations have pinned seeds.
The codebase is compliant with Constitution Principle I (reproducibility).

## Distinction from T050 (random_seeds.md)

This document (**seed_verification.md**) provides **verification** that seeds are pinned.
T050's **random_seeds.md** documents the **values used** in the pipeline.

- `random_seeds.md`: Lists seed values and their purpose (e.g., "42 for visualization")
- `seed_verification.md`: Verifies all stochastic operations have pinned seeds

Both documents are required for complete reproducibility documentation.