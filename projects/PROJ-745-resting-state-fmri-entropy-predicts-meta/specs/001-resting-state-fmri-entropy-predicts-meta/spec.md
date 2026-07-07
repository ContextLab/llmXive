# Feature Specification: Resting-State fMRI Entropy Predicts Metacognitive Accuracy

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Does individual variability in whole‑brain multiscale sample entropy of resting‑state fMRI predict metacognitive accuracy (meta‑d′/d′) on a visual perceptual decision‑making task?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I need the system to download, preprocess, and parcellate resting-state fMRI data from the Human Connectome Project (HCP) 1200-subject release so that I can derive clean, comparable time series for entropy calculation.

**Why this priority**: Without high-quality, standardized input data, no subsequent analysis is possible. This is the foundational step that enables all downstream metrics.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a subset of 10 HCP subjects and verifying that the output consists of 400 time series per subject (matching the Schaefer atlas) with no NaN values and a valid mean framewise displacement metric.

**Acceptance Scenarios**:

1. **Given** a valid HCP subject ID, **When** the preprocessing script runs, **Then** it outputs a CSV file containing 400 parcellated time series with dimensions (timepoints, 400) and a metadata file containing motion parameters.
2. **Given** a subject with high motion (>0.5 mm mean FD), **When** the script runs, **Then** the subject is flagged in the metadata log but still processed to allow for covariate control later.
3. **Given** corrupted or missing raw data files for a subject, **When** the script runs, **Then** the subject is skipped, and a clear error entry is logged without crashing the entire batch process.

---

### User Story 2 - Entropy and Metacognitive Metric Computation (Priority: P2)

As a researcher, I need the system to compute multiscale sample entropy for each parcel and calculate metacognitive efficiency (meta-d′/d′) from behavioral trial data so that I can obtain the primary predictor and outcome variables.

**Why this priority**: This step generates the core scientific variables of the study. The validity of the hypothesis test depends entirely on the correctness of these calculations.

**Independent Test**: The computation module can be tested by feeding synthetic time series with known entropy properties and synthetic behavioral data with known meta-d′ values, verifying that the output matches theoretical expectations within a tolerance of 0.01.

**Acceptance Scenarios**:

1. **Given** a preprocessed time series for a single parcel, **When** the entropy module runs, **Then** it outputs a scalar value for multiscale sample entropy (averaged across scales τ=1–5) and a log entry confirming the use of the `nolds` library.
2. **Given** confidence-rated behavioral trial data (stimulus, response, confidence), **When** the behavioral module runs, **Then** it outputs meta-d′, d′, and the efficiency ratio (meta-d′/d′) for the subject.
3. **Given** a dataset where confidence ratings are missing for >10% of trials, **When** the module runs, **Then** it excludes that subject from the final analysis and logs a "Insufficient behavioral data" warning.

---

### User Story 3 - Statistical Association and Sensitivity Analysis (Priority: P3)

As a researcher, I need the system to run a linear regression to test the association between entropy and metacognition, including a sensitivity analysis on the entropy tolerance parameter r, so that I can determine the robustness of the findings.

**Why this priority**: This step answers the research question. The inclusion of sensitivity analysis ensures the results are not artifacts of arbitrary parameter choices, addressing methodological soundness requirements.

**Independent Test**: The analysis module can be tested by running it on a small, pre-defined dataset where the correlation coefficient is known (e.g., r=0.4), verifying that the p-value is <0.05 and that the sensitivity sweep produces the expected trend in false-positive rates.

**Acceptance Scenarios**:

1. **Given** the computed entropy and efficiency vectors, **When** the statistical model runs, **Then** it outputs a regression coefficient, standard error, and p-value (Bonferroni-corrected) for the entropy predictor.
2. **Given** a specific entropy tolerance parameter r value, **When** the sensitivity analysis runs, **Then** it sweeps the parameter across values {0.1, 0.15, 0.2} and outputs a summary table showing how the association strength (beta) and p-value change.
3. **Given** a dataset with insufficient sample size (n < 30) to support the planned degrees of freedom, **When** the system runs, **Then** it halts execution and reports a "Power Insufficient" error before attempting the regression.

### Edge Cases

