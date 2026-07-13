# Feature Specification: The Impact of Text Message Tone on Perceived Emotional Support

**Feature Branch**: `001-text-tone-emotional-support`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "The Impact of Text Message Tone on Perceived Emotional Support"

## User Scenarios & Testing

### User Story 1 - Stimulus Generation and Data Collection (Priority: P1)

As a researcher, I need to generate a controlled set of text message stimuli varying in paralinguistic features (emoji, punctuation, length) and assign them to relational contexts (close friend vs. acquaintance) so that I can collect human ratings of perceived emotional support.

**Why this priority**: This is the foundational step; without the generated stimuli and the collection of independent human ratings, no analysis can occur. It directly addresses the core experimental manipulation.

**Independent Test**: Can be fully tested by running the stimulus generation script to produce a JSON file of unique message variants and verifying that a sample of participants can successfully complete the rating survey and submit data containing the required fields (stimulus ID, relationship type, rating score) without errors.

**Acceptance Scenarios**:
1. **Given** a list of base scenarios (e.g., "I had a rough day"), **When** the system generates variants with 3 emoji levels, 2 punctuation levels, and 2 length levels (based on pilot data and factorial design efficiency), **Then** A set of unique stimulus texts is produced with metadata linking them to their specific feature combinations.
2. **Given** a participant recruited via Prolific, **When** they complete the survey, **Then** their data record includes a unique ID, the specific stimulus ID they rated, the randomized relationship context (friend/acquaintance), and a numeric rating on the 1-7 Likert scale.

---

### User Story 2 - Statistical Analysis Pipeline (Priority: P2)

As a researcher, I need to execute a Linear Mixed-Effects Model (LMM) with random intercepts for Participant and Stimulus on the collected rating data to test for the interaction effect between relationship type and cue intensity on perceived emotional support.

**Why this priority**: This is the primary analytical method specified in the research plan to answer the main research question. It transforms raw data into the primary statistical evidence and correctly handles the hierarchical data structure.

**Independent Test**: Can be fully tested by running the analysis script against a mock dataset containing the expected structure (subject ID, stimulus ID, condition, rating) and verifying that the output includes the fixed effect estimates, p-values, and effect sizes for the interaction term, without requiring GPU acceleration.

**Acceptance Scenarios**:
1. **Given** a clean dataset of participants rating stimuli, **When** the LMM script executes, **Then** it produces a summary table showing the main effects of Relationship and Cue Intensity, and the Interaction Effect, with significance levels calculated using Satterthwaite approximation for degrees of freedom.
2. **Given** a significant interaction effect (p < 0.05), **When** the post-hoc analysis runs, **Then** it performs Tukey-corrected pairwise comparisons and outputs a matrix indicating which specific cue levels differ significantly between friend and acquaintance contexts.

---

### User Story 3 - Methodological Robustness and Sensitivity Reporting (Priority: P3)

As a reviewer, I need the system to automatically perform a sensitivity analysis on the definition of "Cue Intensity" (including multivariate weighting) and report on the robustness of the findings to ensure the results are not artifacts of arbitrary cutoff choices.

**Why this priority**: This addresses the methodological soundness requirement for threshold justification and sensitivity, ensuring the findings are defensible against critiques of arbitrary operationalization.

**Independent Test**: Can be fully tested by modifying the script to sweep the "Cue Intensity" definition across a range of multivariate weightings and verifying that the system outputs a sensitivity report showing how the interaction p-value and effect size change across these variations.

**Acceptance Scenarios**:
1. **Given** the primary analysis result, **When** the sensitivity analysis module runs, **Then** it re-runs the LMM with at least 3 alternative multivariate definitions of "High" cue intensity (e.g., varying the relative weight of emoji vs. punctuation) and logs the resulting F-statistics.
2. **Given** multiple hypothesis tests are performed (main effects + interaction + post-hoc), **When** the correction module runs, **Then** it applies the Tukey correction to the family-wise error rate and reports the adjusted p-values for all comparisons.

---

### Edge Cases

