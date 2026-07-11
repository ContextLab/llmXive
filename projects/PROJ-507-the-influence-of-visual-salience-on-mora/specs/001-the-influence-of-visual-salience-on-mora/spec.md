# Feature Specification: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Feature Branch**: `001-visual-salience-moral-judgments`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "The Influence of Visual Salience on Moral Judgments of Simulated Scenarios"

## User Scenarios & Testing

### User Story 1 - Data Preparation and Salience Manipulation (Priority: P1)

The system must ingest open visual datasets (e.g., Visual Genome), identify morally ambiguous images via a two-stage process (metadata filtering + human coding), and programmatically generate manipulated variants with controlled luminance contrast/brightness levels (low, medium, high) while preserving semantic content.

**Why this priority**: This is the foundational data layer. Without valid, controlled stimulus generation and verified ambiguity, no experimental data can be collected, and the research question cannot be addressed. It is the MVP for the research pipeline.

**Independent Test**: Can be fully tested by running the data processing pipeline on a subset of 5 raw images. The test must verify: (1) the initial metadata filter correctly identifies candidates, (2) the human coding step correctly labels ambiguity with ≥80% inter-rater reliability (See FR-008), and (3) the output images show measurable pixel-level contrast/brightness changes in target regions without altering object identity or scene semantics, as verified by a secondary validation script.

**Acceptance Scenarios**:

1. **Given** a raw image from an open visual dataset (e.g., Visual Genome) with moral annotations, **When** the salience manipulation script is executed with "high" intensity parameters, **Then** the output image exhibits a statistically significant increase in local contrast/brightness in the target region compared to the original, while the semantic content (object labels, scene layout) remains unchanged.
2. **Given** a set of 20 identified ambiguous scenarios, **When** the batch processing pipeline runs, **Then** Multiple manipulated variants (medium and high salience) are generated for each scenario, resulting in a total of 60 stimulus images ready for survey deployment.

---

### User Story 2 - Survey Deployment and Data Collection (Priority: P2)

The system must present the manipulated images to participants in a randomized within-subject design (See FR-002), collect blame ratings on a Likert scale, and store the responses in a structured format.

**Why this priority**: This enables the core data collection required to test the hypothesis. While dependent on US-001 for stimuli, it is the primary interface for generating the empirical evidence.

**Independent Test**: Can be fully tested by running a pilot survey with a small cohort of test participants, verifying that each participant sees the randomized sequence of images, provides a valid rating, and that the data is correctly logged with participant ID, image ID, salience level, and rating.

**Acceptance Scenarios**:

1. **Given** a deployed survey with 60 manipulated images, **When** a participant completes the survey, **Then** the system records a unique participant ID, the specific image ID shown, the salience level (low/medium/high), and the 1-7 blame rating without data loss or truncation.
2. **Given** a participant who has already viewed a specific scenario at "low" salience, **When** they reach the next block for that scenario, **Then** the system presents the "medium" or "high" salience variant (never the same one twice) to ensure valid within-subject comparison.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system must perform a repeated-measures ANOVA on the collected data to test for salience effects, apply Bonferroni correction for multiple comparisons, and generate a report with effect sizes and confidence intervals.

**Why this priority**: This transforms raw data into scientific findings. It is the final step that answers the research question and validates the methodology.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic dataset with known effect sizes and verifying that the output report correctly identifies the significant effect, applies the correction, and calculates the effect size (e.g., partial eta-squared) within a 5% margin of error of the theoretical value.

**Acceptance Scenarios**:

1. **Given** a dataset of participants with complete within-subject ratings, **When** the analysis script runs, **Then** it outputs a repeated-measures ANOVA table showing the F-statistic, p-value (corrected), and partial eta-squared for the salience factor.
2. **Given** a significant main effect of salience, **When** post-hoc pairwise comparisons are requested, **Then** the system performs Bonferroni-corrected t-tests between all salience pairs (low vs. medium, medium vs. high, low vs. high) and reports which specific contrasts drive the effect.

---

### Edge Cases

