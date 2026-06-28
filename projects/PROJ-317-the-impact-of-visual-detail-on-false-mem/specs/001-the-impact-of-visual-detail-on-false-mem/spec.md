# Feature Specification: Visual Detail and False Memory Susceptibility

**Feature Branch**: 001-visual-detail-false-memory  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "The Impact of Visual Detail on False Memory Susceptibility"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Image Manipulation Pipeline (Priority: P1)

Researcher uploads baseline images from Visual Genome and receives two manipulated versions per image: (a) enhanced detail (3-5 minor objects added via compositing) and (b) reduced detail (minor elements blurred/removed).

**Why this priority**: This is the foundation of the entire experiment—without stimulus manipulation, no false memory test can occur. The pipeline must work reliably before any participant testing.

**Independent Test**: Can be fully tested by running the image manipulation script on 5 sample images and verifying output files exist with correct detail modifications, without requiring participants or statistical analysis.

**Acceptance Scenarios**:

1. **Given** 5 baseline images from Visual Genome, **When** researcher runs the manipulation script, **Then** 10 output images are created (2 per baseline: enhanced and reduced detail)
2. **Given** an enhanced-detail image, **When** visual inspection occurs, **Then** 3-5 additional minor objects are present compared to baseline
3. **Given** a reduced-detail image, **When** visual inspection occurs, **Then** minor elements are blurred or removed compared to baseline

---

### User Story 2 - Participant Testing Interface (Priority: P2)

Participant views an image for 10 seconds, completes a 2-minute arithmetic distractor task, then answers 20 questions about scene details (10 false, 10 true).

**Why this priority**: This is the core data collection mechanism. Without valid participant responses, no statistical analysis can occur. However, the interface can be tested independently of the manipulation pipeline.

**Independent Test**: Can be fully tested by simulating a single participant session end-to-end (image display → distractor → questions → response capture) and verifying all 20 responses are recorded correctly.

**Acceptance Scenarios**:

1. **Given** an image is loaded, **When** participant views it, **Then** display duration is [deferred] (±0.5 seconds)
2. **Given** the distractor task begins, **When** participant completes arithmetic questions, **Then** task duration is [deferred] (±10 seconds)
3. **Given** the 20-question test begins, **When** participant answers all questions, **Then** all 20 responses are recorded with timestamps and participant ID

---

### User Story 3 - Statistical Analysis and Results Generation (Priority: P3)

System executes repeated-measures ANOVA comparing false memory rates across detail conditions and generates visualization with confidence intervals.

**Why this priority**: This delivers the research findings but depends on both image manipulation and participant data being collected first. Can be tested independently once sample data exists.

**Independent Test**: Can be fully tested by running the analysis script on synthetic/mock participant data and verifying ANOVA results and visualization are generated within 30 minutes.

**Acceptance Scenarios**:

1. **Given** 60+ participant response records, **When** analysis script executes, **Then** repeated-measures ANOVA results are output with F-statistic, p-value, and effect size
2. **Given** analysis completes, **When** visualization is generated, **Then** plot shows mean false memory rates with 95% confidence intervals for each condition
3. **Given** multiple hypothesis tests are run, **When** correction is applied, **Then** family-wise error rate is controlled (Bonferroni or similar method documented)

---

### Edge Cases

- What happens when Visual Genome image metadata is missing or incomplete? System MUST skip that image and log the error rather than crashing
- How does system handle participant dropout mid-session? System MUST record partial responses and flag incomplete sessions in the dataset
- What happens when image manipulation fails for a specific image? System MUST skip that image, log the failure, and continue with remaining images (minimum 30 images required for analysis)
- How does system handle network timeout during participant testing? System MUST cache responses locally and retry submission with exponential backoff (max 3 attempts, 30-second intervals)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a representative sample of images from Visual Genome dataset with varied baseline complexity scores (See US-1)
- **FR-002**: System MUST create two manipulated versions per image: (a) enhanced detail adding multiple minor objects via compositing, (b) reduced detail blurring/removing minor elements (See US-1)
- **FR-003**: System MUST display each image for [deferred] (±0.5 seconds) before advancing to distractor task (See US-2)
- **FR-004**: System MUST administer a set of questions per session: an equal number of false details (present only in enhanced/reduced versions) and true details (present in baseline) (See US-2)
- **FR-005**: System MUST execute repeated-measures ANOVA comparing false memory rates across detail conditions using scipy.stats (See US-3)
- **FR-006**: System MUST apply multiple-comparison correction when >1 hypothesis test is performed (See US-3)
- **FR-007**: System MUST generate visualization showing mean false memory rates with 95% confidence intervals for each condition (See US-3)

### Key Entities

- **Image**: Visual stimulus with attributes: baseline_complexity_score, enhanced_version_path, reduced_version_path, manipulation_timestamp
- **Participant**: Human subject with attributes: participant_id, completion_timestamp, condition_assigned, total_false_memory_rate
- **Response**: Single answer with attributes: question_id, is_false_detail, participant_id, response_value, response_timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: False memory rate is measured against the baseline image condition to determine effect size of visual detail manipulation (See US-2, US-3)
- **SC-002**: Statistical power is measured against the planned sample size of 60-80 participants with ≥50 per condition to ensure p < 0.05 significance threshold is testable (See US-3)
- **SC-003**: Analysis runtime is measured against the 6-hour GitHub Actions free-tier job limit to ensure CPU-only feasibility (See US-3)
- **SC-004**: Dataset-variable fit is measured against Visual Genome metadata to confirm all required predictors (complexity scores) and outcomes (false memory rates) are available (See US-1)
- **SC-005**: Multiple-comparison correction is measured against the number of hypothesis tests performed to control family-wise error rate (See US-3)

## Assumptions

- Participants have stable internet connectivity during the testing session (minimum 5 Mbps download, 1 Mbps upload)
- Visual Genome dataset contains sufficient scene images with measurable baseline complexity scores for 30-40 image selection
- False memory measurement uses validated question format from existing literature (DRM paradigm adaptations for visual stimuli)
- All statistical analysis runs on CPU-only hardware (no GPU/CUDA dependencies in scipy, matplotlib, or PIL/Pillow)
- Total dataset size (images + participant responses) fits within 7 GB RAM and 14 GB disk constraints
- Participant recruitment via crowdsourcing platform yields a sufficient number of complete sessions within the allocated budget
- Image manipulation via PIL/Pillow compositing is computationally feasible on free-tier CI (no GPU required)
- Observational design frames findings as associational, not causal (no random assignment to detail conditions at individual level)
- Sensitivity analysis for any decision cutoffs (e.g., complexity thresholds) will sweep values over {0.01, 0.05, 0.1} and report false-positive/false-negative rate variation
- Predictor collinearity is diagnosed when multiple visual detail metrics are used (e.g., object count, texture resolution, complexity score) and joint relationships are framed descriptively
