# Feature Specification: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Feature Branch**: `001-visual-salience-moral-judgments`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "The Influence of Visual Salience on Moral Judgments of Simulated Scenarios"

## User Scenarios & Testing

### User Story 1 - Data Preparation and Salience Manipulation (Priority: P1)

The system must ingest open visual datasets (e.g., Visual Genome), identify morally ambiguous images via a two-stage process (metadata filtering + human coding), and programmatically generate manipulated variants with controlled luminance contrast/brightness levels (low, medium, high) while preserving semantic content.

**Why this priority**: This is the foundational data layer. Without valid, controlled stimulus generation and verified ambiguity, no experimental data can be collected, and the research question cannot be addressed. It is the MVP for the research pipeline.

**Independent Test**: Can be fully tested by running the data processing pipeline on a subset of raw images. The test must verify: (1) the initial metadata filter correctly identifies candidates, (2) the human coding step correctly labels ambiguity with a 5-point Likert scale (1=Not ambiguous, 5=Highly ambiguous) and Cohen's κ ≥ 0.6 (See FR-008), (3) the output images show measurable pixel-level contrast/brightness changes (RMS contrast) in target regions without altering object identity or scene semantics, verified by a semantic similarity model (CLIP) with cosine similarity ≥ 0.95 AND a pilot human manipulation check where ≥80% of coders confirm the 'moral narrative' is preserved.

**Acceptance Scenarios**:

1. **Given** a raw image from an open visual dataset (e.g., Visual Genome) with moral annotations, **When** the salience manipulation script is executed with "high" intensity parameters, **Then** the output image exhibits a statistically significant increase in local RMS contrast in the target region compared to the original, while the semantic content (object labels, scene layout) remains unchanged (verified by a semantic similarity model with cosine similarity ≥ 0.95 AND a pilot human rating confirming moral narrative preservation).
2. **Given** a set of A set of ambiguous scenarios will be identified., **When** the batch processing pipeline runs, **Then** Multiple manipulated variants (medium and high salience) are generated for each scenario, resulting in a set of stimulus images ready for survey deployment.

---

### User Story 2 - Survey Deployment and Data Collection (Priority: P2)

The system must present the manipulated images to participants in a randomized within-subject design (See FR-002), collect blame ratings on a 1-7 Likert scale, and store the responses in a structured format.

**Why this priority**: This enables the core data collection required to test the hypothesis. While dependent on US-001 for stimuli, it is the primary interface for generating the empirical evidence.

**Independent Test**: Can be fully tested by running a pilot survey with a small cohort of test participants, verifying that each participant sees the randomized sequence of images, provides a valid rating, and that the data is correctly logged with participant ID, image ID, salience level, and rating.

**Acceptance Scenarios**:

1. **Given** a deployed survey with A set of manipulated images will be generated to investigate [Research Question] using [Method], as established in prior work [Citation]., **When** a participant completes the survey, **Then** the system records a unique participant ID, the specific image ID shown, the salience level (low/medium/high), and the 1-7 blame rating (1=Not at all blameworthy, 7=Extremely blameworthy) without data loss or truncation.
2. **Given** a participant who has already viewed a specific scenario at "low" salience, **When** they reach the next block for that scenario, **Then** the system presents the "medium" or "high" salience variant (never the same one twice) to ensure valid within-subject comparison.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system must perform a Linear Mixed-Effects Model (LMM) analysis on the collected data to test for salience effects, applying robust corrections for multiple comparisons and generating a report with effect sizes and confidence intervals.

**Why this priority**: This transforms raw data into scientific findings. It is the final step that answers the research question and validates the methodology.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic dataset with known effect sizes and verifying that the output report correctly identifies the significant effect, applies the correction, and calculates the effect size (e.g., partial eta-squared) within an acceptable margin of error of the theoretical value.

**Acceptance Scenarios**:

1. **Given** a dataset of participants with complete within-subject ratings, **When** the analysis script runs, **Then** it outputs an LMM table showing the fixed effect of salience, random intercepts for Participant and Scenario, p-value (corrected), and partial eta-squared.
2. **Given** a significant main effect of salience, **When** post-hoc pairwise comparisons are requested, **Then** the system performs Bonferroni-corrected tests between all salience pairs (low vs. medium, medium vs. high, low vs. high) and reports which specific contrasts drive the effect.

---

### Edge Cases

