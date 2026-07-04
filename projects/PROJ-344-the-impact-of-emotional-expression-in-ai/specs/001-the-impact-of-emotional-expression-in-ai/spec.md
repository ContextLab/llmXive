# Feature Specification: The Impact of Emotional Expression in AI Avatars on User Trust

**Feature Branch**: `001-emotional-synchrony-trust`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "How does the synchrony between vocal tone and facial emotional expression in AI avatars influence users' trust in the avatar's advice?"

## User Scenarios & Testing

### User Story 1 - Core Intra-Modal Consistency Extraction and Correlation (Priority: P1)

The researcher must be able to download or generate a human-AI interaction dataset containing video/audio and trust scores, extract facial and vocal features using CPU-compatible models, compute an intra-modal consistency metric via cross-correlation, and calculate the Spearman rank correlation between consistency and trust.

**Why this priority**: This is the primary research objective. Without establishing the core correlation, the study cannot answer the research question. It forms the Minimum Viable Product (MVP) of the research pipeline.

**Independent Test**: Can be fully tested by running the extraction and correlation script on a small sample of the dataset and verifying the output includes a correlation coefficient with a 95% confidence interval.

**Acceptance Scenarios**:

1. **Given** a valid dataset file with video, audio, and trust metadata, **When** the extraction script runs, **Then** it outputs a CSV containing interaction IDs, computed consistency scores, and trust scores.
2. **Given** the generated CSV, **When** the correlation analysis runs, **Then** it outputs a Spearman correlation coefficient and a 95% confidence interval.
3. **Given** the analysis results, **When** the researcher reviews them, **Then** the results are framed as associational (not causal) due to the observational nature of the data.

---

### User Story 2 - Robustness Check with Control Variables (Priority: P2)

The researcher must be able to run an ordinal regression analysis that includes control variables (avatar type, interaction duration, task difficulty) to verify if the consistency-trust relationship holds when accounting for confounding factors.

**Why this priority**: This validates the robustness of the primary finding. While the core correlation answers the main question, controlling for confounders strengthens the validity of the conclusion and addresses potential alternative explanations.

**Independent Test**: Can be fully tested by running the regression script on the same dataset and verifying the output includes regression coefficients, p-values, and model fit statistics (pseudo R-squared).

**Acceptance Scenarios**:

1. **Given** the extracted feature CSV and metadata containing control variables, **When** the regression script runs, **Then** it outputs a regression table with coefficients for consistency and all control variables.
2. **Given** the regression results, **When** the researcher reviews them, **Then** the p-value for the consistency coefficient is reported alongside the confidence interval.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The researcher must be able to generate a scatter plot with a regression line and 95% confidence intervals, visualizing the relationship between consistency and trust, and export this figure for inclusion in a report.

**Why this priority**: Visualization is essential for interpreting and communicating the results. While the statistical analysis provides the numbers, the plot provides the intuitive understanding required for publication and design guidelines.

**Independent Test**: Can be fully tested by running the plotting script and verifying the output is a valid image file (e.g., PNG) showing the scatter plot with the regression line and confidence bands.

**Acceptance Scenarios**:

1. **Given** the correlation analysis results, **When** the plotting script runs, **Then** it generates a scatter plot with consistency on the x-axis, trust on the y-axis, and a regression line with 95% CI.
2. **Given** the generated plot, **When** the file is opened, **Then** it is clearly labeled with axis titles, a legend, and a title indicating the correlation coefficient.

### Edge Cases

- What happens when the dataset contains video or audio files that are corrupted or unreadable? (System logs the error and skips the file, continuing with valid data).
- How does the system handle interactions where the facial expression or vocal prosody time-series are too short for cross-correlation? (System flags these interactions as "insufficient data" and excludes them from the correlation calculation).
- What happens if the trust scores are missing for a specific interaction? (System excludes the interaction from the analysis).

## Requirements

### Functional Requirements

- **FR-001**: System MUST validate the selected dataset against a schema requiring synchronized video/audio tracks of the avatar, corresponding user trust scores, and metadata fields for 'avatar type', 'interaction duration', and 'task difficulty'. If a candidate dataset lacks these, the system MUST reject it and query the next candidate in the registry. If no valid dataset is found in the registry, the system MUST initiate a fallback protocol to generate simulated data or trigger a controlled data collection study. (See US-1)
- **FR-002**: System MUST compute facial expression intensity time-series using OpenFace from video frames. (See US-1)
- **FR-003**: System MUST extract vocal prosody features (pitch, energy, tempo) using librosa from audio tracks. (See US-1)
- **FR-004**: System MUST calculate an intra-modal consistency metric defined as the maximum absolute value of the cross-correlation between facial expression and vocal prosody time-series within a lag window of ±2 seconds, normalized by the product of their standard deviations. (See US-1)
- **FR-005**: System MUST perform a Spearman rank correlation test between the computed consistency scores and user trust scores, reporting the coefficient and a confidence interval. (See US-1)
- **FR-006**: System MUST execute an ordinal regression (proportional odds model) with control variables (avatar type, interaction duration, task difficulty) to assess the robustness of the consistency-trust relationship. (See US-2)
- **FR-007**: System MUST generate a scatter plot visualizing the consistency-trust relationship with a regression line and confidence intervals. (See US-3)

### Key Entities

- **Interaction**: A single session between a user and an AI avatar, characterized by video, audio, and a trust score.
- **Consistency Score**: A numerical value representing the intra-modal cross-correlation between the avatar's facial and vocal emotional signals for an interaction.
- **Trust Score**: A numerical value (Likert scale) representing the user's trust in the avatar's advice.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between consistency and trust is measured against the null hypothesis of no association (r=0) to determine statistical significance. (See US-1)
- **SC-002**: The robustness of the consistency-trust relationship is measured against the model fit (pseudo R-squared) and p-values of control variables in the ordinal regression analysis. (See US-2)
- **SC-003**: The visualization quality is measured against WCAG 2.1 AA contrast ratios (≥4.5:1) for text elements and a minimum axis-label font size of a readable magnitude. (See US-3)
- **SC-004**: The methodological validity is measured against the requirement to frame findings as associational (not causal) in all outputs, given the observational nature of the data. (See US-1)
- **SC-005**: The computational feasibility is measured against the constraint that the entire analysis must complete within 6 hours on a free-tier GitHub Actions runner (limited CPU, ~7 GB RAM) without GPU acceleration, processing a dataset of N=500 interactions. (See Assumptions)

## Assumptions

- The research focuses on **intra-modal consistency** (the alignment between an avatar's face and voice) as a predictor of trust, rather than interpersonal synchrony (avatar-user alignment).
- Pre-trained CPU-compatible models (specifically OpenFace.0) are sufficient for extracting facial and vocal features with acceptable accuracy for correlation analysis.
- The cross-correlation method with a ±2 second lag window is an appropriate metric for quantifying intra-modal consistency in this context, and the time-series data are sufficiently aligned in time.
- If no pre-existing dataset containing the required modalities and metadata fields is available in the public registry, the fallback data generation or collection protocol (triggered by FR-001) will provide sufficient data (N≥500) to achieve a statistical power of ≥0.8 for detecting a moderate effect size (r=0.3).
- The analysis will be conducted entirely on CPU resources, adhering to the free-tier GitHub Actions constraints (no GPU, ≤6h runtime).
- The trust scores are on a valid Likert scale (e.g., 1-5 or 1-7) and are suitable for ordinal regression analysis.