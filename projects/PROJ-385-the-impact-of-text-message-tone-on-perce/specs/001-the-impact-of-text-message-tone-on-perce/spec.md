# Feature Specification: The Impact of Text Message Tone on Perceived Emotional Support

**Feature Branch**: `001-text-tone-emotional-support`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "The Impact of Text Message Tone on Perceived Emotional Support"

## User Scenarios & Testing

### User Story 1 - Stimulus Generation and Data Collection (Priority: P1)

As a researcher, I need to generate a controlled set of text message stimuli varying in paralinguistic features (emoji, punctuation, length) and assign them to relational contexts (close friend vs. acquaintance) so that I can collect human ratings of perceived emotional support.

**Why this priority**: This is the foundational step; without the generated stimuli and the collection of independent human ratings, no analysis can occur. It directly addresses the core experimental manipulation.

**Independent Test**: Can be fully tested by running the stimulus generation script to produce a JSON file of unique message variants, AND verifying that a real dataset file `data/raw/real_ratings.csv` exists containing ratings from actual Prolific submissions (not simulated data) with the required fields (stimulus ID, relationship type, rating score, Prolific ID).

**Acceptance Scenarios**:
1. **Given** a list of base scenarios (e.g., "I had a rough day"), **When** the system generates variants with A small set of emoji levels (e.g., none, single, multiple)., Multiple punctuation levels (e.g., Standard, Excessive), and 2 length levels (Short <10 words, Long ≥10 words), **Then** A set of unique stimulus texts is produced with metadata linking them to their specific feature combinations.
2. **Given** a participant recruited via Prolific, **When** they complete the survey, **Then** their data record includes a unique ID, the specific stimulus ID they rated, the randomized relationship context (friend/acquaintance), and a numeric rating on the 1-7 Likert scale.

---

### User Story 2 - Statistical Analysis Pipeline (Priority: P2)

As a researcher, I need to execute a Linear Mixed-Effects Model (LMM) with random intercepts for Participant and Stimulus on the collected rating data to test for the interaction effect between relationship type and cue intensity on perceived emotional support.

**Why this priority**: This is the primary analytical method specified in the research plan to answer the main research question. It transforms raw data into the primary statistical evidence and correctly handles the hierarchical data structure.

**Independent Test**: Can be fully tested by running the analysis script against the real `data/raw/real_ratings.csv` dataset and verifying that the output includes the fixed effect estimates, p-values, and effect sizes for the interaction term, without requiring GPU acceleration.

**Acceptance Scenarios**:
1. **Given** a clean dataset of participants rating stimuli, **When** the LMM script executes, **Then** it produces a summary table showing the main effects of Relationship and Cue Intensity, and the Interaction Effect, with significance levels calculated using Satterthwaite approximation for degrees of freedom.
2. **Given** a significant interaction effect (p < 0.05), **When** the post-hoc analysis runs, **Then** it performs Tukey-corrected pairwise comparisons and outputs a matrix indicating which specific cue levels differ significantly between friend and acquaintance contexts.

---

### User Story 3 - Methodological Robustness and Sensitivity Reporting (Priority: P3)

As a reviewer, I need the system to automatically perform a sensitivity analysis on the definition of "Cue Intensity" (including alternative weightings of features) and report on the robustness of the findings to ensure the results are not artifacts of arbitrary cutoff choices. The alternative weightings must be grounded in theoretical hypotheses (e.g., "emoji dominance" vs. "punctuation dominance").

**Why this priority**: This addresses the methodological soundness requirement for threshold justification and sensitivity, ensuring the findings are defensible against critiques of arbitrary operationalization.

**Independent Test**: Can be fully tested by modifying the script to sweep the "Cue Intensity" definition across a range of alternative weightings (with cited theoretical basis) and verifying that the system outputs a sensitivity report showing how the interaction effect direction, magnitude, and significance change across these variations.

**Acceptance Scenarios**:
1. **Given** the primary analysis result, **When** the sensitivity analysis module runs, **Then** it re-runs the LMM with at least 3 alternative operationalizations of "Cue Intensity" (Equal Weight, Emoji-Dominant, Punctuation-Dominant) and logs the resulting F-statistics and effect coefficients.
2. **Given** multiple hypothesis tests are performed (main effects + interaction + post-hoc), **When** the correction module runs, **Then** it applies the Tukey correction to the family-wise error rate and reports the adjusted p-values for all comparisons.

---

### Edge Cases

