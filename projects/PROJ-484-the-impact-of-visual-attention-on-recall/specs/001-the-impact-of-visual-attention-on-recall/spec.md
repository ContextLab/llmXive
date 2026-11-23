# Feature Specification: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Feature Branch**: `001-visual-attention-recall`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "How does trait anxiety modulate the relationship between gaze fixation duration on threat stimuli and subsequent recall accuracy in rapid serial visual presentation?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download the raw RSVP dataset (OpenNeuro dsXXXXXX or equivalent), extract gaze fixation metrics using a velocity-threshold algorithm, and map stimulus IDs to emotional valence labels (threat/neutral) to generate a clean analysis-ready CSV file.

**Why this priority**: Without valid, cleaned data linking fixation duration, stimulus valence, and participant ID, no statistical modeling is possible. This is the foundational step for the entire research pipeline.

**Independent Test**: This can be fully tested by running the preprocessing script on a small sample subset (e.g., 5 participants) and verifying that the output CSV contains non-null fixation durations, valid valence labels, and matches the expected schema without crashing or exceeding memory limits.

**Acceptance Scenarios**:

1. **Given** the raw dataset is downloaded via `wget`, **When** the preprocessing script executes the velocity-threshold algorithm on the gaze data, **Then** the output CSV must contain a `fixation_duration_ms` column with ≥ 95% non-null values for valid trials.
2. **Given** the stimulus ID mapping file, **When** the script joins stimulus IDs to the IAPS/NimStim database, **Then** every row in the output CSV must have a valid `valence` label (categorical: threat, neutral) with no unmapped IDs.
3. **Given** the STAI inventory data, **When** the script merges participant scores, **Then** the output CSV must include a `trait_anxiety_score` column with integer values consistent with the STAI range.

---

### User Story 2 - Mixed-Effects Model Execution and Interaction Testing (Priority: P2)

The researcher MUST be able to fit a mixed-effects logistic regression model (`recall ~ fixation_duration * valence * trait_anxiety`) on the CPU-only environment and perform a likelihood-ratio test to determine if the three-way interaction term significantly improves model fit.

**Why this priority**: This directly addresses the core research question regarding the modulation of the attention-memory link by anxiety. It is the primary analytical engine of the project.

**Independent Test**: This can be fully tested by running the model fitting script on a simulated dataset with known interaction parameters and verifying that the likelihood-ratio test correctly identifies the interaction term as significant (p < 0.05) with the expected coefficient sign.

**Acceptance Scenarios**:

1. **Given** the cleaned analysis-ready CSV, **When** the model fitting script executes the `lme4` or `statsmodels` logistic regression, **Then** the process must complete within 4 hours on a 2-core CPU without GPU errors.
2. **Given** the full model and a reduced model (without the three-way interaction), **When** the likelihood-ratio test is performed, **Then** the output must include a chi-squared statistic, degrees of freedom, and a p-value indicating the significance of the interaction.
3. **Given** the model convergence diagnostics, **When** the script checks residuals, **Then** the output must report "Convergence: OK" or flag overdispersion if the dispersion parameter exceeds unity.

---

### User Story 3 - Visualization of Marginal Effects (Priority: P3)

The researcher MUST be able to generate marginal effect plots showing the slope of fixation duration on recall probability for high-anxiety versus low-anxiety groups, with 95% confidence intervals.

**Why this priority**: Visualizing the interaction effect is critical for interpreting the results and communicating the "enhanced encoding" hypothesis or null findings to the scientific community.

**Independent Test**: This can be fully tested by generating the plot file (PNG) and verifying that the plot contains two distinct regression lines (high vs. low anxiety) with shaded confidence intervals and a legend, without requiring a display server (headless generation).

**Acceptance Scenarios**:

1. **Given** the fitted model coefficients, **When** the plotting script generates the marginal effects graph, **Then** the output PNG must correctly render two distinct regression lines and shaded 95% CI regions for both high and low anxiety groups, regardless of the slope direction.
2. **Given** the plot generation process, **When** the script runs, **Then** the total disk usage for the output artifacts (figures + logs) must remain within a reasonable storage budget.
3. **Given** the confidence interval calculation, **When** the plot is rendered, **Then** the shaded regions must represent the confidence interval derived from the model's standard errors.

---

### Edge Cases

