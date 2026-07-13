# Feature Specification: The Impact of Social Comparison on Self-Perception in AI-Generated Image Platforms

**Feature Branch**: `001-synthetic-body-comparison`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Do upward social comparisons with AI-generated idealized body images on image-sharing platforms produce stronger negative effects on body image self-perception than comparisons with human-generated idealized images, after controlling for platform usage frequency and baseline comparison orientation?"

## User Scenarios & Testing

### User Story 1 - Controlled Stimulus Presentation and Immediate Self-Report (Priority: P1)

As a research participant, I want to view a randomized sequence of idealized body images (half AI-generated, half human-generated) one-by-one and immediately report my body satisfaction after each image, so that the study can capture the acute psychological impact of image origin on self-perception without block-order confounds.

**Why this priority**: This is the core data collection mechanism. Without the ability to present stimuli in a fully randomized, image-by-image sequence and capture the dependent variable (BISS score) immediately, the primary hypothesis cannot be tested, and block-order effects cannot be controlled.

**Independent Test**: A test script can simulate a participant session, presenting human and AI images in random order (one at a time), recording BISS scores after each image, and verifying that the dataset contains the correct image-type labels, timestamps, and corresponding scores for analysis.

**Acceptance Scenarios**:

1. **Given** a participant has completed the consent form and baseline survey, **When** they view the first image, **Then** the system displays the image and prompts for a BISS score immediately after the image is viewed.
2. **Given** a participant has submitted a BISS score for an image, **When** the next image loads, **Then** the system ensures the new image is distinct from the previous one and maintains the global randomized sequence constraint.
3. **Given** a participant finishes the final image, **When** they submit the final BISS score, **Then** the system records the timestamp and flags the session as complete for export.

---

### User Story 2 - Baseline Covariate Collection (Priority: P2)

As a researcher, I want to collect each participant's baseline comparison orientation (INCOM score) and platform usage frequency before they view any images, so that I can control for individual differences in social comparison tendency and exposure history during statistical analysis.

**Why this priority**: The research question explicitly requires controlling for "baseline comparison orientation" and "platform usage frequency." Without these covariates, the analysis cannot isolate the effect of image origin, failing the methodology check.

**Independent Test**: A test script can submit a participant profile with specific INCOM scores and usage hours, verify the data is stored correctly, and confirm the analysis script correctly retrieves these values as covariates in the LME model.

**Acceptance Scenarios**:

1. **Given** a new participant joins the study, **When** they complete the intake survey, **Then** the system records their INCOM score (0-60 scale) and average weekly hours spent on image-sharing platforms.
2. **Given** a participant has completed the intake survey, **When** they proceed to the image viewing phase, **Then** the system validates that the INCOM and usage data are present before unlocking the stimulus presentation.

---

### User Story 3 - Statistical Analysis and Hypothesis Testing (Priority: P3)

As a researcher, I want to run a Linear Mixed Effects (LME) model on the collected data with "Image Type" as the fixed within-subject factor, "INCOM" and "Usage Frequency" as fixed between-subject covariates, and "Participant ID" as a random intercept, so that I can determine if AI-generated images produce significantly lower body satisfaction scores than human-generated images while correctly modeling the data structure.

**Why this priority**: This delivers the final research output. It transforms raw data into the empirical answer required by the research question, specifically testing the main effect of Image Type and its interaction with covariates using a methodologically valid approach for mixed data structures.

**Independent Test**: A test script can load a mock dataset with known differences between AI and Human conditions, run the analysis pipeline, and verify that the output includes the fixed effect estimates, p-values, and effect sizes for the "Image Type" factor and its interactions.

**Acceptance Scenarios**:

1. **Given** a complete dataset of 150 participants with BISS scores and covariates, **When** the analysis script is executed, **Then** it performs a Linear Mixed Effects (LME) analysis and outputs a summary table containing the estimate, t-value, and p-value for the "Image Type" factor.
2. **Given** the analysis is complete, **When** the results are generated, **Then** the system explicitly reports whether the p-value for the Image Type effect is < 0.05, indicating a statistically significant difference.
3. **Given** multiple hypothesis tests are run (e.g., main effects and interactions), **When** the analysis concludes, **Then** the system applies a family-wise error correction (e.g., Bonferroni) and reports the adjusted p-values.

---

### Edge Cases

- What happens if a participant fails to complete the full sequence of 40 images (e.g., drops out after 20)? The system MUST exclude their partial data from the analysis to maintain statistical validity. Imputation is NOT performed as no specific missing-data strategy is defined.
- How does the system handle participants with extreme INCOM scores (outliers)? The analysis script MUST flag these for sensitivity analysis or robust statistical methods to ensure the covariate does not skew the results.
- What happens if the pre-validated image set is missing a match for a specific human image? The system MUST use a pre-validated backup set of matched AI images to ensure the "matched sets" constraint is met without breaking the randomization.

## Requirements

### Functional Requirements

