# Feature Specification: Simulation-Based Sensitivity Analysis of Framing Effects on Perceived Severity of Online Misinformation

**Feature Branch**: `001-the-impact-of-framing`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does framing misinformation as harmful to society versus as factually inaccurate affect individuals' perceived severity and sharing intentions toward online content?"

## User Scenarios & Testing

### User Story 1 - Primary Analysis: Simulation of Framing Effect on Severity Perception (Priority: P1)

The system must execute a simulation-based sensitivity analysis comparing "harm-framed" versus "fact-framed" misinformation to determine the *potential* impact of harm framing on perceived severity ratings. This is a hypothetical experiment using the MPSD-v2 dataset to generate synthetic response data, modeling the effect of framing as an experimental manipulation.

**Why this priority**: This directly addresses the central research gap: whether emphasizing societal harm is more effective than stating factual falsity. The simulation allows for a controlled test of the causal hypothesis without requiring new data collection, serving as the minimum viable product for the study's methodological framework.

**Independent Test**: Can be fully tested by running the mixed-effects linear model on the generated synthetic dataset and verifying the coefficient for the `framing_condition` variable is correctly calculated and reported, regardless of its statistical significance.

**Acceptance Scenarios**:

1. **Given** a generated synthetic dataset of 300 responses with severity ratings (1-7) and framing conditions, **When** the mixed-effects model is fitted with severity as the outcome and framing as the fixed effect, **Then** the model outputs a coefficient for "harm" framing and its p-value.
2. **Given** the generated dataset, **When** the analysis is run with Bonferroni correction applied for the number of primary hypothesis tests (1), **Then** the adjusted p-value is correctly calculated and reported.
3. **Given** the model results, **When** the effect size (Cohen's d) is calculated, **Then** the value is reported.

---

### User Story 2 - Secondary Analysis: Simulation of Framing Effect on Sharing Intentions (Priority: P2)

The system must analyze the relationship between simulated framing conditions and binary sharing intentions, controlling for content domain (health, politics, science), to determine if framing influences behavioral intent in the synthetic model.

**Why this priority**: While severity perception is the primary mechanism, the ultimate goal is reducing misinformation spread. This story validates whether the framing effect translates to behavioral outcomes in the simulation, making it a critical secondary contribution.

**Independent Test**: Can be fully tested by running a logistic regression model predicting `sharing_intention` from `framing_condition` and `content_domain`, and verifying the odds ratio and p-value are correctly calculated.

**Acceptance Scenarios**:

1. **Given** the generated dataset with binary sharing intention flags, **When** a logistic regression is fitted with `sharing_intention` as the outcome and `framing_condition` as a predictor, **Then** the model outputs an odds ratio for "harm" framing and its p-value.
2. **Given** the regression results, **When** the interaction between framing and content domain is tested, **Then** the model reports the interaction coefficient and p-value.

---

### User Story 3 - A Priori Power Analysis (Priority: P3)

The system must perform an *a priori* power analysis to justify that the planned sample size (N=300) is sufficient to detect a small-to-medium effect size (d=0.3) with ≥80% power before data generation.

**Why this priority**: This ensures the study's statistical validity and defensibility. It confirms that the planned sample size is adequate to detect the hypothesized effect, ensuring the simulation is not underpowered by design.

**Independent Test**: Can be fully tested by running the `pwr` package calculation using the target effect size (d=0.3) and sample size (N=300), and verifying the calculated power meets or exceeds 80%.

**Acceptance Scenarios**:

1. **Given** the target effect size d=0.3 and sample size N=300, **When** the a priori power analysis is executed, **Then** the output reports a statistical power ≥ 0.80.
2. **Given** a scenario where the target effect size is smaller (e.g., d=0.2), **When** the power analysis is run, **Then** the system reports the calculated power and flags if it falls below 0.80.

### Edge Cases

- What happens if the downloaded MPSD-v2 dataset is corrupted or missing specific columns (e.g., `stimulus_id`, `content_domain`, or `headline`)?
- How does the system handle a scenario where the mixed-effects model fails to converge due to a singular fit (e.g., if a specific stimulus has no variance in the generated synthetic data)?
- How does the system handle a scenario where the calculated power is < 0.80? (The system must report this and not proceed with the main analysis without a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the MPSD-v2 dataset from the specified OSF URL, validating that all required *stimulus* columns (`stimulus_id`, `content_domain`, `headline`) are present. The system MUST NOT require a `framing_condition` column in the source data, as this variable is generated synthetically (See US-1).
- **FR-002**: System MUST generate a synthetic dataset by: (1) Sampling N_stimuli unique stimuli from the source dataset (default N_stimuli=20); (2) For each sampled stimulus, generating 15 synthetic "harm" responses and 15 synthetic "fact" responses (Total N=600, or N=300 if sampling 10 stimuli) such that `framing_condition` is explicitly assigned as an experimental variable, and `severity_rating` and `sharing_intention` are generated based on a parametric model with a predefined effect size (See US-1).
- **FR-003**: System MUST fit a mixed-effects linear model using `lme4` in R, with `severity_rating` as the outcome, `framing_condition` as a fixed effect, and `stimulus_id` as a random intercept (See US-1).
- **FR-004**: System MUST apply Bonferroni correction to p-values derived from the analysis. The correction factor MUST be equal to the number of primary hypothesis tests performed (one for the main framing effect, or three if testing framing x content_domain interactions). (See US-1).
- **FR-005**: System MUST fit a logistic regression model predicting `sharing_intention` from `framing_condition` while controlling for `content_domain` (See US-2).
- **FR-006**: System MUST calculate Cohen's d effect size for the difference in mean severity ratings between the two framing conditions (See US-1).
- **FR-007**: System MUST perform an *a priori* power analysis using the `pwr` package to verify that the planned sample size (N=300) achieves ≥80% power for detecting an effect size of d=0.3 (See US-3).
- **FR-008**: System MUST generate summary visualizations including a bar plot with 95% confidence intervals for severity ratings by framing condition (See US-1).
- **FR-009**: System MUST export the final results table and visualizations to the `results.md` file in the project root (See US-1).

### Key Entities

- **Stimulus**: A piece of misinformation content (headline) characterized by its `stimulus_id` and `content_domain` (health, politics, science).
- **Response**: A synthetic participant's reaction to a stimulus, containing `severity_rating` (1-7 Likert), `sharing_intention` (binary), and the assigned `framing_condition`.
- **Participant**: A simulated entity identified by `participant_id`, contributing multiple responses across different stimuli.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The primary analysis (mixed-effects model) MUST correctly calculate and report the Bonferroni-adjusted p-value for the `framing_condition` coefficient (See US-1).
- **SC-002**: The system MUST correctly calculate and report Cohen's d effect size for severity ratings (See US-1).
- **SC-003**: The logistic regression MUST correctly calculate and report the odds ratio and p-value for the effect of "harm" framing on sharing intentions (See US-2).
- **SC-004**: The *a priori* power analysis MUST correctly calculate and report the power value for the planned sample size and target effect size (See US-3).
- **SC-005**: The total runtime of the analysis pipeline MUST be ≤ 6 hours on a GitHub Actions free-tier runner (2 CPU, 7GB RAM), measured against the CI job time limit (See Assumption 4).

## Assumptions

- **Simulation Methodology**: This study is a *simulation-based sensitivity analysis*. The MPSD-v2 dataset is used solely as a source of realistic stimulus parameters (headlines, domains). The `framing_condition` is an experimental manipulation generated by the system, not a property of the source data. The system generates *new* synthetic response data for each stimulus under both framing conditions to simulate a hypothetical between-subjects experiment.
- **Causal Inference**: Since this is a simulation of a hypothetical experiment with random assignment of framing labels, the analysis models the *potential* causal effect of framing. It does not claim to measure the effect in the real world without empirical validation.
- **Compute feasibility**: The analysis (mixed-effects models, logistic regression, power analysis) is computationally lightweight and will complete within the 6-hour limit on a CPU-only GitHub Actions runner with 7GB RAM, provided the synthetic dataset is limited to N=300.
- **Threshold justification**: The alpha level for significance is fixed at a conventional threshold. The effect size threshold of d > 0.3 is based on standard conventions for small-to-medium effects in social psychology.
- **Measurement validity**: The `severity_rating` (1-7 Likert) and `sharing_intention` (binary) metrics in the MPSD-v2 dataset are treated as validated instruments for perceived severity and behavioral intent, and their parametric properties are assumed for the synthetic data generation.
- **Predictor collinearity**: The `framing_condition` is an independent experimental manipulation, and `content_domain` is a categorical control variable; no collinearity diagnostics are required as these are not definitionally related predictors.
- **Stimulus Count**: The number of unique stimuli sampled (N_stimuli) is a configurable parameter, defaulting to a representative magnitude sufficient for initial evaluation. The Bonferroni correction is applied to the number of hypothesis tests, not the number of stimuli.