- **Missing Data**: What happens when a participant's eye-tracking data has >50% missing frames due to blinks or loss of lock? The system must exclude that participant from the analysis. For individual trials, if missing gaze data is excessive, that trial must be excluded. Imputation is NOT permitted to preserve the integrity of observed gaze metrics.
- **Model Convergence Failure**: How does the system handle non-convergence of the mixed-effects model due to sparse data in the three-way interaction? The system must automatically retry with a simplified random effects structure (e.g., removing the random slope for stimulus) and log the warning, rather than crashing.
- **Dataset Variance**: What happens if the OpenNeuro dataset lacks STAI scores for some participants? The system must exclude those participants from the anxiety-modulation analysis and report the reduced sample size in the final log.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and unzip the RSVP dataset (target: OpenNeuro ds001435 or equivalent) via `wget`, verify available disk space is sufficient for the full dataset, and validate that the dataset contains required variables (STAI scores, recall responses) before proceeding. (See US-1)
- **FR-002**: System MUST extract fixation duration from raw gaze coordinates using a standard velocity-threshold algorithm (e.g., I-VT) with a configurable threshold and a minimum fixation window sufficient to align with RSVP stimulus duration. (See US-1)
- **FR-003**: System MUST map stimulus IDs to emotional valence categories (threat, neutral) using a verified lookup table (IAPS/NimStim) and reject any unmapped IDs. (See US-1)
- **FR-004**: System MUST fit a mixed-effects logistic regression model with the formula `recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)` using CPU-only libraries (e.g., `statsmodels` or `lme4`), assuming a fully crossed design. If the design is not fully crossed, the system must fallback to `(1|participant)` only. The model MUST use the 'logit' link function, 'bobyqa' optimizer, a sufficiently high maximum number of iterations to ensure convergence, and convergence tolerance of a sufficiently small threshold. (See US-2)
- **FR-005**: System MUST perform a likelihood-ratio test comparing the full model against a reduced model lacking the three-way interaction term to assess the specific modulation by anxiety. (See US-2)
- **FR-006**: System MUST generate a marginal effects plot visualizing the relationship between fixation duration and recall probability for high vs. low anxiety groups with 95% confidence intervals. (See US-3)
- **FR-007**: System MUST report model convergence status and residual diagnostics (overdispersion check) in the final output log. (See US-2)

### Key Entities

- **Participant**: Represents an individual subject in the study, identified by a unique ID, with attributes for `trait_anxiety_score` (STAI) and `group` (high/low based on median split).
- **Stimulus**: Represents an individual image/frame in the RSVP sequence, identified by a unique ID, with attributes for `valence` (threat/neutral) and `duration_ms`.
- **Trial**: Represents a single observation unit linking a participant to a stimulus, containing `fixation_duration_ms`, `recall_accuracy` (binary), and the associated `participant_id` and `stimulus_id`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Data preprocessing success rate is measured against the total number of valid trials in the raw dataset; the system must retain ≥ 80% of trials after filtering for missing gaze data. (See US-1)
- **SC-002**: Model convergence rate is measured against the total number of model fitting attempts; the system must achieve convergence for ≥ 95% of bootstrap samples or the full dataset without manual intervention. (See US-2)
- **SC-003**: Statistical power is measured against the expected effect size (f2 ≥ 0.15) using a Monte Carlo simulation with alpha=0.05 and A substantial number of iterations will be performed to ensure convergence.; the system must report the achieved power to assess study sensitivity. (See US-2)
- **SC-004**: Computational feasibility is measured against the 4-hour runtime limit on GitHub Actions ubuntu-latest; the total pipeline (download, preprocess, model, plot) must complete within 4 hours. (See US-2)
- **SC-005**: Visual output validity is measured against the presence of confidence intervals; the generated plot must include shaded confidence interval regions for both high and low anxiety groups. (See US-3)

## Assumptions

- The OpenNeuro dataset (ds001435 or equivalent) contains both the raw eye-tracking data and the post-task recall responses for the same participants, and includes the STAI scores or a proxy measure for trait anxiety.
- The "threat" stimuli in the dataset are sufficiently distinct from "neutral" stimuli to allow for binary classification based on the provided metadata or IAPS mapping.
- The mixed-effects model will converge on the available dataset size (approx. a moderate cohort of participants) without requiring complex Bayesian priors or GPU acceleration.
- The velocity-threshold algorithm for fixation detection (I-VT) with a velocity threshold and minimum window duration is an appropriate standard for this specific RSVP dataset resolution and sampling rate.
- The "high anxiety" and "low anxiety" groups will be defined by a median split of the STAI scores, which is a standard practice for exploratory interaction analysis in this domain.
- The analysis will be treated as associational; no causal claims will be made about the effect of anxiety on memory unless the study design (randomization) supports it, which is not the case here.
- The dataset variables (fixation duration, recall accuracy, STAI scores) are present and correctly formatted in the source files; if a variable is missing, the pipeline will fail gracefully with a specific error message rather than proceeding with imputation.
- The study design assumes a fully crossed structure (every participant sees every stimulus) to justify the inclusion of `(1|stimulus_id)` as a random effect.