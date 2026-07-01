# Feature Specification: The Influence of Narrative Framing on Attitudes Towards AI Assistance

**Feature Branch**: `001-narrative-framing-ai-attitudes`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does framing large‑language‑model assistance as a 'collaborative partner' versus an 'automated tool' lead to more positive attitudes, higher perceived usefulness, and greater trust among lay users?"

## User Scenarios & Testing

### User Story 1 - Stimulus Generation and Randomization (Priority: P1)

The system MUST generate two distinct vignette texts (Partner vs. Tool) based on a controlled template and assign participants to exactly one condition via a randomized script.

**Why this priority**: This is the core experimental manipulation. Without valid, distinct stimuli and proper randomization, the research question cannot be tested.

**Independent Test**: The system can be tested by running the stimulus generation script to output two CSV files (one per condition) and verifying via a unit test that the randomization script assigns unique user IDs to conditions with a 50/50 split distribution (within statistical tolerance) over 10,000 simulated runs.

**Acceptance Scenarios**:

1. **Given** the base task description (e.g., "drafting an email") and the framing parameter, **When** the stimulus generator runs, **Then** it outputs a vignette where the AI is explicitly referred to as a "collaborative partner" or "automated tool" respectively, with no other variable changes.
2. **Given** a new participant ID, **When** the survey randomization script executes, **Then** the participant is assigned to exactly one of the two conditions, and the assignment is recorded in the metadata before any survey questions are displayed.
3. **Given** the generated vignettes, **When** a readability check (Flesch-Kincaid) is performed, **Then** the difference in readability scores between the two vignettes is ≤ 2.0 points, ensuring comparable difficulty.

---

### User Story 2 - Data Collection and Validation (Priority: P2)

The system MUST collect survey responses for attitude, perceived usefulness, trust, and manipulation checks, exporting them as a structured CSV with quality flags.

**Why this priority**: Data integrity is critical for statistical analysis. This story ensures the raw data is usable and that participants actually read the stimuli (manipulation check).

**Independent Test**: The system can be tested by submitting synthetic survey data for 100 participants (50 per condition) and verifying that the export process produces a CSV where all required columns exist, missing values are flagged, and the manipulation check correctly identifies participants who failed to recognize the framing.

**Acceptance Scenarios**:

1. **Given** a participant has completed the survey, **When** the data is exported, **Then** the record includes the framing condition, the 7-item attitude scale, the 3-item usefulness scale, the 4-item trust scale, and the manipulation check response.
2. **Given** a participant fails the manipulation check (e.g., identifies the wrong framing), **When** the data is processed, **Then** the record is flagged with a `manipulation_check_failed` boolean set to `true`.
3. **Given** the raw data file, **When** the validation script runs, **Then** it confirms that no participant has duplicate entries and that all Likert scale responses are integers between 1 and 7.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST perform independent-samples t-tests (or Welch's correction) and non-parametric Mann-Whitney U tests to compare conditions, calculating effect sizes (Cohen's d) and 95% confidence intervals.

**Why this priority**: This transforms raw data into the answer for the research question. It must handle the specific statistical requirements (multiple comparisons, effect sizes) defined in the methodology.

**Independent Test**: The system can be tested by feeding it a synthetic dataset with a known effect size (e.g., d = 0.5) and verifying that the analysis script correctly identifies a significant difference (p < 0.05) and reports an effect size within 10% of the input value.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset, **When** the analysis script runs, **Then** it outputs a report containing p-values, t-statistics, and Cohen's d for the three dependent variables (attitude, usefulness, trust).
2. **Given** the set of three hypothesis tests, **When** the multiple-comparison correction is applied, **Then** the adjusted p-values are calculated using the Benjamini-Hochberg procedure (or similar) to control the false discovery rate.
3. **Given** the primary results, **When** the robustness check runs, **Then** it performs a Mann-Whitney U test and a linear regression controlling for age and gender, confirming the primary findings hold under these alternative models.

