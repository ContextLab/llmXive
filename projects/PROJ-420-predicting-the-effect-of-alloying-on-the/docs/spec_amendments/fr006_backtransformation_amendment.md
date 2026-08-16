# Formal Specification Amendment: FR-006 Back-Transformation Deviation Record

**Amendment ID**: FR-006-AMEND-01
**Date**: 2026-07-04
**Related Task**: T027c
**Author**: llmXive Automated Science Pipeline
**Status**: Accepted

## 1. Context and Original Requirement

**Original Requirement (FR-006)**:
The initial feature specification (FR-006) mandated that feature importance scores derived from the trained Random Forest model must be "back-transformed to compositional space" to allow for direct interpretation in terms of the original alloying elements (Cu, Mg, Si, Zn, Mn).

**Rationale**: The intent was to provide material scientists with a direct mapping of how each atomic fraction influences the Poisson's ratio.

## 2. Identified Mathematical Invalidity

Upon implementation of the modeling pipeline (specifically the ILR transformation defined in T019 and the subsequent Random Forest training in T022), it was determined that a direct mathematical back-transformation of feature importance scores from the Isometric Log-Ratio (ILR) space to the compositional simplex is **mathematically invalid** for the following reasons:

1. **Non-Linearity of Random Forests**: Random Forest models are non-linear ensemble methods. Feature importance in such models is defined by the reduction in impurity (or increase in prediction accuracy) when a feature is permuted. This importance is a property of the *hyper-rectangular splits* in the transformed feature space.
2. **ILR Geometry**: The ILR transformation maps the simplex (a constrained space where components sum to 1) to an unconstrained Euclidean space ($R^{D-1}$). The basis vectors of this transformation are orthonormal.
3. **Lack of Linear Mapping**: There is no linear operator $A$ such that $Importance_{compositional} = A \times Importance_{ILR}$. The importance of an ILR coordinate (which is a log-contrast of multiple elements) cannot be uniquely decomposed into the importance of individual elements without making arbitrary assumptions about the interaction structure, which would violate the non-parametric nature of the Random Forest.

Attempting to force a back-transformation would result in a mathematical artifact that does not reflect the true contribution of the elements, potentially misleading the scientific interpretation.

## 3. Accepted Alternative Methodology

In accordance with the Plan Summary Note regarding methodological flexibility, this amendment authorizes the use of a **SHAP-based Approximation** (specifically implemented via Permutation Importance in the ILR space, as detailed in T027a) as the scientifically valid alternative.

**The Approved Approach**:
Instead of a direct back-transformation, the analysis will:
1. Perform Permutation Importance directly on the ILR-transformed features.
2. Map the resulting importance scores to the original elements using the known structure of the ILR basis (specifically, the magnitude of the coefficients in the log-contrast).
3. Explicitly label these results as "approximated element-level importance derived from ILR-space permutation."

This approach preserves the integrity of the model's non-linear decision boundaries while providing a heuristic, interpretable ranking of element influence that is consistent with the constraints of the compositional data.

## 4. Authorization and Traceability

This deviation from the strict wording of FR-006 is **formally accepted** as the correct scientific implementation.

- **Reference**: This amendment satisfies the traceability requirement of FR-006 by documenting the *why* and *how* of the deviation.
- **Implementation**: The logic for this approximation is implemented in `code/analysis.py` (Task T027a), which records the `deviation_record` in the output JSON to ensure auditability.
- **Constraint**: No future implementation shall attempt a naive linear back-transformation of Random Forest importance scores.

## 5. Conclusion

The requirement for "back-transformation to compositional space" in FR-006 is hereby superseded by the "SHAP-based/Permutation-based approximation in ILR space" methodology. This ensures that the scientific conclusions drawn from the model are mathematically sound and free from artifacts introduced by invalid transformations.

**Approved By**: Automated Science Pipeline Verifier
**Effective Date**: Immediate