# Feature Specification: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Feature Branch**: `001-pain-sensitivity-microstates`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Does the temporal dynamics of resting‑state EEG microstates predict an individual's heat‑pain threshold?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest the OpenNeuro ds003XXX dataset, apply standard EEG preprocessing (re-referencing, filtering, ICA artifact removal), and segment the data into canonical microstate maps to produce a clean feature matrix for every participant.

**Why this priority**: Without a robust, reproducible preprocessing pipeline that handles the raw EEG and extracts the microstate descriptors (duration, occurrence, transitions, spectral power), no predictive modeling can occur. This is the foundational data product of the project.

**Independent Test**: The pipeline can be executed end-to-end on a sample of 5 participants from the dataset; the output must be a CSV file containing 30 features per participant and the corresponding heat-pain threshold labels, with no NaN values in the feature columns.

**Acceptance Scenarios**:
1. **Given** the raw EEG files and heat-pain threshold CSV exist in the input directory, **When** the preprocessing script is executed, **Then** the output feature matrix contains exactly 30 features per participant with no missing values.
2. **Given** an EEG recording with significant ocular artifacts, **When** the ICA component removal step is applied, **Then** the participant is included in the output only if ≥ 4 minutes of valid EEG data remains after artifact removal; otherwise, the participant is excluded with a logged warning.

### User Story 2 - Predictive Model Training and Validation (Priority: P2)

The system must train an Elastic Net regression model using nested cross-validation to predict heat-pain thresholds from the extracted microstate features, and evaluate performance using Pearson correlation and Mean Absolute Error (MAE).

**Why this priority**: This is the core scientific inquiry. It tests the hypothesis that microstate dynamics contain predictive information. It must be robust to overfitting via nested cross-validation.

**Independent Test**: Running the training script on the full dataset must produce a cross-validated Pearson correlation coefficient (r) and a 95% confidence interval derived from bootstrap resampling, respecting the nested cross-validation structure for all statistical estimates.

**Acceptance Scenarios**:
1. **Given** the complete feature matrix and labels, **When** the Elastic Net model is trained with nested 5-fold cross-validation, **Then** the output report includes the mean Pearson correlation (r) and the bootstrap confidence interval.
2. **Given** a permutation test of 1,000 iterations performed *within* the nested cross-validation loop, **When** the null distribution is generated, **Then** the empirical p-value is calculated and reported, indicating whether the observed correlation significantly exceeds chance (p < 0.05).

### User Story 3 - Statistical Rigor and Sensitivity Analysis (Priority: P3)

The system must perform multiple-comparison corrections for feature testing, conduct a sensitivity analysis on the classification threshold (if group comparisons are made), and verify that no predictor collinearity invalidates the coefficient interpretations.

**Why this priority**: To satisfy the methodological soundness panel, the design must explicitly address multiplicity, threshold justification, and collinearity. Without this, the results are statistically defensible only as exploratory, not confirmatory.

**Independent Test**: The analysis report must include a section on multiple comparison correction (e.g., Bonferroni or FDR) for the 30 features, a sensitivity sweep of any decision thresholds, and a Variance Inflation Factor (VIF) diagnostic check for the top predictors.

**Acceptance Scenarios**:
1. **Given** the p-values for the 30 feature coefficients, **When** the multiple-comparison correction is applied, **Then** the report lists the adjusted p-values and flags any features that remain significant.
2. **Given** a decision threshold for classifying high vs. low pain sensitivity (e.g., median split), **When** the threshold is swept across {median-0.1, median-0.05, median, median+0.05, median+0.1} (in °C), **Then** the report shows the variation in the top predictor's effect size and the model's R-squared stability across the sweep.

### Edge Cases

