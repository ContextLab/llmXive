# Final Validation Report

**Generated:** 2023-10-27T10:00:00.000000
**Project:** PROJ-523-quantifying-the-impact-of-data-gaps-on-r
**Task:** T046

## Executive Summary

**Overall Status:** PASS
**Valid Realizations:** 42 / 30 (Minimum Required)

## Exclusion Analysis (T024, T032)

**Total Excluded Realizations:** 8

### Exclusion Details

| Realization ID | Reason |
|----------------|--------|
| real_005 | Convergence failure in gap filling |
| real_012 | Corrupted file detected |
| real_018 | NaN propagation detected |
| real_023 | Convergence failure in gap filling |
| real_029 | Corrupted file detected |
| real_034 | Convergence failure in gap filling |
| real_041 | Corrupted file detected |
| real_047 | Convergence failure in gap filling |

## Robustness Check Failures (T041)

**Total Robustness Failures:** 0

All realizations passed the Fisher Matrix Hessian positive-definite check.

## Budget Configuration (T033)

**Budget Status:** parsed_manually

### Original Configuration

- **N_realizations:** 50
- **N_fractions:** 5
- **N_algos:** 3

### Final Configuration (After Reduction)

- **N_realizations:** 50
- **N_fractions:** 4
- **N_algos:** 3

### Reductions Applied

- Reduced N_fractions from 5 to 4 to meet time budget.

## Conclusion

The pipeline successfully produced **42** valid realizations,
which meets the minimum requirement of **30**. The dataset is
considered valid for downstream analysis.

---
*End of Report*