- What happens if a participant provides the same rating (e.g., all 4s) for every stimulus (straight-lining)? The system must detect this pattern and flag the participant's data for exclusion.
- How does the system handle missing data if a participant drops out before rating all stimuli? The system must implement a listwise deletion or appropriate imputation strategy for the LMM, documenting the exclusion criteria.
- What if the relationship context (friend vs. acquaintance) is not successfully randomized for a participant? The system must log a warning and exclude that participant's data to maintain the integrity of the within-subjects design.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a set of unique text message stimuli by systematically combining multiple levels of emoji presence (0, 1, 2+), 2 levels of punctuation patterns (Standard, Excessive), and 2 levels of message length (Short <10 words, Long ≥10 words), ensuring no two stimuli share the same combination of these features. (See US-1)
- **FR-002**: System MUST collect REAL human ratings on a Likert scale with multiple points for perceived emotional support from a minimum of 60 unique participants (verified via power analysis for Cohen's f=0.25, power≥0.80, α=0.05, ICC=0.05), with each participant rating stimuli in both "close friend" and "acquaintance" contexts, verified via Prolific ID. The system MUST prohibit the use of simulated or placeholder data for the primary analysis. (See US-1)
- **FR-003**: System MUST execute a Linear Mixed-Effects Model (LMM) with random intercepts for Participant and Stimulus to test for the interaction effect between sender relationship type and paralinguistic cue intensity. (See US-2)
- **FR-004**: System MUST perform Tukey-corrected post-hoc pairwise comparisons if the interaction effect is statistically significant (p < 0.05) to identify specific differences between cue levels. (See US-2)
- **FR-005**: System MUST conduct a sensitivity analysis by re-running the primary LMM with three specific alternative operationalizations of the "Cue Intensity" definition: () Equal Weight (three equally weighted components), (2) Emoji-Dominant (0.6/0.2/0.2), and (3) Punctuation-Dominant (0.2/0.6/0.2), and report the stability of the interaction effect (beta coefficient and p-value) across these variations. (See US-3)
- **FR-006**: System MUST detect and flag participants who exhibit straight-lining behavior (e.g., variance equals zero across the full set of generated stimuli, N_stimuli) for data exclusion. (See US-1)
- **FR-007**: System MUST ensure all statistical computations are performed using CPU-only methods (e.g., `statsmodels`, `lmerTest`) compatible with free-tier CI runners (≤7 GB RAM, no GPU). (See US-2)

### Key Entities

- **Stimulus**: A text message variant defined by its base scenario, emoji count, punctuation pattern, and length category.
- **Participant**: A unique human subject providing ratings, associated with a demographic profile (age 18-35).
- **Rating**: A numeric value (1-7) representing the perceived emotional support for a specific stimulus in a specific relational context.
- **AnalysisResult**: The output of the statistical test, containing fixed effect estimates, p-values, and effect sizes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The interaction effect fixed effect estimate and p-value for "Relationship × Cue Intensity" are measured against the null hypothesis of no interaction, with significance determined at α = 0.05, derived exclusively from `data/raw/real_ratings.csv`. (See US-2)
- **SC-002**: The stability of the interaction effect is measured against the consistency of the effect direction, magnitude, and significance (p < 0.05) across the three alternative operationalizations of cue intensity. (See US-3)
- **SC-003**: The family-wise error rate for post-hoc comparisons is measured against the Tukey-corrected threshold to ensure the probability of Type I error remains ≤ 0.05. (See US-3)
- **SC-004**: The data quality is measured against the exclusion criteria, ensuring that participants with straight-lining behavior (variance = 0 across the full set of N_stimuli) are identified and removed from the final analysis set. (See US-1)
- **SC-005**: The computational feasibility is measured against the constraint that the entire analysis pipeline (generation, collection, LMM, sensitivity) must complete within 6 hours on a standard CPU-only runner (GitHub Actions -core) using the verified N=60 dataset. (See US-2)

## Assumptions

- The dataset (simulated stimuli and human ratings) will fit within the memory and disk limits of the free-tier GitHub Actions runner, as the data consists of text strings and numeric ratings.
- The "perceived emotional support" metric relies on the validity of the 7-point Likert scale, assuming participants interpret the scale consistently.
- The "close friend" and "acquaintance" contexts are effectively operationalized by the instruction text provided to participants, assuming participants can reliably distinguish between these relational categories in a hypothetical scenario.
- The sample size is fixed at 60 participants, determined by a power analysis for a medium effect size (Cohen's f=0.25) in a 2x2 LMM design (power=0.80, alpha=0.05, ICC=0.05).
- The paralinguistic features (emoji, punctuation) are the primary drivers of perceived support, and other unmeasured variables (e.g., specific word choice beyond length) are controlled or randomized by the stimulus construction process.
- No GPU or CUDA acceleration is required or available; all statistical modeling uses CPU-optimized libraries (`statsmodels`, `lmerTest`).
- **External Recruitment Dependency**: The project assumes the feasibility of recruiting a sufficient number of unique participants via Prolific within the project budget and IRB constraints. If recruitment fails to meet the N=60 threshold, the research question is considered unanswerable under the current scope, and the project must be re-evaluated.