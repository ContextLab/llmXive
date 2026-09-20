# Amendment: Methodology Overrides

## 1. Sample Size Threshold (N < 130 vs N < 30)
**Original Spec (FR-002):** Halt if N < 30.
**Amendment:** Halt if N < 130.
**Justification:** The Plan Phase 1 requirement (N < 130) provides higher statistical power to detect small-to-medium effects, aligning with modern standards for regression analysis in social science. The Spec's N < 30 threshold is insufficient for reliable multiple regression with 4 predictors.

## 2. Robustness Check Condition
**Original Spec (FR-006):** Conditional robustness check (only if engagement correlation > 0.3).
**Plan Proposal:** Unconditional robustness check.
**Implementation Status:** The current implementation (T025) follows the Spec's conditional logic. The Plan proposes an amendment to make it unconditional. This deviation is noted for future Spec alignment.

## 3. Spec Consistency Note
The Plan's overrides are documented here to preserve the Spec as the source of truth while recording necessary deviations for scientific rigor. Future updates should align the Spec with these methodology overrides.
