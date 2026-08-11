# Specification Override: FR-003 Rejection

## Task ID
T045

## Original Requirement (Rejected)
**FR-003 (Original)**: "System MUST compute alpha diversity (Shannon index) on CLR-transformed counts."

## Reason for Rejection
The application of Centered Log-Ratio (CLR) transformation prior to the calculation of alpha diversity indices (specifically Shannon Index) is mathematically invalid for this study design.

1. **Scale Invariance**: Alpha diversity metrics like Shannon Index are designed to measure the entropy of the relative abundance distribution within a sample. They are inherently scale-invariant.
2. **CLR Properties**: The CLR transformation maps compositional data from the simplex to real Euclidean space by taking the log of the ratio of each component to the geometric mean of all components.
3. **Mathematical Conflict**: Applying Shannon's formula ($H = -\sum p_i \ln p_i$) to CLR-transformed values ($y_i = \ln(x_i / g(x))$) distorts the probabilistic interpretation of $p_i$. The resulting value does not represent entropy in the information-theoretic sense nor the biological diversity intended by the metric. It introduces artifacts dependent on the zero-replacement strategy and the specific geometric mean of the CLR denominator, rather than the true community structure.
4. **Plan Correction**: The research plan explicitly mandates the use of **raw counts** (normalized to relative abundances internally by the diversity function) to ensure the Shannon Index reflects true ecological diversity.

## Corrected Requirement
**FR-002 (Corrected)**: "System MUST compute alpha diversity (Shannon index) using `scikit-bio` on the OTU/ASV tables **using raw counts** (not CLR-transformed)."

## Implementation Impact
- **Module**: `code/diversity.py`
- **Function**: `calculate_shannon_index`
- **Change**: Input data must be raw count tables (or tables normalized to relative abundance *after* or *during* calculation, but not pre-transformed via CLR).
- **Verification**: The pipeline will verify that `code/diversity.py` does not import or apply `code/transformation.py` (CLR) before calculating Shannon Index.

## Status
**APPROVED** - Effective immediately for PROJ-077.

## References
- Research Plan: "Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance"
- Task: T045 (Spec Override)
- Related Task: T046 (Spec Override SC-001)
