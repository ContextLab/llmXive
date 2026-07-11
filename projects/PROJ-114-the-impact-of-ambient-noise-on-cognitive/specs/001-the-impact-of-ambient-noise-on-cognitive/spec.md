# Feature Specification: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

**Feature Branch**: `001-ambient-noise-cognitive-flexibility`  
**Created**: 2026-07-04  
**Status**: Draft  
**Input**: User description: "The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers"

## User Scenarios & Testing

### User Story 1 - Data Collection Pipeline (Priority: P1)

A remote worker uses the system to record their ambient acoustic environment and complete cognitive tasks over a 5-day period, generating a structured dataset linking decibel levels to performance metrics.

**Why this priority**: This is the foundational data acquisition layer. Without valid, time-synchronized logs of noise and task performance, no analysis can occur. It represents the minimum viable data product.

**Independent Test**: A simulated user session can be run where a script generates synthetic decibel logs and task-switching metrics; the system must successfully ingest, align, and store these records without data loss.

**Acceptance Scenarios**:

1. **Given** a participant has installed the logging app and completed the consent form, **When** they work for 4 hours in an environment with fluctuating noise, **Then** the system logs decibel levels at ≥1Hz frequency (sufficient to calculate hourly standard deviation with <2dB error) and timestamps them with resolution ≤10ms, verified by comparing against a reference clock source.
2. **Given** a participant has completed the baseline and final task-switching battery, **When** they submit the results, **Then** the system stores reaction times, error counts, and task conditions linked to the participant ID.
3. **Given** a participant has <80% valid logging hours (defined as count of 1-minute bins with ≥1 log entry) OR any single data gap >20% of total session time, **When** the data is processed, **Then** the system flags this participant for exclusion in the pre-processing step.

---

### User Story 2 - Statistical Analysis Engine (Priority: P2)

A researcher runs the analysis pipeline to fit a linear mixed-effects model, testing the non-linear relationship between noise categories (Low, Moderate, High) and cognitive flexibility scores.

**Why this priority**: This is the core scientific value proposition. It transforms raw data into the primary hypothesis test (the "coffee shop effect" vs. impairment).

**Independent Test**: A fixed dataset of simulated participants can be processed; the system must output a model summary containing fixed effects coefficients, p-values, and likelihood-ratio test results for the quadratic noise term.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of N=150 participants with valid logs, **When** the analysis script executes, **Then** it fits a linear mixed-effects model with continuous noise level and noise variability (standard deviation over the task session) as fixed effects, and the Cognitive Flexibility Index (CFI) as the dependent variable, with participant ID as a random intercept.
2. **Given** the model includes a quadratic term for noise level, **When** the likelihood-ratio test is performed, **Then** the system outputs the p-value comparing the quadratic model against the linear baseline.
3. **Given** the model converges, **When** post-hoc pairwise comparisons are run, **Then** the system reports Tukey HSD adjusted p-values for differences between Low, Moderate, and High noise groups.

---

### User Story 3 - Robustness & Sensitivity Reporting (Priority: P3)

A researcher validates the findings by running sensitivity analyses, including threshold sweeps for noise categorization and exclusion of high-sensitivity participants, to ensure the "sweet spot" hypothesis is not an artifact of arbitrary cutoffs.

**Why this priority**: This ensures methodological soundness and defensibility against claims of data dredging or threshold bias, which is critical for publication.

**Independent Test**: The system can be run with modified noise thresholds (e.g., shifting the Moderate band by ±5dB); the output must show how the headline significance rates change across these sweeps.

**Acceptance Scenarios**:

1. **Given** the primary model results, **When** the sensitivity analysis script runs, **Then** it re-runs the model with noise thresholds swept over {Low<40dB, Moderate 40-50dB, High>50dB}, {Low<45dB, Moderate 45-65dB, High>65dB} (Baseline), and {Low<50dB, Moderate 50-70dB, High>70dB}.
2. **Given** the sensitivity runs, **When** the results are aggregated, **Then** the system reports the variation in false-positive rates and the stability of the "Moderate" effect across the different threshold definitions.
3. **Given** participants with extreme self-reported noise sensitivity, **When** the robustness check is executed, **Then** the system re-fits the model excluding these participants and compares the effect size to the full sample.

---

### Edge Cases

