# Spec Override: FR-003 Rejection and Correction

## Original Requirement (Rejected)

**FR-003**: System MUST compute alpha diversity (Shannon index) on CLR-transformed OTU/ASV tables.

## Rejection Rationale

This requirement is **mathematically invalid**. The Shannon Index is a measure of entropy derived from probability distributions (relative abundances) of raw counts. Applying a Centered Log-Ratio (CLR) transformation prior to Shannon calculation distorts the underlying probability distribution, as CLR operates on log-ratios of geometric means rather than raw proportions. Calculating Shannon on CLR-transformed data yields a metric that does not represent true biological diversity and violates standard ecological definitions.

## Corrected Requirement

**FR-002**: System MUST compute alpha diversity (Shannon index) using `scikit-bio` on the OTU/ASV tables **using raw counts** (not CLR-transformed).

## Implementation Specification

1. **Input**: The `diversity.py` module must accept OTU/ASV tables containing **raw integer counts**.
2. **Validation**: The module MUST validate that input values are non-negative integers. If non-integer or negative values are detected (indicating a potential CLR transformation or data error), the process MUST halt with a `ValueError` stating: "Shannon Index requires raw counts. CLR-transformed data detected."
3. **Calculation**: Use `scikit-bio.diversity.alpha.shannon` (or equivalent implementation) on the raw count matrix.
4. **Output**: A column `shannon_index` added to the processed dataset.
5. **CLR Usage**: CLR transformation (implemented in `transformation.py`) is **strictly reserved** for secondary path analyses (e.g., Lasso regression on taxa) and must **never** be applied to the `shannon_index` calculation.

## Dependency

This override supersedes the original FR-003 in the main specification and is a prerequisite for Task T020 (Shannon Index Calculation).

## Verification

- Unit tests in `tests/unit/test_diversity.py` must verify that `calculate_shannon_index` fails on CLR-transformed data.
- Integration tests must confirm that `shannon_index` values are derived from raw counts.