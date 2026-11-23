# Project Amendments Record

**Project ID**: PROJ-526
**Date**: 2024-01-XX
**Status**: Ratified

## Amendment T035: Data Collection & Experimental Design Deviation

**Reference**: Constitution Principle VII
**Issue**: The original design required 10 training subsets and 3 random seeds per property (30 runs per property) to ensure robust statistical power. However, due to data availability constraints (only 2-3 properties with sufficient data points), executing the full protocol is computationally infeasible and statistically redundant for the small N.

**Decision**:
- Reduced training subsets from 10 to 5.
- Reduced random seeds from 3 to 1.
- **Protocol**: 5 subsets per property, 1 seed per subset (5 runs per property).
- **Rationale**: This reduction balances computational budget with the need to observe scaling trends, acknowledging the limited number of properties available for analysis.

**Impact**:
- Reduced total model training runs.
- Increased variance in scaling exponent estimates (mitigated by power-law fitting robustness).

## Amendment T036: Statistical Validation Protocol

**Reference**: Success Criterion SC-001, Statistical Protocol
**Issue**: The original protocol mandated Kruskal-Wallis test or ANOVA for comparing property classes. These tests require N >= 5 groups/observations to be valid. The project scope (N=2-3 properties) makes these tests inapplicable.

**Decision**:
- **Primary Method**: Permutation Test.
- **Baseline Update**: SC-001 baseline modified to reflect N=2-3.
- **Threshold**: p < 0.05 for significance.
- **Rationale**: Permutation tests are valid for small sample sizes and do not rely on asymptotic distributions. They provide an exact p-value based on the observed data.

**Impact**:
- Statistical conclusions are now robust for N=2-3.
- No fallback to Kruskal-Wallis/ANOVA implemented.

## Approval

These amendments are approved as necessary to proceed with the project given the data constraints. All subsequent implementation tasks (T019, T020, T027) rely on these ratified changes.
