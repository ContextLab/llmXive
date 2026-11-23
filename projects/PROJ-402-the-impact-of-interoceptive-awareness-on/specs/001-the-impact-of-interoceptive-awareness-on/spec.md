# Feature Specification: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Feature Branch**: `001-impact-of-interoceptive-awareness`  
**Created**: 2026-07-31  
**Status**: Draft  
**Input**: User description: "Does behavioral interoceptive accuracy predict the magnitude of physiological emotional regulation during acute psychosocial stress, independent of baseline heart rate variability?"

## User Scenarios & Testing

### User Story 1 - Data Availability Audit (Priority: P1)

As a researcher, I want to systematically verify whether open-source psychophysiological datasets (specifically WESAD and OpenNeuro) contain the necessary multimodal data (behavioral interoceptive tasks AND stress paradigms) to test the hypothesis, so that I can determine if the study is feasible before attempting analysis.

**Why this priority**: This is the critical path. The idea explicitly states that the primary expected result is a feasibility report confirming data scarcity. If the data does not exist, the project cannot proceed to regression analysis, and the "finding" is the documentation of the gap.

**Independent Test**: Can be fully tested by executing the data discovery script, which outputs a `data_audit.md` file listing the presence or absence of the Schandry heartbeat perception task and TSST stress markers in the specified datasets.

**Acceptance Scenarios**:

1. **Given** the WESAD and OpenNeuro repositories are accessible via `wget` and `curl`, **When** the script scans for "heartbeat", "Schandry", "interoception", and "TSST" keywords in metadata and event files, **Then** the output `data_audit.md` explicitly states whether the specific behavioral interoception task is present or absent in each dataset.
2. **Given** the script runs on the GitHub Actions free-tier runner, **When** the scan completes, **Then** the script exits with code 0 and generates a human-readable report within 15 minutes, regardless of whether the required data is found.

### User Story 2 - Physiological Signal Preprocessing (Priority: P2)

As a researcher, I want to extract and compute Heart Rate Variability (HRV) metrics (RMSSD, SDNN) from ECG/PPG signals for baseline and stress phases in the available datasets, so that I can quantify the physiological regulation magnitude if the data exists.

**Why this priority**: This is the core analytical engine. Even if the primary hypothesis cannot be tested due to missing interoception data, the ability to correctly compute HRV from raw signals is a necessary capability for any future extension or secondary analysis of stress reactivity.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a known subset of WESAD data (which contains ECG/PPG) and verifying that the output CSV contains valid RMSSD and SDNN values for both baseline and stress windows.

**Acceptance Scenarios**:

1. **Given** a valid BIDS-formatted dataset containing ECG or PPG signals, **When** the preprocessing script processes the raw signal using `hrv-analysis`, **Then** it outputs a CSV file with columns for `subject_id`, `phase` (baseline/stress), `RMSSD`, and `SDNN`, with no NaN values in the metric columns for subjects with complete data.
2. **Given** a signal with artifacts or missing segments, **When** the script processes the data, **Then** it flags the subject as "incomplete" in the output log and excludes them from the final metric calculation without crashing the pipeline.

### User Story 3 - Regression Analysis & Reporting (Priority: P3)

As a researcher, I want to perform a linear regression analysis (if data exists) to test if interoceptive accuracy predicts stress regulation magnitude while controlling for baseline HRV, so that I can quantify the independent effect of interoception.

**Why this priority**: This is the specific hypothesis test. It is lower priority than the audit and preprocessing because it is conditional on the data being available. If the audit fails (P1), this story is skipped.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic dataset where the relationship between variables is known, verifying that the script correctly outputs the regression coefficients, p-values, and the specific control for baseline HRV.

**Acceptance Scenarios**:

1. **Given** a dataset containing both interoceptive accuracy scores and HRV metrics, **When** the analysis script runs the linear regression model (Outcome: Stress HRV; Predictors: Interoception Accuracy, Baseline HRV), **Then** the output report includes the coefficient for Interoception Accuracy, its p-value, and the R-squared value.
2. **Given** the dataset lacks the interoceptive variable, **When** the script runs, **Then** it calculates the Upper Bound of Detectable Effect (UBDE) based on sample size and noise, and outputs this as the primary scientific finding instead of a regression coefficient.

### Edge Cases