- What happens if a participant provides the same rating (e.g., all 4s) for every stimulus (straight-lining)? The system must detect this pattern and flag the participant's data for exclusion.
- How does the system handle missing data if a participant drops out before rating all stimuli? The system must implement a listwise deletion or appropriate imputation strategy for the LMM, documenting the exclusion criteria.
- What if the relationship context (friend vs. acquaintance) is not successfully randomized for a participant? The system must log a warning and exclude that participant's data to maintain the integrity of the within-subjects design.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a set of unique text message stimuli by systematically combining 3 levels of emoji presence, 2 levels of punctuation patterns, and 2 levels of message length, ensuring no two stimuli share the same combination of these features. (See US-1)
- **FR-002**: System MUST collect independent human ratings on a 7-point Likert scale for perceived emotional support from a minimum of [deferred] unique participants (determined by power analysis), with each participant rating stimuli in both "close friend" and "acquaintance" contexts, verified via Prolific ID. (See US-1)
- **FR-003**: System MUST execute a Linear Mixed-Effects Model (LMM) with random intercepts for Participant and Stimulus to test for the interaction effect between sender relationship type and paralinguistic cue intensity. (See US-2)
- **FR-004**: System MUST perform Tukey-corrected post-hoc pairwise comparisons if the interaction effect is statistically significant (p < 0.05) to identify specific differences between cue levels. (See US-2)
- **FR-005**: System MUST conduct a sensitivity analysis by re-running the primary LMM with at least three alternative multivariate operationalizations of the "Cue Intensity" definition (e.g., varying the relative weights of emoji, punctuation, and length) and report the stability of the interaction effect. (See US-3)
- **FR-006**: System MUST detect and flag participants who exhibit straight-lining behavior (e.g., variance equals zero across the full set of 40 stimuli) for data exclusion. (See US-1)
- **FR-007**: System MUST ensure all statistical computations are performed using CPU-only methods (e.g., `statsmodels`, `lmerTest`) compatible with free-tier CI runners (≤7 GB RAM, no GPU). (See US-2)

### Key Entities

- **Stimulus**: A text message variant defined by its base scenario, emoji count, punctuation pattern, and length category.
- **Participant**: A unique human subject providing ratings, associated with a demographic profile (age 18-35).
- **Rating**: A numeric value (1-7) representing the perceived emotional support for a specific stimulus in a specific relational context.
- **AnalysisResult**: The output of the statistical test, containing fixed effect estimates, p-values, and effect sizes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The interaction effect fixed effect estimate and p-value for "Relationship × Cue Intensity" are measured against the null hypothesis of no interaction, with significance determined at α = 0.05. (See US-2)
- **SC-002**: The stability of the interaction effect is measured against the variation in p-values obtained from the sensitivity analysis across the three alternative multivariate cue intensity definitions. (See US-3)
- **SC-003**: The family-wise error rate for post-hoc comparisons is measured against the Tukey-corrected threshold to ensure the probability of Type I error remains ≤ 0.05. (See US-3)
- **SC-004**: The data quality is measured against the exclusion criteria, ensuring that participants with straight-lining behavior (variance = 0 across the full set of stimuli) are identified and removed from the final analysis set. (See US-1)
- **SC-005**: The computational feasibility is measured against the constraint that the entire analysis pipeline (generation, collection, LMM, sensitivity) must complete within 6 hours on a standard CPU-only runner (GitHub Actions 2-core) under the target N determined by power analysis. (See US-2)

## Assumptions

- The dataset (simulated stimuli and human ratings) will fit within the ~7 GB RAM and ~14 GB disk limits of the free-tier GitHub Actions runner, as the data consists of [deferred] text strings and [deferred] numeric ratings.
- The "perceived emotional support" metric relies on the validity of the 7-point Likert scale, assuming participants interpret the scale consistently.
- The "close friend" and "acquaintance" contexts are effectively operationalized by the instruction text provided to participants, assuming participants can reliably distinguish between these relational categories in a hypothetical scenario.
- The sample size WILL BE determined to provide sufficient statistical power to detect a medium effect size for the interaction term, based on standard power analysis for Linear Mixed-Effects Models (α=0.05, power=0.80).
- The paralinguistic features (emoji, punctuation) are the primary drivers of perceived support, and other unmeasured variables (e.g., specific word choice beyond length) are controlled or randomized by the stimulus construction process.
- No GPU or CUDA acceleration is required or available; all statistical modeling uses CPU-optimized libraries (`statsmodels`, `lmerTest`).