### Edge Cases

- What happens when a participant abandons the survey halfway through? (System must exclude partial responses from the final analysis).
- How does the system handle participants who fail the manipulation check? (They are flagged and excluded from the primary analysis, but included in a sensitivity analysis).
- What if the sample size is significantly smaller than the target N=300 due to recruitment issues? (The system must still run the analysis but flag the statistical power as insufficient in the final report).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate two vignette variants where the only linguistic difference is the framing of the AI as a "collaborative partner" versus an "automated tool" (See US-1).
- **FR-002**: The system MUST randomize participant assignment to one of the two framing conditions with a target 1:1 ratio (See US-1).
- **FR-003**: The system MUST collect and store responses for three specific scales: 7-item Attitude, 3-item Perceived Usefulness, and 4-item Trust (See US-2).
- **FR-004**: The system MUST perform an independent-samples t-test (or Welch's t-test if variances are unequal) for each dependent variable comparing the two framing conditions (See US-3).
- **FR-005**: The system MUST calculate Cohen's d effect sizes and 95% confidence intervals for all primary comparisons (See US-3).
- **FR-006**: The system MUST apply a multiple-comparison correction (e.g., Benjamini-Hochberg) to the family of three hypothesis tests to control the false discovery rate (See US-3).
- **FR-007**: The system MUST perform a sensitivity analysis by re-running the primary t-tests excluding participants who failed the manipulation check (See US-3).
- **FR-008**: The system MUST execute all statistical computations using only CPU-based libraries (e.g., `scipy`, `statsmodels`, `pandas`) without requiring GPU acceleration (See US-3).

### Key Entities

- **Participant**: A unique identifier for a survey respondent, linked to a specific framing condition and a set of survey responses.
- **Vignette**: The stimulus text presented to the participant, characterized by its framing type (Partner/Tool) and readability score.
- **Response Set**: A collection of Likert-scale scores associated with a Participant, including the manipulation check result.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The readability difference between the two vignette variants is measured against the Flesch-Kincaid Grade Level, requiring a difference of ≤ 2.0 points (See FR-001).
- **SC-002**: The statistical power of the analysis is measured against the target sample size of N=300, requiring a minimum of 80% power to detect an effect size of d=0.4 at α=0.05 (See FR-004).
- **SC-003**: The false discovery rate is measured against the family-wise error rate, requiring the application of a correction method that keeps the FDR ≤ 0.05 across the three primary tests (See FR-006).
- **SC-004**: The effect size estimates (Cohen's d) are measured against the 95% confidence intervals, requiring that the intervals do not cross zero if the result is declared statistically significant (See FR-005).
- **SC-005**: The analysis runtime is measured against the free-tier CPU limit (6 hours), requiring the entire statistical pipeline to complete in ≤ 30 minutes on a standard 2-core runner (See FR-008).

## Assumptions

- The "Sentiment140" dataset is available via the public GitHub repository URL provided in the idea markdown to compute baseline sentiment scores, and the repository remains accessible throughout the analysis period.
- The participant recruitment platform (Prolific or MTurk) allows for the export of raw CSV data via an API or manual download without requiring additional paid tiers.
- The survey platform (Qualtrics free tier or Google Forms) supports the embedding of a JavaScript randomization script that persists the condition assignment in the final export.
- The statistical power calculation assumes a two-tailed test with α=0.05 and an expected effect size (Cohen's d) between 0.4 and 0.6 based on prior literature.
- The analysis environment has access to `python`, `pandas`, `scipy`, and `statsmodels` packages pre-installed or installable within the 6-hour GitHub Actions job limit.
- The manipulation check question ("The AI was described as a...") has sufficient discriminative validity to identify participants who did not read the vignette carefully.
- The "collaborative partner" and "automated tool" framings do not inadvertently introduce significant differences in sentiment valence (positive/negative tone) other than the intended framing effect.
