# Architecture Decision Records (ADRs)

## ADR-001: Use of Welch's t-test

**Status**: Accepted
**Date**: 2023-10-27

### Context
The project requires statistical comparison of latency distributions between different compiler optimization configurations. The initial specification mentioned a "paired t-test", but the configurations are independent binaries.

### Decision
We will use **Welch's Independent Samples t-test** to compare configurations. This is statistically more appropriate for independent samples with potentially unequal variances.

### Consequences
- More accurate p-values for independent comparisons.
- Spec FR-004 must be updated to reflect "Welch's t-test".
- Implementation in `code/analysis/stats.py`.

## ADR-002: Fixed Iteration Count

**Status**: Accepted
**Date**: 2023-10-27

**Context**: The Plan listed "[deferred]" for iterations, but statistical power requires a fixed number of samples.

**Decision**: We will use a fixed iteration count of **1000** per configuration (Constitution Principle VII). An adaptive stop condition (CV ≤ 1% after 30 iterations) is implemented as a secondary safety check only.

**Consequences**:
- Consistent runtime budget across configurations.
- Plan must be updated to reflect "Fixed 1000 iterations".

## ADR-003: Stability Threshold

**Status**: Accepted
**Date**: 2023-10-27

**Context**: The Spec mentions "valid" configurations but does not define stability.

**Decision**: A configuration is considered **stable** if its L2 relative error is ≤ 1e-5. Configurations exceeding this are marked "UNSTABLE" and excluded from final statistical analysis and the final Pareto frontier.

**Consequences**:
- Clear criteria for inclusion in final results.
- Unstable runs are retained in raw logs for audit.

## ADR-004: Memory Pressure Handling

**Status**: Accepted
**Date**: 2023-10-27

**Context**: Large tensor dimensions (768x768) may exceed available RAM on some systems.

**Decision**: The executor will automatically downsample to 512x512 if allocation fails. Downsampled runs will be marked in logs and included in the exploration plot with a distinct visual indicator.

**Consequences**:
- Improved robustness on low-memory systems.
- Clear distinction between standard and downsampled runs in visualizations.