- What happens when the image dataset contains images that cannot be successfully manipulated (e.g., target object detection fails)? The system must log these failures and exclude them from the final stimulus set, ensuring the analysis only includes valid data.
- How does the system handle participants who provide identical ratings for all images (straight-lining)? The system must flag these responses as invalid during data cleaning and exclude them from the statistical analysis.
- What happens if the sample size falls below the planned range? The system must still run the analysis but report the reduced power and wider confidence intervals, explicitly noting the limitation in the final report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest images from open visual datasets (e.g., Visual Genome) and programmatically enhance luminance contrast/brightness of target regions to create low, medium, and high salience variants while preserving semantic content (verified during development by object detection model with >95% IoU overlap) (See US-001).
- **FR-002**: System MUST deploy a survey interface that randomizes the presentation order of salience levels for each scenario within a within-subject design (See US-002).
- **FR-003**: System MUST collect blame ratings on a 1-7 Likert scale for each manipulated image, capturing participant ID, image ID, salience level, and timestamp (See US-002).
- **FR-004**: System MUST perform a repeated-measures ANOVA to test the main effect of visual salience on blame ratings, ensuring the analysis accounts for the within-subject design. The system MUST check for sphericity (Mauchly's test) and apply Greenhouse-Geisser or Huynh-Feldt corrections if the assumption is violated (See US-003).
- **FR-005**: System MUST apply Bonferroni correction to all post-hoc pairwise comparisons to control for family-wise error rate when testing multiple salience contrasts (See US-003).
- **FR-006**: System MUST calculate and report effect sizes (partial eta-squared) and 95% confidence intervals for all significant findings (See US-003).
- **FR-007**: System MUST implement a data cleaning routine to exclude participants who provide [deferred] identical ratings across all items (straight-lining) to ensure data validity (See US-003).
- **FR-008**: System MUST identify morally ambiguous scenarios using a two-stage process: (1) initial filtering via open dataset metadata (e.g., Visual Genome 'social' or 'conflict' tags) to narrow the candidate pool, followed by (2) a mandatory human coding step where ≥2 independent annotators label scenarios as 'morally ambiguous' with ≥80% inter-rater reliability (Cohen's κ ≥ 0.8). Scenarios failing this consensus check are excluded (See US-001).

### Key Entities

- **Scenario**: A morally ambiguous visual situation (e.g., traffic accident) identified from the source dataset, serving as the experimental unit.
- **Stimulus Variant**: A specific manipulated version of a Scenario (low/medium/high salience) used as a survey item.
- **Response**: A single data point linking a Participant to a Stimulus Variant, containing the blame rating and metadata.
- **Participant**: An individual completing the survey, contributing multiple responses (one per stimulus variant per scenario).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The pixel-level contrast/brightness change in target regions is measured against the original image to verify the manipulation was successful (See US-001).
- **SC-002**: The effect size (partial eta-squared) of visual salience on blame ratings is measured against the null hypothesis of no effect to determine statistical significance (See US-003).
- **SC-003**: The family-wise error rate is measured against the nominal alpha level (0.05) to verify that Bonferroni correction was correctly applied (See US-003).
- **SC-004**: The proportion of valid participants (excluding straight-liners) is measured against the total recruited sample to ensure data quality (See US-002).
- **SC-005**: The 95% confidence interval width for the estimated effect size is measured against a [deferred] precision threshold to assess the reliability of the estimate (See US-003).

## Assumptions

- The open visual datasets (e.g., Visual Genome) contain sufficient morally ambiguous scenarios with clear target objects for salience manipulation.
- The 1-7 Likert scale for blame ratings is a valid and reliable measure of moral judgment in this context, consistent with established psychological literature.
- Participants recruited via the chosen platform (e.g., Prolific, university pool) will provide honest and attentive responses, and the sample size is sufficient to detect a medium effect size with [deferred] power.
- The analysis will be conducted on CPU-only infrastructure; therefore, the dataset size and statistical methods are constrained to those tractable within 7 GB RAM and 6 hours of compute time.
- The visual salience manipulation (luminance contrast/brightness enhancement) is the primary mechanism of attentional capture, and other visual features (color, motion) are held constant.
- The relationship between visual salience and blame ratings is causal, as the design is a controlled experiment with within-subject manipulation of the independent variable, provided confounds are controlled.
- The Bonferroni correction is appropriate for controlling family-wise error rate given the small number of planned pairwise comparisons.