- What happens when a participant's mobile app fails to log noise for >2 consecutive hours due to battery saving? (System flags data gap; participant excluded if gap >20% of total time, consistent with US-1 logic).
- How does the system handle reaction time outliers >3 SD from the mean? (System removes them automatically but logs the count for audit).
- What if the mixed-effects model fails to converge? (System falls back to a simpler linear model or reports a convergence error with diagnostic stats).
- How does the system handle participants who complete tasks in a completely silent environment (0dB)? (Treated as "Low" noise; model checks for singularity).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST aggregate continuous decibel logs into three discrete categories (Low: <45dB, Moderate: 45-65dB, High: >65dB) for *descriptive analysis only* (Primary Hypothesis Baseline); the raw continuous stream MUST be retained for statistical modeling (See US-1).
- **FR-002**: The system MUST compute the Cognitive Flexibility Index (CFI) as the sum of standardized (z-scored) reaction time difference between switch and repeat trials and standardized rule-violation error count (See US-1).
- **FR-003**: The system MUST fit a linear mixed-effects model with continuous noise level, noise variability (standard deviation over the task session), and a quadratic noise term as fixed effects, and participant ID as a random intercept, using the CFI as the dependent variable (See US-2).
- **FR-004**: The system MUST perform a likelihood-ratio test comparing the model with the quadratic noise term against a linear-only model to test for non-linearity (See US-2).
- **FR-005**: The system MUST execute a sensitivity analysis sweeping the noise categorization thresholds over a set of {40, 45, 50} dB and {60, 65, 70} dB and report the stability of the primary effect size (See US-3).
- **FR-006**: The system MUST apply a multiple-comparison correction (e.g., Tukey HSD) to all post-hoc pairwise comparisons between noise categories to control family-wise error rate (See US-2).
- **FR-007**: The system MUST define "valid logging hours" as the count of 1-minute bins containing ≥1 log entry for the purpose of data exclusion logic (See US-1).
- **FR-008**: The system MUST require a power analysis justification for the target sample size (N=150) prior to initiating data collection (See US-1).
- **FR-009**: The system MUST execute a device-specific calibration protocol using a reference tone before logging; if calibration fails or error margin >2dB, the system MUST flag the participant for exclusion (See Assumption).

### Non-Functional Requirements

- **NFR-001**: The end-to-end analysis pipeline MUST complete within 6 hours on a standard GitHub Actions runner with 7GB RAM.

### Key Entities

- **Participant**: Represents a remote worker; attributes include ID, demographic covariates (age, gender, job type), self-reported noise sensitivity, and baseline cognitive scores.
- **NoiseLog**: Represents a time-series record of acoustic environment; attributes include timestamp, decibel level (dB), and calculated hourly standard deviation.
- **TaskPerformance**: Represents a single cognitive task session; attributes include trial type (switch/repeat), reaction time (ms), error flag (boolean), and session timestamp.
- **ModelResult**: Represents the output of the statistical analysis; attributes include coefficients, p-values, confidence intervals, and convergence status.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of participants with valid data (≥80% logging hours, ≥90% task completion) is measured against the recruitment target of N=150, justified by the power analysis required in FR-008 (See US-1).
- **SC-002**: The system outputs the p-value for the quadratic term, which is then compared to 0.05 to assess the null hypothesis of linearity (See US-2).
- **SC-003**: The stability of the "Moderate noise" effect size is measured across the sensitivity analysis threshold sweeps (±5dB) to ensure the result is not an artifact of a single arbitrary cutoff (See US-3).
- **SC-004**: The family-wise error rate in post-hoc comparisons is measured against the nominal alpha level (0.05) after Tukey HSD correction (See US-2).

## Assumptions

- **Assumption about data validity**: The mobile app's microphone calibration is sufficient to distinguish between the defined noise categories (Low <45dB, Moderate 45-65dB, High >65dB) with an error margin of <2dB, *provided* the device-specific calibration protocol (FR-009) is executed successfully.
- **Assumption about cognitive tasks**: The digital task-switching battery provided by the Open Science Framework is a validated instrument for measuring cognitive flexibility (switch cost) in remote settings.
- **Assumption about dataset-variable fit**: The recruited dataset will contain all required variables (decibel logs, reaction times, error counts, demographics); if the source lacks specific covariates like "perceived noise disturbance," the analysis will rely solely on objective measures.
- **Assumption about compute constraints**: The dataset size (N=150, of logs) will fit within the 7GB RAM limit of the free-tier CI runner, allowing the use of `statsmodels` without memory overflow.
- **Assumption about inference framing**: The study design is observational (no random assignment of noise levels); therefore, all findings will be framed as associational, not causal, in the final output.
- **Assumption about threshold justification**: The noise categories (quiet office vs. busy street noise levels) are based on community standards for quiet office vs. busy street noise., and the sensitivity analysis will confirm the robustness of these specific boundaries.
- **Assumption about predictor collinearity**: While "noise variability" and "average noise level" may be correlated, the model will include a collinearity diagnostic (VIF) to ensure independent predictive effects are not claimed if VIF > 5.