- What happens when the HCP behavioral data for a subject does not include confidence ratings? The system must exclude the subject and log the exclusion reason.
- How does the system handle subjects with zero variance in their time series (flat lines)? The system must detect this, exclude the subject, and log "Zero Variance Detected" to prevent invalid entropy calculations.
- How does the system handle the case where the sample size is too small to support the planned degrees of freedom? The system must halt execution and report a "Power Insufficient" error before attempting the regression.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and cache the HCP large-scale cohort resting-state fMRI minimally preprocessed data. and the associated behavioral dataset for the visual perceptual decision task (See US-1).
- **FR-002**: The system MUST apply nuisance regression (motion parameters, CSF/WM signals) and band-pass filtering to all resting-state time series prior to parcellation. (See US-1).
- **FR-003**: The system MUST compute multiscale sample entropy for each of the Schaefer atlas parcels and aggregate them into a single whole-brain entropy score per subject by calculating the arithmetic mean across all parcels. (See US-2).
- **FR-004**: The system MUST calculate metacognitive efficiency (meta-d′/d′) from confidence-rated trial data using the standard meta-d′ toolbox logic (See US-2).
- **FR-005**: The system MUST fit a linear regression model `meta_efficiency ~ whole_brain_entropy + age + sex + mean_framewise_displacement` and report the regression coefficient and Bonferroni-corrected p-value (See US-3).
- **FR-006**: The system MUST perform a sensitivity analysis by sweeping the entropy tolerance parameter r across values {0.1, 0.15, 0.2} and report the variation in the association strength (beta) and p-value (See US-3).
- **FR-007**: The system MUST execute all statistical analyses on a CPU-only environment without requiring GPU acceleration or mixed-precision training (See US-3).

### Key Entities

- **Subject**: An individual participant from the HCP 1200 release, identified by a unique ID, containing associated fMRI and behavioral data.
- **TimeSeries**: A 1D array of BOLD signal values for a specific brain parcel, preprocessed and filtered.
- **EntropyMetric**: A scalar value representing the multiscale sample entropy of a subject's whole-brain signal.
- **MetacognitiveEfficiency**: A scalar ratio (meta-d′/d′) representing the accuracy of a subject's confidence judgments.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The preprocessing pipeline successfully processes ≥ 95% of the available HCP subjects without crashing, measured against the total count of subjects in the release (See US-1) (FR-001, FR-002).
- **SC-002**: The computed entropy values for the whole-brain profile fall within the expected physiological range [0.2, 1.5] for ≥ 90% of subjects, measured against established norms reported in Zou et al. (2019) or equivalent HCP-based MSE studies (See US-2) (FR-003).
- **SC-003**: The statistical model produces a valid regression coefficient and p-value for the entropy predictor in ≥ 90% of the analyzed cohort, measured against the total number of subjects with valid behavioral data (See US-3) (FR-005).
- **SC-004**: The sensitivity analysis demonstrates that the direction of the association (positive/negative) remains consistent across the entropy tolerance parameter r sweep {0.1, 0.15, 0.2}, measured against the baseline result at the default value r=0.15 (See US-3) (FR-006).
- **SC-005**: The entire analysis pipeline completes within 6 hours on a GitHub Actions ubuntu-latest runner with ≤ 7 GB RAM usage, measured against the GitHub Actions free-tier constraints (See US-3) (FR-007).

## Assumptions

- The Human Connectome Project (HCP) 1200-subject release contains both the resting-state fMRI data and the specific visual perceptual decision-making task data with confidence ratings for the same subjects.
- The `nolds` Python package is available and compatible with the CPU-only CI environment for computing multiscale sample entropy.
- The Schaefer 400-region atlas is the standard parcellation method for this analysis and is compatible with the HCP minimally preprocessed data format.
- The relationship between entropy and metacognition is assumed to be linear for the purpose of the primary linear regression model.
- The sample size of the HCP 1200 release is sufficient to achieve statistical power > 0.8 for detecting a small-to-medium effect size (r ≈ 0.2) after Bonferroni correction.
- The analysis assumes that head motion (mean framewise displacement) is a confounding variable that can be adequately controlled for via linear covariate adjustment.
- No GPU or CUDA acceleration is required; all computations (entropy, regression, cross-validation) are performed in double precision on the CPU.