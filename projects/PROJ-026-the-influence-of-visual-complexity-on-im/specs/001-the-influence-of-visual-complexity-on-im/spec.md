# Feature Specification: The Influence of Visual Complexity on Implicit Bias

**Feature Branch**: `001-the-influence-of-visual-complexity-on-im`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does increasing the visual complexity of background stimuli presented during an Implicit Association Test (IAT) reduce implicit bias scores by increasing cognitive load and diverting attention from stereotypical associations?"

## User Scenarios & Testing

### User Story 1 - Stimulus Complexity Quantification (Priority: P1)

As a researcher, I need to compute objective visual complexity metrics (edge density, entropy, fractal dimension) for a set of background images so that I can categorize them into low, medium, and high complexity conditions for the experiment.

**Why this priority**: Without quantified complexity scores, the independent variable (visual complexity) cannot be defined or manipulated. This is the foundational data preparation step required before any statistical analysis can occur.

**Independent Test**: Can be fully tested by running the image processing script on a small, known set of images (e.g., a solid color vs. a noisy texture) and verifying the output scores match expected theoretical ordering (solid color < noise).

**Acceptance Scenarios**:
1. **Given** a set of 50 grayscale images with varying textures, **When** the complexity quantification script is executed, **Then** every image receives a numeric score for edge density, entropy, and fractal dimension.
2. **Given** a solid white image and a high-entropy noise image, **When** scores are computed, **Then** the noise image must have strictly higher scores across all three metrics than the solid image.

---

### User Story 2 - Experimental Data Collection and D-Score Aggregation (Priority: P2)

As a researcher, I need to recruit participants and administer two separate IAT sessions (one with low-complexity backgrounds, one with high-complexity backgrounds) in counterbalanced order, then aggregate the raw response times into valid D-scores per session so that I can analyze the effect of complexity on bias.

**Why this priority**: The core dependent variable (IAT D-score) must be derived from raw response data collected under controlled conditions. This step transforms raw logs into the metric required for the ANOVA and ensures causal validity by separating the complexity manipulation across two distinct sessions.

**Independent Test**: Can be tested by simulating two IAT sessions for a single synthetic participant with known reaction times and verifying the aggregation logic produces two distinct D-scores (one per session) that match expected values within a floating-point tolerance (e.g., < 0.001).

**Acceptance Scenarios**:
1. **Given** a participant who completes two IAT sessions (Session A: Low Complexity, Session B: High Complexity), **When** the aggregation module runs, **Then** it outputs two distinct D-scores for that participant (one per session).
2. **Given** a participant with insufficient valid trials (< 10) in either session, **When** aggregation runs, **Then** that participant's D-score for that specific session is flagged as `NaN` and excluded from the final analysis dataset.
3. **Given** the counterbalanced order requirement, **When** the data collection script runs, **Then** it assigns [deferred] of participants to start with Low Complexity and [deferred] to start with High Complexity.

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

As a researcher, I need to perform a repeated-measures ANOVA on the aggregated D-scores across complexity levels and generate a visualization of the effect size and confidence intervals, including a sensitivity analysis of the complexity thresholds, so that I can determine if visual complexity significantly reduces implicit bias.

**Why this priority**: This delivers the final research answer. It is the culmination of the data preparation and analysis pipeline. The inclusion of sensitivity analysis ensures the robustness of the findings against arbitrary threshold choices.

**Independent Test**: Can be tested by running the analysis script on a pre-generated dataset with a known, pre-calculated ANOVA result (p-value, F-statistic) and verifying the script outputs match within numerical precision.

**Acceptance Scenarios**:
1. **Given** a dataset of 60 participants with two D-scores each (Low vs. High complexity), **When** the analysis script runs, **Then** it outputs a p-value, F-statistic, and partial η² for the main effect of visual complexity.
2. **Given** the analysis results, **When** the visualization module runs, **Then** it generates a plot (e.g., boxplot or bar chart with error bars) showing the mean D-score for each complexity condition with 95% confidence intervals.
3. **Given** a set of complexity thresholds derived from the median split, **When** the sensitivity analysis runs, **Then** it reports the p-value variation across thresholds shifted by ±0.05, ±0.10, and ±0.15 standard deviations of the complexity metric, excluding any sweep point where the participant count drops below 15 per condition.