- **FR-001**: System MUST present a randomized sequence of idealized body images (comprising both AI-generated and human-generated stimuli) to each participant to ensure the within-subjects design is maintained. (See US-1)
- **FR-002**: System MUST administer the Body Image States Scale (BISS) immediately after each individual image to capture acute changes in self-perception. (See US-1)
- **FR-003**: System MUST collect the Iowa-Netherlands Comparison Orientation Measure (INCOM) score and platform usage frequency as covariates prior to image exposure. (See US-2)
- **FR-004**: System MUST execute a Linear Mixed Effects (LME) model with "Image Type" as the fixed within-subject factor, "INCOM" and "Usage Frequency" as fixed between-subject covariates, and "Participant ID" as a random intercept. The system MUST output a JSON object containing keys: `f_stat` (or t-stat), `p_value`, `eta_squared` (or effect size), and `n`. (See US-3)
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to the statistical output when testing multiple hypotheses (main effects and interactions) to control family-wise error. (See US-3)
- **FR-006**: System MUST run all statistical analysis on a CPU-only environment without requiring GPU acceleration. The analysis pipeline MUST complete within ≤ 3600 seconds and use ≤ 7GB RAM on the standard GitHub Actions `ubuntu-latest` runner. The system MUST load pre-generated static assets for all stimuli; no on-the-fly image generation is permitted. (See Assumptions)
- **FR-007**: System MUST validate that the dataset contains all required variables (Image Type, BISS Score, INCOM, Usage Frequency) before initiating the analysis script. Validation passes ONLY if ≥ 95% of values are non-null and the participant count is ≥ 150. (See US-3)
- **FR-008**: System MUST validate that the AI and Human image sets are matched by metadata (pose, lighting, body type) before presentation. If the metadata validation fails, the system MUST block the study launch. (See US-1)
- **FR-009**: System MUST validate that the AI and Human image sets are visually indistinguishable in a blind pre-test. The system MUST report a p-value > 0.05 for the difference in visual quality ratings between the two sets before the study begins. (See Assumptions)

### Key Entities

- **Participant**: An individual user who provides consent, baseline demographics, INCOM scores, and BISS responses.
- **Stimulus**: An image entity with attributes `id`, `origin` (AI/Human), `match_group` (to ensure paired comparison), `file_path`, and `metadata` (pose, lighting, body type).
- **Response**: A record linking a `Participant` to a specific `Stimulus`, containing the `BISS_score`, `timestamp`, and `stimulus_id`.
- **AnalysisResult**: The output entity containing the statistical metrics (estimate, t-value, p-value, effect size) derived from the LME model.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in mean BISS scores between AI and Human image conditions is measured against the null hypothesis of no difference (p < 0.05) to determine statistical significance. (See US-3)
- **SC-002**: The effect size (Cohen's d or partial eta-squared equivalent) of the "Image Type" factor is measured against the LME output to quantify the magnitude of the synthetic perfection effect. (See US-3)
- **SC-003**: The family-wise error rate is measured against the alpha level of 0.05 after applying the Bonferroni correction to ensure valid inference across multiple tests. (See US-3)
- **SC-004**: The completion rate of the full image sequence is measured against the target of [deferred] of enrolled participants to ensure sufficient power for the within-subjects design. (See US-1)
- **SC-005**: The runtime of the full analysis pipeline (from data ingestion to result generation) is measured against the specific threshold of ≤ 3600 seconds on the `ubuntu-latest` runner configuration to confirm CPU feasibility. (See Assumptions)

## Assumptions

- **Dataset-variable fit**: The curated set of 20 human images and the generated set of 20 AI images are assumed to be matched for body type, pose, and lighting, such that "Image Type" is the only systematic difference. This matching is verified by FR-008 (metadata) and FR-009 (blind pre-test).
- **Inference framing**: Since this is an experimental design with random assignment to image order, findings regarding the "Image Type" effect will be framed as causal regarding the *stimulus origin*, provided the within-subjects design holds.
- **Compute feasibility**: The analysis assumes that the statistical computations (LME) will fit within the RAM (≤ 7GB) and CPU time limits (≤ 3600 seconds) of the GitHub Actions free tier. AI images are PRE-GENERATED and stored as static assets; no runtime generation occurs.
- **Measurement validity**: The BISS and INCOM instruments are assumed to be valid and reliable for the target population (university students/public volunteers) without requiring re-validation for this specific context.
- **Threshold justification**: The significance threshold is fixed at p < 0.05, consistent with standard psychological research conventions; a sensitivity analysis will sweep this threshold over {0.01, 0.05, 0.10} to report how the conclusion varies.
- **Power considerations**: The sample size of 150 participants is assumed to provide sufficient power (>0.80) to detect a medium effect size (f = 0.25) in a Linear Mixed Effects model; if power is lower, this will be acknowledged as a limitation.
- **No GPU dependency**: The system relies on pre-generated images. The statistical analysis assumes no GPU acceleration is required.
- **Visual Indistinguishability**: The AI and Human image sets are assumed to be indistinguishable in visual quality metrics (e.g., smoothness, symmetry) other than origin, as verified by the blind pre-test (FR-009).