# Amendment 001: Replacement of FR-003

**Date**: 2026-06-29
**Status**: Ratified

## Summary
This amendment replaces the original Functional Requirement FR-003 (Repeated-Measures ANOVA) with a **Permutation Test** (n=1000) to assess the significance of the difference in D-scores between complexity conditions.

## Justification
The original ANOVA requirement is methodologically invalid because 'Stimulus Set' is perfectly confounded with 'Complexity Level'. A parametric ANOVA would violate the assumption of independence. A Permutation Test provides a non-parametric alternative that correctly handles the stimulus-set confound by randomizing labels within the observed data structure.

## Impact
- **FR-003**: Updated to require Permutation Test.
- **Code**: `code/analysis/permutation.py` must implement the new logic.
- **Spec**: `spec.md` updated to reference this amendment.