- **What happens when** the dataset contains the stress task but the interoception task is only present for a subset of subjects? **The system** must exclude subjects with missing interoception data from the regression but include them in the descriptive statistics for stress reactivity, clearly documenting the reduced sample size (N) in the report.
- **How does the system handle** datasets where the ECG signal is too noisy to compute HRV (e.g., motion artifacts during TSST)? **The system** must apply a strict artifact rejection threshold (e.g., < 5% valid beats) and exclude those specific epochs from the HRV calculation, logging the exclusion count.
- **What happens when** the dataset contains multiple stress paradigms (e.g., TSST and cold pressor)? **The system** must report the presence of ALL stress paradigms found in the audit (FR-002) to ensure a comprehensive data gap finding, but default to analyzing the TSST phase only in the regression (FR-005), as per the research question's focus on "acute psychosocial stress."

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the WESAD dataset from Zenodo (DOI: 10.5281/zenodo.1292932) and download the OpenNeuro index (metadata) for studies containing "TSST" and "heartbeat" or "interoception" keywords, then scan local metadata and event files to verify the presence of a specific behavioral interoceptive accuracy task (e.g., Schandry heartbeat perception) distinct from resting-state measures. (See US-1)
- **FR-002**: System MUST scan dataset metadata and event files to verify the presence of a specific behavioral interoceptive accuracy task. "Presence" is confirmed ONLY if a BIDS `events.tsv` file contains a `task` label matching 'Schandry' or 'heartbeat' (case-insensitive). (See US-1)
- **FR-003**: System MUST compute HRV metrics (RMSSD, SDNN) from ECG/PPG signals for both baseline (resting) and stress (TSST) phases using the `hrv-analysis` library. (See US-2)
- **FR-004**: System MUST extract the HRV metric for the stress phase (Stress HRV) to serve as the outcome variable for regression. (See US-3)
- **FR-005**: System MUST perform a linear regression analysis (ANCOVA style) with Stress HRV as the outcome, interoceptive accuracy as the primary predictor, and baseline HRV as a covariate to isolate the effect of interoception. (See US-3)
- **FR-006**: System MUST generate a `data_audit.md` report explicitly stating the feasibility of the study based on the presence/absence of required variables. If behavioral data is missing, the report MUST include the calculated Upper Bound of Detectable Effect (UBDE). (See US-1)
- **FR-007**: System MUST execute the entire pipeline (download, preprocess, analyze, report) within a reasonable time limit on a CPU-only GitHub Actions runner. (See Assumptions)

### Key Entities

- **Subject**: A participant in the dataset with unique ID, containing associated physiological signals and behavioral scores.
- **Phase**: A distinct temporal segment of the experiment (e.g., "Baseline", "Stress", "Recovery") associated with specific signal windows.
- **Metric**: A derived quantitative value (e.g., RMSSD, Interoceptive Accuracy Score) calculated from raw signals or task performance.
- **Model**: The statistical representation (Linear Regression) linking predictors to outcomes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The presence or absence of the Schandry heartbeat perception task in the WESAD/OpenNeuro datasets is measured against the dataset's official documentation and metadata files. (See US-1)
- **SC-002**: The computed HRV metrics (RMSSD, SDNN) are measured against the WESAD ground-truth labels and the output of the `hrv-analysis` library on the PhysioNet MIT-BIH test set to ensure valid calculation from raw ECG/PPG. (See US-2)
- **SC-003**: The regression coefficient for interoceptive accuracy is measured against the null hypothesis (coefficient = 0) to determine statistical significance, with baseline HRV included as a control. (See US-3)
- **SC-004**: The total pipeline execution time is measured against the GitHub Actions free-tier limit. using the `GITHUB_JOB_DURATION` environment variable or script start/end timestamps logged to a file. (See FR-007)
- **SC-005**: The sample size (N) of subjects with complete data for all variables is measured against the initial dataset size to quantify data attrition due to missing tasks or artifacts. (See Edge Cases)

## Assumptions

- **Assumption about data availability**: The WESAD dataset is assumed to contain high-quality ECG/PPG data for stress and baseline phases, but it is explicitly assumed that it **does not** contain a behavioral interoceptive accuracy task (Schandry task), which is the primary driver of the "data gap" finding.
- **Assumption about methodological framing**: Since no randomization is possible in observational dataset analysis, the regression results will be framed strictly as **associational** (predictive) relationships, not causal claims, regardless of the statistical significance of the coefficients.
- **Assumption about compute constraints**: The analysis will rely on classical statistical methods (linear regression) and standard Python libraries (`pandas`, `scikit-learn`, `hrv-analysis`) that run efficiently on CPU; no GPU acceleration, deep learning models, or large language models will be used. The total pipeline execution time is constrained to a feasible duration.
- **Assumption about variable definition**: "Interoceptive accuracy" is defined strictly as performance on a behavioral heartbeat counting/estimation task; no proxy variables (e.g., resting HRV stability) will be used to substitute for missing behavioral data.
- **Assumption about threshold justification**: No arbitrary decision thresholds (e.g., for artifact rejection) are introduced without a community-standard basis; artifact rejection will use standard signal processing defaults (e.g., < 5% valid beats) and sensitivity will be noted if the threshold is swept.
- **Assumption about statistical model**: The system will model "Stress HRV" as the outcome and "Baseline HRV" as a covariate (ANCOVA) to avoid mathematical tautology, rather than regressing the difference (Stress - Baseline) against Baseline.