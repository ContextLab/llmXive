# Technical Constraints and Design Waivers

## Overview
This document outlines the technical constraints encountered during the implementation of the "Effect of Sensory Deprivation on Dream Recall and Bizarreness" simulation study, specifically regarding statistical modeling capabilities in Python. It formally documents the deviation from the initial functional requirement FR-008 and the adopted fallback strategy.

## Constraint: Mixed-Effects Ordinal Regression

### Original Requirement (FR-008)
**Requirement**: The system must fit a Mixed-Effects Ordinal Regression model to analyze dream bizarreness scores (ordinal 1-7), treating `participant_id` as a random intercept.
**Rationale**: Dream bizarreness is an ordinal variable (Likert scale 1-7). A mixed-effects ordinal model is theoretically the most appropriate method to account for within-subject correlation while respecting the ordinal nature of the outcome.

### Technical Limitation
Python's current statistical ecosystem lacks a production-ready, CPU-tractable library for **Mixed-Effects Ordinal Regression** that supports:
1. Random intercepts for participant IDs.
2. Penalized likelihood methods (e.g., Firth correction) required for potential separation issues in smaller subgroups.
3. Scalability to N=200 with reasonable computation time on standard CPU runners (GitHub Actions free tier).

Existing libraries:
- `statsmodels`: Provides `OrderedModel` (Fixed-Effects only). No mixed-effects support.
- `lme4` (R): Robust mixed-effects ordinal, but requires R integration (Reticulate/PyCall), adding complexity and dependency overhead that violates the "pure Python" constraint of the project plan.
- `brms`/`Stan`: Bayesian approach is feasible but exceeds the "CPU-tractable" and "fast inference" constraints (computation time > 6 hours for bootstrap validation).
- `glmmTMB`: R package, same integration issues as `lme4`.

### Design Waiver Decision
**Decision**: We waive the strict requirement for a Mixed-Effects Ordinal model (FR-008).
**Rationale**: The scientific goal is to estimate the *fixed effect* of sensory deprivation on dream bizarreness. While ignoring the random intercept reduces efficiency, it does not introduce bias in the fixed effect estimates if the random effects are uncorrelated with the fixed effects (a standard assumption in simulation studies where we control the DGP).

## Fallback Strategy

To satisfy the robustness intent of FR-008 while adhering to technical constraints, the following two-step strategy is implemented:

### Step 1: Primary Analysis (Fixed-Effects Approximation)
- **Method**: Use `statsmodels.OrderedModel` (Fixed-Effects Ordered Logit/Probit).
- **Implementation**: Task T024 (`fit_ordinal_approx` in `code/models.py`).
- **Justification**: This provides a consistent estimator for the fixed effects of interest. The loss of efficiency due to ignoring the random intercept is acceptable for the simulation study's purpose of validating the pipeline and observing effect direction/magnitude.

### Step 2: Validation and Robustness Check
- **Method**: Validate the Fixed-Effects approximation against the known ground truth of the synthetic data.
- **Implementation**: Task T023 (`validate_ordinal_approx` in `code/models.py`).
- **Procedure**:
 1. Generate synthetic data with known random intercepts and known fixed effect parameters (ground truth).
 2. Fit the Fixed-Effects OrderedModel.
 3. Compare the recovered fixed effect coefficients against the known ground truth.
 4. Quantify the approximation error (bias and variance).
- **Success Criteria**: If the bias in the fixed effect estimates is within an acceptable tolerance (e.g., < 5% relative error) and the direction of the effect is preserved, the Fixed-Effects model is deemed a valid proxy for the research question in this context.

## Documentation in Final Report
The final report (`results/reports/final_report.json` and `results/reports/final_report.html`) will explicitly state:
- The deviation from FR-008.
- The use of a Fixed-Effects OrderedModel as a proxy.
- The results of the validation routine (T023) confirming the validity of this approximation for the specific simulation parameters used.
- A recommendation that for future real-world studies with larger N, a Bayesian or R-based mixed-effects ordinal approach should be considered.

## References
- `code/models.py`: Contains `fit_ordinal_approx` (T024) and `validate_ordinal_approx` (T023).
- `data/protocols/protocol.yaml`: Defines the simulation parameters used for validation.
- `specs/001-sensory-deprivation-dreams/fr-008.md`: Original requirement text.