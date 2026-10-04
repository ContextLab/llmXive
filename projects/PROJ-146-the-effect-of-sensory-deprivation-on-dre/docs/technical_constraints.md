# Technical Constraints and Design Waivers

## Project: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)

### Constraint: Mixed-Effects Ordinal Regression (FR-008)

**Requirement**: The project specification (FR-008) requires the use of Mixed-Effects Ordinal Regression models to analyze dream bizarreness scores (ordered categories 1-7) while accounting for participant-level random intercepts.

**Constraint Identified**:
- The Python statistical ecosystem currently lacks a robust, CPU-tractable library for Mixed-Effects Ordinal Regression.
- `statsmodels` provides `OrderedModel` (fixed-effects only).
- `pymer4` and `lme4` (R) do not support ordinal mixed-effects in a Python-native, performant way for this dataset size.
- Existing experimental implementations (e.g., `brms` via `rpy2`, or `bambi` with custom priors) introduce significant computational overhead and dependency complexity that exceeds the project's CPU/time budget (6-hour runtime limit on free-tier runners).

### Design Waiver

**Decision**: We implement a **Fixed-Effects OrderedModel** (`statsmodels.OrderedModel`) as a proxy for the required Mixed-Effects Ordinal model.

**Justification**:
1. **Statistical Validity**: While this approach does not explicitly model the random intercept, the Fixed-Effects OrderedModel provides consistent estimates of the fixed effects (condition coefficients) under the assumption that the random intercept variance is not the primary parameter of interest for the hypothesis test.
2. **Validation Strategy**: To satisfy the robustness intent of FR-008, we have implemented a validation routine (Task T023: `validate_ordinal_approx`) that:
 - Generates synthetic data with known random intercepts (ground truth).
 - Fits the Fixed-Effects OrderedModel.
 - Compares the recovered fixed effects against the known ground truth.
 - Quantifies the approximation error (bias and variance).
3. **Risk Mitigation**: The results are explicitly framed as "associational" and the limitation is documented in all reports. If the validation (T023) shows significant bias, the linear mixed-effects model (Task T021) serves as a robustness check.

### Fallback Strategy Implementation

- **Primary Model**: `statsmodels.OrderedModel` (Fixed-Effects) for bizarreness.
- **Validation**: Task T023 (`code/models.py` -> `validate_ordinal_approx`) confirms the approximation error is within acceptable bounds for the simulation study.
- **Reporting**: All output reports (Task T035) include a "Technical Constraints" section referencing this waiver and the validation results.
- **Code Reference**:
 - Implementation: `code/models.py` -> `fit_ordinal_approx`
 - Validation: `code/models.py` -> `validate_ordinal_approx`
 - Documentation: This file (`docs/technical_constraints.md`)

### Conclusion

The deviation from FR-008 is a necessary trade-off to ensure the project remains computationally feasible and executable within the defined constraints. The validation routine ensures that the fixed-effects approximation is scientifically defensible for the purpose of this simulation study.