### Edge Cases

- **What happens when** the computed fractal dimension for an image exceeds the valid range for the box-counting algorithm? The system must clamp the value or flag the image for manual review rather than crashing.
- **How does the system handle** participants with missing data for one of the two IAT sessions? The analysis must exclude these participants from the repeated-measures comparison to avoid biased estimates, logging the count of excluded participants.
- **What happens when** the dataset contains images that are not valid images (corrupted files)? The script must skip these files, log the filename, and continue processing without failing the entire batch.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute three specific visual complexity metrics (edge density via Canny edge detection, entropy of grayscale histograms, and fractal dimension via box-counting) for every input image. (See US-1)
- **FR-002**: System MUST aggregate raw IAT response times into D-scores using the Greenwald et al. (2003) D2 algorithm, removing trials with latency < 300ms or > 10,000ms, and handling error trials according to the standard protocol. (See US-2)
- **FR-003**: System MUST perform a repeated-measures ANOVA to test the hypothesis that D-scores differ significantly between low and high visual complexity conditions, based on data from two separate IAT administrations per participant. (See US-3)
- **FR-004**: System MUST calculate and report effect sizes (Cohen's d and partial η²) alongside the ANOVA p-value. (See US-3)
- **FR-005**: System MUST generate a publication-quality plot visualizing the mean D-scores and 95% confidence intervals for each complexity condition. (See US-3)
- **FR-006**: System MUST detect and exclude participants who have an insufficient number of valid trials in any session from the final statistical analysis. (See US-2)
- **FR-007**: System MUST perform a sensitivity analysis sweeping the complexity threshold cutoff by ±0.05, ±0.10, and ±0.15 standard deviations of the observed complexity metric distribution; if a threshold shift results in fewer than 15 valid participants per condition, that sweep point is marked as 'invalid' and excluded from the robustness conclusion. (See US-3)

### Key Entities

- **Image Stimulus**: Represents a background image used in the IAT, characterized by file path and computed complexity metrics (edge density, entropy, fractal dimension).
- **Participant Response**: Represents a single trial from an IAT, characterized by reaction time, correctness, session ID (Low/High Complexity), and assigned condition label determined during data collection.
- **Aggregated Score**: Represents a participant's summary D-score for a specific complexity session, derived from multiple raw response trials.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The mean D-score in the high-complexity condition is measured against the mean D-score in the low-complexity condition to determine the direction and magnitude of the effect (See US-3).
- **SC-002**: The statistical significance (p-value) of the visual complexity effect is measured against the alpha level of 0.05 to determine if the null hypothesis is rejected (See US-3).
- **SC-003**: The robustness of the findings is measured by the variation in the headline p-value across the sensitivity analysis sweep of complexity thresholds (See US-3).
- **SC-004**: The power of the study is measured against the target of 0.80 for a medium effect size (η² > 0.02) with N=60, verified via post-hoc calculation (See US-3).
- **SC-005**: The computational feasibility is measured against the constraint of completing the entire analysis pipeline (data load, metric computation, ANOVA, plotting) within 6 hours on a CPU-only runner with ≤7 GB RAM (See Assumptions).

## Assumptions

- **Assumption about data source**: The project assumes that new data will be collected from recruited participants who complete two separate IAT sessions (one with low-complexity backgrounds, one with high-complexity backgrounds) to ensure causal validity and controlled manipulation of the independent variable.
- **Assumption about compute resources**: The project assumes that the selected images (sampled from a larger set if necessary) and the resulting dataframes will fit within the RAM limit of the GitHub Actions free-tier runner., requiring no GPU acceleration.
- **Assumption about measurement validity**: The project assumes that the standard D-score algorithm (Greenwald et al.) is a valid and citable measure of implicit bias for the purpose of this analysis.
- **Assumption about threshold justification**: The project assumes that a median split (or similar standard cutoff) of the computed complexity scores is sufficient to define "low" and "high" conditions, and that the required sensitivity analysis will confirm this choice does not alter the primary conclusion.