- **What happens when** the dataset contains participants with < 4 minutes of valid EEG data after artifact removal? -> The system MUST exclude these participants and log a warning; the analysis proceeds with the remaining N.
- **How does the system handle** a situation where the Elastic Net model fails to converge within the default iteration limit? -> The system MUST increase the maximum iterations to [deferred] and re-run; if it still fails, it MUST raise an explicit error and halt the job.
- **What happens when** the Variance Inflation Factor (VIF) for a predictor exceeds 10? -> The system MUST flag the predictor as collinear in the diagnostic report but MUST NOT exclude it or re-run the model, as Elastic Net handles collinearity and re-running would introduce data-dependent selection bias.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the OpenNeuro ds003XXX dataset, re-reference to average mastoids, band-pass filter (1–40 Hz), and remove ocular/muscle artifacts via ICA. (See US-1)
- **FR-002**: System MUST extract 30 microstate features per participant: 4 mean durations, 4 occurrence rates, 16 transition probabilities (4x4 matrix flattened), and 6 spectral power features (delta, theta, alpha, beta, low-gamma, high-gamma). (See US-1)
- **FR-003**: System MUST train an Elastic Net regression model (α=0.5) with nested 5-fold cross-validation to predict heat-pain thresholds from the 30 extracted features. (See US-2)
- **FR-004**: System MUST perform 1,000 permutations of the pain-threshold labels *within* the nested cross-validation loop to generate a null distribution and calculate an empirical p-value for the observed correlation. (See US-2)
- **FR-005**: System MUST apply a False Discovery Rate (FDR) correction to the p-values of all 30 feature coefficients to control for multiplicity. (See US-3)
- **FR-006**: System MUST calculate Variance Inflation Factors (VIF) for all predictors and report any with VIF > 10 in the diagnostic output, but MUST NOT exclude them or re-run the model. (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis on the median-split threshold for exploratory group comparisons, sweeping the cutoff by ±0.05°C and ±0.1°C (methodologically essential to verify robustness against arbitrary cutoffs), and report the resulting changes in effect size estimates. (See US-3)

### Key Entities

- **Participant**: Represents an individual in the study, containing attributes: `id`, `heat_pain_threshold`, `age`, `gender`.
- **MicrostateFeature**: Represents a derived metric from the EEG, containing attributes: `participant_id`, `feature_name` (e.g., "MS_C_Duration", "Spectral_Beta_Power"), `value`, `standard_error`.
- **ModelResult**: Represents the output of the regression, containing attributes: `pearson_r`, `p_value`, `mae`, `confidence_interval_lower`, `confidence_interval_upper`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient between predicted and observed heat-pain thresholds is measured against the chance level established by the permutation null distribution (See US-2).
- **SC-002**: The False Discovery Rate (FDR) adjusted p-value for the top predictive feature is measured against the significance threshold of 0.05 (See US-3).
- **SC-003**: The Variance Inflation Factor (VIF) for the top 5 predictors is measured against the collinearity threshold of 10 to ensure model stability (See US-3).
- **SC-004**: The variation in effect size estimates across the sensitivity analysis threshold sweep is measured against the baseline rate at the median split to assess robustness (See US-3).
- **SC-005**: The total execution time of the full analysis pipeline is measured against the GitHub Actions free-tier limit. (See US-2).

## Assumptions

- The OpenNeuro ds003XXX dataset contains the required heat-pain threshold measurements for all participants included in the resting-state EEG recordings; if missing, those participants will be excluded.
- The resting-state EEG recordings in the dataset are of sufficient quality (≥ 4 minutes of valid data after artifact removal) for reliable microstate segmentation; participants failing this are excluded.
- The dataset contains no missing values for the heat-pain threshold variable; any missing values will result in participant exclusion.
- The "canonical" 4 microstate maps (A, B, C, D) are sufficient to capture the relevant dynamics; no additional microstate classes (e.g., k=5 or 6) are required for the primary analysis.
- The Elastic Net regression model (α=0.5) is appropriate for the ~30 features and sample size; no more complex non-linear models are required.
- The heat-pain threshold is measured in a consistent unit (°C) across all participants; if units vary, a conversion factor is applied.
- The analysis assumes the observational nature of the data; all findings are framed as associational, not causal, in accordance with the lack of randomization.
- The dataset size is sufficient to run a permutation test and bootstrap resamples within the 6-hour CPU limit.; if the sample size is too large, the number of resamples will be reduced to a computationally feasible level.
- The 6-hour time limit is a non-functional constraint of the CI environment; functional correctness of the model output takes precedence over meeting this limit if the dataset is exceptionally large.