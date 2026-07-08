# Feature Specification: The Impact of Linguistic Complexity on Trust in AI-Generated Text

**Feature Branch**: `001-linguistic-complexity-trust`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does linguistic complexity in AI-generated text (e.g., sentence structure, lexical diversity) predict readers' trust ratings when the source is explicitly identified as AI-generated?"

## User Scenarios & Testing

### User Story 1 - Data Generation and Metric Computation (Priority: P1)

**As a** researcher, **I want** to generate AI text samples with controlled linguistic complexity and compute objective metrics (Flesch-Kincaid, MTLD, sentence length) so that I have a validated dataset linking text properties to complexity scores.

**Why this priority**: This is the foundational data layer. Without a dataset where complexity is quantified and text is generated, no trust analysis can occur. It is the prerequisite for all downstream analysis.

**Independent Test**: Can be fully tested by running the generation script on a local sample of Wikipedia articles, verifying that the output CSV contains valid text, computed complexity scores, and that the scores vary across the generated samples.

**Acceptance Scenarios**:

1. **Given** a source corpus (e.g., Wikipedia subset), **When** the generation script runs with Gemma-2B and prompt variations, **Then** a CSV file is produced containing at least 200 text samples with computed Flesch-Kincaid, MTLD, and average sentence length values.
2. **Given** the generated CSV, **When** a script calculates the range of Flesch-Kincaid scores, **Then** the range spans from a lower bound to an upper threshold to ensure sufficient variance for regression analysis.

---

### User Story 2 - Participant Trust Rating Collection (Priority: P2)

**As a** researcher, **I want** to recruit human participants via Prolific to read AI-labeled text samples and provide Likert trust ratings so that I can correlate subjective trust with objective complexity metrics.

**Why this priority**: This captures the dependent variable (trust). While the data generation (P1) creates the stimuli, this story captures the human response required to answer the research question.

**Independent Test**: Can be fully tested by simulating the survey interface with 10 dummy participants (or a small pilot) and verifying that the resulting dataset links participant IDs, text IDs, and trust scores (1-5) without data loss.

**Acceptance Scenarios**:

1. **Given** a set of text samples labeled as "AI-Generated", **When** a participant completes the survey, **Then** the system records a trust rating for each text sample presented.
2. **Given** a participant who fails an attention check (e.g., "Select 'Strongly Disagree' for this item"), **When** the data is processed, **Then** that participant's entire response set is flagged for exclusion.

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**As a** researcher, **I want** to run a linear regression with quadratic terms to test for non-linear (inverted-U) relationships between complexity and trust, and visualize the results, so that I can validate the hypothesis that moderate complexity maximizes trust.

**Why this priority**: This delivers the final research output. It synthesizes the data from P1 and P2 to answer the core research question.

**Independent Test**: Can be fully tested by running the analysis script on a mock dataset where the relationship is known (e.g., a synthetic dataset with a perfect inverted-U curve) and verifying that the regression coefficient for the quadratic term is significant and negative.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset of trust ratings and complexity metrics, **When** the regression model is executed, **Then** the output includes a p-value for the quadratic term (complexity²) indicating significance (p < 0.05) or non-significance.
2. **Given** the regression results, **When** the visualization script runs, **Then** a plot is generated showing the fitted curve of Trust vs. Complexity with 95% confidence intervals.

### Edge Cases

- What happens if the generated text samples do not show enough variance in complexity (e.g., all scores are within a narrow band)?
- How does the system handle participants who provide identical trust ratings (1, 1, 1...) for all items (straight-lining)?
- What happens if the Prolific API returns an error during recruitment or if the target N=100 is not reached within the budget?

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate AI text samples from a source corpus using a local LLM (Gemma-2B) with prompt variations to ensure a wide distribution of linguistic complexity metrics (See US-1).
- **FR-002**: System MUST compute Flesch-Kincaid readability, MTLD (lexical diversity), and average sentence length for every generated text sample and store these in a structured dataset (See US-1).
- **FR-003**: System MUST present text samples labeled explicitly as "AI-Generated" to participants and collect 5-point Likert trust ratings for each sample (See US-2).
- **FR-004**: System MUST implement attention checks to filter out low-quality participant responses and exclude them from the final analysis dataset (See US-2).
- **FR-005**: System MUST perform separate univariate linear regression analyses (one per complexity metric) including a quadratic term (complexity²) to test for non-linear relationships, and generate a visualization of the fitted curve with confidence intervals for each metric (See US-3).
- **FR-006**: System MUST apply Bonferroni correction when the number of univariate models tested is greater than 1, and the output log MUST explicitly state the correction method used and the adjusted alpha threshold (e.g., alpha = 0.05 / k) (See US-3).
- **FR-007**: System MUST perform a post-hoc power analysis to calculate the minimum detectable effect size for the quadratic term given the final sample size (N ≥ 100) and report this value to justify the study's sensitivity (See US-3).
- **FR-008**: System MUST validate the interval-scale assumption of the Likert data by running a robust ordinal logistic regression as a sensitivity check and comparing the qualitative conclusions (sign and significance of the quadratic term) against the linear model results (See US-3).

### Key Entities

- **TextSample**: Represents a unique text instance, containing the raw text content, source ID, and computed complexity metrics (FK, MTLD, SentenceLength).
- **ParticipantResponse**: Represents a single user's interaction, containing the ParticipantID, TextSampleID, TrustRating (1-5), and AttentionCheckStatus.
- **AnalysisResult**: Represents the output of the statistical model, containing coefficients, p-values, R-squared, and the plot artifact.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The distribution of Flesch-Kincaid scores in the generated dataset is measured against a target range of 5.0 to 12.0 to ensure sufficient variance for regression analysis (See FR-001, US-1).
- **SC-002**: The final dataset size is measured against the target of N ≥ 100 valid participant responses after attention check filtering (See FR-004, US-2).
- **SC-003**: The regression model's quadratic term significance is measured against the p < 0.05 threshold to confirm or reject the non-linear hypothesis (See FR-005, US-3).
- **SC-004**: The regression model must converge and produce valid coefficients (no NaN/Inf) for at least one complexity metric to be considered a successful analysis run (See FR-005, US-3).
- **SC-005**: The sensitivity of the results is measured by re-running the regression with an alternative metric (average sentence length instead of MTLD) and verifying that the sign and significance (p < 0.05) of the quadratic term remain consistent across both metrics (See FR-006, US-3).
- **SC-006**: The study's sensitivity is validated if the post-hoc power analysis confirms a minimum detectable effect size (for the quadratic term) of f² ≤ 0.15 at power ≥ 0.80, given the final sample size (See FR-007, US-3).
- **SC-007**: The validity of the linear model is confirmed if the ordinal logistic regression sensitivity check (FR-008) yields a consistent qualitative conclusion regarding the direction and significance of the quadratic effect (See FR-008, US-3).

## Assumptions

- **Assumption about data source**: The Wikipedia corpus on HuggingFace contains sufficient textual variety to generate samples spanning low, medium, and high linguistic complexity when processed by Gemma-2B.
- **Assumption about participant behavior**: Participants recruited via Prolific will read the text carefully and provide honest trust ratings rather than random responses, provided attention checks are in place.
- **Assumption about methodological framing**: Since this is an observational study of human ratings, the analysis will strictly frame results as associational correlations between complexity and trust, avoiding causal claims about complexity *causing* trust changes.
- **Assumption about threshold justification**: The 5-point Likert scale is treated as an interval scale for the purpose of linear regression, consistent with standard practice in psychometrics for this type of survey data, subject to validation via FR-008.