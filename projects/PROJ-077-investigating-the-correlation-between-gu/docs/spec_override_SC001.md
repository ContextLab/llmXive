# Spec Override: Rejection of SC-001 (CLR-transformed alpha diversity)

**Date:** 2023-10-27
**Status:** Approved
**Reference:** Plan Correction for Phase 4 (User Story 2)

## Original Specification (SC-001)

**Original Requirement:**
> "System MUST compute the correlation between **CLR-transformed** alpha diversity (Shannon Index) and fluid intelligence."

**Rationale in Original Spec:**
The original specification assumed that because compositional data requires CLR transformation for inter-taxa comparisons, the alpha diversity metric itself (a summary statistic) must also be CLR-transformed to maintain consistency with the "compositional nature" of the dataset.

## Rejection Justification

The requirement to apply Centered Log-Ratio (CLR) transformation to the **Shannon Index** is **mathematically invalid** and methodologically unsound for the following reasons:

1. **Nature of the Metric**: The Shannon Index ($H' = -\sum p_i \ln p_i$) is already a normalized, scale-invariant summary statistic derived from relative abundances ($p_i$). It represents the entropy of the distribution and is bounded by $\ln(S)$, where $S$ is the number of observed species. It is not a compositional vector subject to the constant-sum constraint in the same way raw counts or relative abundance vectors are.

2. **Domain of CLR**: The CLR transformation is defined for a vector of positive components $x = (x_1, \dots, x_D)$ as:
 $$clr(x)_i = \ln \left( \frac{x_i}{g(x)} \right)$$
 where $g(x)$ is the geometric mean of the components.
 Applying CLR to a **scalar** (the single Shannon Index value per sample) is undefined. There is no vector of components to compute a geometric mean against, nor is there a simplex constraint to normalize.

3. **Distortion of Interpretation**: If one were to force a log-transformation on the Shannon Index (e.g., $\ln(H')$), it would arbitrarily distort the linear relationship with the outcome variable (Fluid Intelligence) without addressing any compositional artifact, as the Shannon Index is already a function of proportions. This would introduce unnecessary non-linearity and obscure the biological signal.

4. **Statistical Consistency**: Standard ecological and microbiome literature (e.g., McMurdie & Holmes, 2014; Gloor et al., 2017) distinguishes between transforming **feature matrices** (taxa abundances) via CLR for regression/correlation, and analyzing **alpha diversity** (scalars) using standard parametric or non-parametric tests (e.g., Spearman, t-test) on the raw index values.

## Corrected Requirement

The system requirement is hereby corrected to:

> **System MUST measure the correlation of Raw Shannon Index.**
>
> "The analysis pipeline shall compute the Spearman rank correlation coefficient between the **untransformed** (raw) Shannon Index values and the Fluid Intelligence scores. No CLR or log-transformation shall be applied to the Shannon Index column."

## Implementation Impact

- **Code Change**: The `code/analysis.py` module (Task T022) must utilize the `shannon_index` column directly from `data/processed/cleaned_data.csv` without applying `np.log` or any CLR-like operation.
- **Validation**: The validation script `code/validate_sc001.py` (Task T028) must verify that the input to the correlation function is the raw index.
- **Documentation**: All subsequent reports and visualizations must label the metric as "Raw Shannon Index" to prevent ambiguity.

## References

- Gloor, G. B., Macklaim, J. M., Pawlowsky-Glahn, V., & Egozcue, J. J. (2017). Microbiome datasets are compositional: and this is not optional. *Frontiers in Microbiology*, 8, 2224.
- McMurdie, P. J., & Holmes, S. (2014). Waste not, want not: why rarefying microbiome data is inadmissible. *PLOS Computational Biology*, 10(4), e1003531.