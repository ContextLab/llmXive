# Spec Override: Rejection of FR-003 (CLR on Alpha Diversity)

**Date**: 2023-10-27
**Reference**: FR-003 (Original Specification)
**Status**: REJECTED / CORRECTED

## 1. Original Requirement (FR-003)

The original feature requirement FR-003 stated:
> "System MUST apply Centered Log-Ratio (CLR) transformation to Alpha Diversity metrics (e.g., Shannon Index) prior to correlation analysis."

## 2. Rationale for Rejection

This requirement is **mathematically invalid** and methodologically unsound for the following reasons:

1. **Nature of Alpha Diversity**: Alpha diversity indices (such as Shannon Index, Simpson Index) are scalar summary statistics derived from the relative abundance distribution of a community. They represent a single value per sample, not a composition vector.
2. **CLR Definition**: The Centered Log-Ratio (CLR) transformation is defined for compositional data vectors $x = (x_1, x_2,..., x_D)$ where $x_i > 0$ and $\sum x_i = C$ (constant). The transformation is:
 $$ clr(x)_i = \ln \left( \frac{x_i}{g(x)} \right) $$
 where $g(x)$ is the geometric mean of the components.
3. **Inapplicability**: Applying CLR to a single scalar value (the Shannon Index) is undefined. There is no vector of components to normalize, and no geometric mean of components to calculate. Even if one attempts to treat the scalar as a 1D vector, the geometric mean equals the value itself, resulting in $\ln(1) = 0$ for all samples, which destroys all variance and renders correlation analysis impossible.
4. **Statistical Validity**: Alpha diversity indices are typically treated as continuous, unbounded (or semi-bounded) variables. Standard parametric or non-parametric tests (e.g., Pearson/Spearman correlation) can be applied directly to the raw index values, potentially after standard normalization (e.g., Z-score) if required for regression scaling, but **not** CLR.

## 3. Corrected Requirement

The requirement FR-003 is hereby **REJECTED** and replaced with the following corrected specification:

> **Corrected FR-003**: "System MUST compute Shannon Index on **raw** count data. The resulting alpha diversity values MUST be used directly (raw or Z-score normalized) for correlation and regression analysis. **CLR transformation MUST NOT be applied to alpha diversity metrics.**"

## 4. Implementation Impact

- **`code/diversity.py`**: Must calculate Shannon Index from raw OTU/ASV counts using `scikit-bio` or equivalent.
- **`code/analysis.py`**: Correlation analysis (Spearman/Pearson) and regression models must use the raw `shannon_index` column.
- **`code/transformation.py`**: CLR transformation logic, if implemented, must be strictly scoped to taxonomic abundance matrices (compositional vectors) and must explicitly exclude alpha diversity columns.

## 5. Verification

- Unit tests in `tests/unit/test_diversity.py` will verify that `shannon_index` is calculated from raw counts.
- Integration tests will verify that no CLR transformation is applied to the `shannon_index` column before statistical testing.

---
**Approved by**: Automated Science Pipeline Validator
**Linked Task**: T045 (Spec Override Implementation)
**Linked Task**: T020 (Shannon Calculation)