- What happens when the image dataset contains images that cannot be successfully manipulated (e.g., target object detection fails)? The system must log these failures and exclude them from the final stimulus set, ensuring the analysis only includes valid data.
- How does the system handle participants who provide identical ratings for all images (straight-lining)? The system must flag these responses as invalid during data cleaning and exclude them from the statistical analysis (variance < 0.1 or >90% identical ratings).
- What happens if the sample size falls below the planned range? The system must still run the analysis but report the reduced power and wider confidence intervals, explicitly noting the limitation in the final report. The system MUST perform a post-hoc power analysis (using G*Power or equivalent) with the observed effect size and flag if power < 0.80.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest images from open visual datasets (e.g., Visual Genome) and programmatically enhance luminance contrast/brightness of target regions to create low, medium, and high salience variants while preserving semantic content. Validation requires: (1) CLIP cosine similarity ≥ 0.95 between original and manipulated image embeddings, (2) RMS contrast change ≥ 15% in the target region (ROI defined by bounding box), (3) texture and edge density changes < 0.05 (Stimulus-Control Integrity), and (4) a pilot human manipulation check where ≥80% of a separate coder panel confirms the 'moral narrative' is preserved (See US-001).
- **FR-002**: System MUST deploy a survey interface that randomizes the presentation order of salience levels for each scenario within a within-subject design. Randomization constraints: no two identical scenarios in a row; balanced order of salience levels across participants (See US-002).
- **FR-003**: System MUST collect blame ratings on a 1-7 Likert scale for each manipulated image, capturing participant ID, image ID, salience level, and timestamp. The scale anchors are explicitly defined as: 1=Not at all blameworthy, 7=Extremely blameworthy (See US-002).
- **FR-004**: System MUST perform a Linear Mixed-Effects Model (LMM) to test the main effect of visual salience on blame ratings, ensuring the analysis accounts for the nested data structure. The model MUST include random intercepts for both Participant and Scenario. The system MUST check for normality of residuals (Shapiro-Wilk test); if violated, the system MUST switch to a robust alternative (e.g., LMM with ordinal link function or non-parametric bootstrap) (See US-003).
- **FR-005**: System MUST apply Bonferroni correction to all 3 post-hoc pairwise comparisons (Low vs Medium, Medium vs High, Low vs High) to control for family-wise error rate when testing multiple salience contrasts. If the normality assumption is violated, the system MUST use a robust alternative (e.g., Wilcoxon signed-rank test with Bonferroni correction) (See US-003).
- **FR-006**: System MUST calculate and report effect sizes (partial eta-squared) and confidence intervals for all significant findings. The effect size MUST be calculated using Type III Sums of Squares for the LMM (See US-003).
- **FR-007**: System MUST implement a data cleaning routine to exclude participants who provide identical ratings across all items (straight-lining). A participant is excluded if the variance of their ratings is < 0.1 OR if >90% of their ratings are identical (See US-003).
- **FR-008**: System MUST identify morally ambiguous scenarios using a two-stage process: (1) initial filtering via open dataset metadata (e.g., Visual Genome 'social' or 'conflict' tags) to narrow the candidate pool, followed by (2) a mandatory human coding step using script `04_human_coding.py`. In this step, ≥3 independent annotators rate each scenario on a 5-point Likert scale (1=Not ambiguous, 5=Highly ambiguous) based on specific dimensions (conflict of duty, uncertainty of outcome). Scenarios are labeled 'morally ambiguous' if the mean score ≥ 3.5 AND Cohen's κ ≥ 0.6. Disagreements are resolved by majority vote. Scenarios failing this consensus check are excluded (See US-001).

### Key Entities

- **Scenario**: A morally ambiguous visual situation (e.g., traffic accident) identified from the source dataset, serving as the experimental unit.
- **Stimulus Variant**: A specific manipulated version of a Scenario (low/medium/high salience) used as a survey item.
- **Response**: A single data point linking a Participant to a Stimulus Variant, containing the blame rating and metadata.
- **Participant**: An individual completing the survey, contributing multiple responses (one per stimulus variant per scenario).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The pixel-level contrast/brightness change (RMS contrast) in target regions is measured against the original image to verify the manipulation was successful. Additionally, the 'moral narrative preservation' is measured against a pilot human rating (≥80% agreement) (See US-001).
- **SC-002**: The effect size (partial eta-squared) of visual salience on blame ratings is measured against the null hypothesis of no effect to determine statistical significance using an LMM with random intercepts (See US-003).
- **SC-003**: The family-wise error rate is measured against the nominal alpha level (0.05) to verify that Bonferroni correction was correctly applied to the 3 pairwise comparisons (See US-003).
- **SC-004**: The proportion of valid participants (excluding straight-liners) is measured against the total recruited sample to ensure data quality (See US-002).
- **SC-005**: The 95% confidence interval width for the estimated effect size is measured against a pre-registered precision threshold of ≤ 0.3 to assess the reliability of the estimate (See US-003).

## Assumptions

- The open visual datasets (e.g., Visual Genome) contain sufficient morally ambiguous scenarios with clear target objects for salience manipulation.
- The 1-7 Likert scale for blame ratings is a valid and reliable measure of moral judgment in this context, consistent with established psychological literature.
- Participants recruited via the chosen platform (e.g., Prolific, university pool) will provide honest and attentive responses, and the sample size is sufficient to detect a medium effect size with adequate power (≥0.80) given the number of scenarios (≥20).
- The analysis will be conducted on CPU-only infrastructure; therefore, the dataset size and statistical methods are constrained to those tractable within 7 GB RAM and substantial compute time.
- The visual salience manipulation (luminance contrast/brightness enhancement) is the primary mechanism of attentional capture, and other visual features (color, motion) are held constant.
- The relationship between visual salience and blame ratings is causal, as the design is a controlled experiment with within-subject manipulation of the independent variable, provided confounds are controlled.
- The Bonferroni correction is appropriate for controlling family-wise error rate given the small number of planned pairwise comparisons (3).
- The human coding step (FR-008) is feasible and will yield a sufficient number of 'morally ambiguous' scenarios (≥20) from the Visual Genome candidate pool.