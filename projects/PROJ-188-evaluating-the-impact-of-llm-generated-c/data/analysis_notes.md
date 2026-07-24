# Statistical Model Selection Notes

## Date: 2023-10-27
## Project: PROJ-188 Evaluating the Impact of LLM-Generated Code Explanations

### Model Selection Decision

This document records the statistical model selection for the analysis of user study data, specifically addressing the choice between a Generalized Linear Mixed Model (GLMM) and a Linear Mixed Model (LMM).

#### Requirement Specification

**Spec FR-005** explicitly mandates the use of a Linear Mixed Model (LMM) with participant-only random intercepts for the primary analysis. The specification states:

> "Use a Linear Mixed Model (LMM) with participant-only random intercepts to account for repeated measures within participants."

#### Initial Design Consideration (Rejected)

The initial design plan suggested a Generalized Linear Mixed Model (GLMM) with random effects for both `participant_id` and `snippet_id`. The rationale was to control for potential variability in both participants and code snippets.

**Rejection Reason**: This approach was explicitly rejected to maintain strict alignment with **Spec FR-005**. The specification's mandate for an LMM with *only* participant random intercepts takes precedence over the initial design rationale. Using a GLMM with snippet random effects would deviate from the approved experimental design and statistical analysis plan. The GLMM rationale found in earlier planning drafts is hereby invalidated.

#### Selected Model: Linear Mixed Model (LMM)

The final model is a Linear Mixed Model (LMM) configured as follows:

- **Fixed Effects**:
 - `condition`: Categorical variable representing the three experimental conditions (Code Only, Code+LLM, Code+Docstring).
 - `complexity`: Categorical variable representing the code complexity level (low, medium, high).
 - `condition:complexity`: Interaction term between condition and complexity to test if the effect of explanation type varies by code complexity.

- **Random Effects**:
 - `(1|participant_id)`: Random intercepts for participants only. This accounts for the non-independence of multiple responses from the same participant. No random slopes or snippet-level random effects are included, strictly adhering to the "participant-only" constraint of FR-005.

- **Family/Distribution**:
 - **Gaussian**: The response variable `answer` is treated as a continuous measure (e.g., accuracy score or normalized correctness) for the purpose of this LMM, or the analysis assumes a linear approximation suitable for the LMM framework as mandated by the spec. If the response is strictly binary, the spec's mandate for an LMM (Gaussian) overrides the typical GLMM approach for binary outcomes, likely implying a pre-processing step (e.g., averaging per condition) or an approximation. *Note: Implementation in `code/03_analysis.py` follows the Gaussian family as per the LMM mandate.*

- **Model Formula**:
 ```
 answer ~ condition * complexity + (1|participant_id)
 ```

#### Implementation Details

The model is implemented in `code/03_analysis.py` using the `statsmodels` library (`MixedLM`).

- **Fixed Effects Design Matrix**: Includes columns for condition (dummy coded), complexity (dummy coded), and their interaction.
- **Random Effects Design Matrix**: Identity matrix for the grouping variable `participant_id`.
- **Estimation Method**: Restricted Maximum Likelihood (REML) is used for parameter estimation, which provides unbiased estimates of variance components.

#### Justification for LMM over GLMM in this Context

While GLMMs are often preferred for binary outcomes (like correctness) to handle non-Gaussian distributions directly, the project specification (FR-005) explicitly requires an LMM. This requirement may stem from:
1. **Simplicity and Interpretability**: LMMs are computationally less intensive and easier to interpret for certain audiences.
2. **Robustness**: With a sufficient sample size, LMMs can be robust to mild deviations from normality.
3. **Alignment with Pre-registered Plan**: The analysis plan was pre-registered with an LMM, and deviating to a GLMM would require a protocol amendment.
4. **Specific Research Question Focus**: The primary interest is in the fixed effects (condition, complexity, interaction) rather than the precise distributional assumptions of the residuals.

By adhering to the LMM specification, we ensure that the analysis results are directly comparable to the pre-registered plan and meet the project's governance requirements.

### Plan Update Reference

This decision aligns with the update to `plan.md` (Task T026c), which removed the contradictory GLMM rationale from the 'Complexity Tracking' section and explicitly documented the LMM as the Spec-compliant choice. The text "Spec FR-005 mandates LMM with participant-only random intercepts; GLMM rejected for non-compliance" has been recorded in the project plan.

### Next Steps

- Proceed with implementing the LMM in `code/03_analysis.py` as described.
- Conduct post-hoc Tukey HSD tests for pairwise condition comparisons (Task T027).
- Perform BLEU sensitivity analysis (Task T028).
- Generate the final report (Task T029).

---
*This note serves as the official record of the statistical model selection decision, explicitly documenting the rejection of the GLMM rationale in favor of the Spec FR-005 mandate for an LMM.*
