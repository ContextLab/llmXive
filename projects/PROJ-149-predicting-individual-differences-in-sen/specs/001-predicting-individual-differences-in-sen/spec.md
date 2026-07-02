# Feature Specification: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

**Feature Branch**: `001-predict-sensory-speed-from-eeg`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra"

## User Scenarios & Testing

### User Story 1 - Compute Band-Power Features and Behavioral Metrics (Priority: P1)

The system must successfully ingest raw resting-state EEG data and behavioral task logs, preprocess them to remove artifacts, extract canonical frequency band power spectra from continuous 5-minute epochs using 4-second windows, and compute median reaction times for each participant.

**Why this priority**: This is the foundational data pipeline. Without clean, aligned features (EEG power) and outcomes (RT), no modeling or statistical inference can occur. It delivers the core dataset required for the research question.

**Independent Test**: Can be fully tested by running the preprocessing script on a subset of the PhysioNet dataset and verifying that the output CSV contains one row per participant with columns for delta, theta, alpha, beta, gamma power, and median RT, with no null values.

**Acceptance Scenarios**:

1. **Given** a raw EEG file and corresponding task log for a participant, **When** the preprocessing pipeline runs, **Then** the system outputs a single row with computed band powers and median RT, excluding the participant only if >30% of channels are rejected due to noise (hard stop).
2. **Given** a dataset with 50 participants, **When** the pipeline processes all files, **Then** the resulting feature table contains exactly 50 rows, and the distribution of median RTs falls within the physiologically plausible range of 150ms to 1000ms.
3. **Given** a participant with severe ocular artifacts, **When** ICA cleaning is applied, **Then** the resulting alpha-band power spectrum shows reduced high-frequency noise compared to the uncleaned spectrum, and the participant is retained in the final table.

---

### User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

The system must fit linear regression and LASSO models to predict reaction time from EEG relative band powers, perform cross-validation, and compute Pearson correlations with Bonferroni correction for 6 bands.

**Why this priority**: This addresses the core research hypothesis. It transforms the prepared data into statistical evidence, determining if a relationship exists between neural oscillations and processing speed.

**Independent Test**: Can be fully tested by executing the modeling script on the generated feature table and verifying that the output includes model coefficients, R² scores, p-values for correlations, and a flag indicating whether the null hypothesis is rejected at the Bonferroni-corrected threshold.

**Acceptance Scenarios**:

1. **Given** the prepared feature table, **When** the regression model is trained with 5-fold cross-validation, **Then** the system reports the mean R² and RMSE across folds, and the test set R² is within ±0.05 of the cross-validated mean.
2. **Given** the correlation matrix between relative band powers and RT, **When** the significance test runs, **Then** the system applies Bonferroni correction for 6 tests (bands) and reports adjusted p-values, flagging any result with p < 0.0083 (0.05/6) as significant.
3. **Given** a scenario where alpha power is the strongest predictor, **When** the LASSO model is fit, **Then** the non-zero coefficients are restricted to alpha and potentially beta bands, while other bands are shrunk to zero.

---

### User Story 3 - Perform Robustness Checks and Sensitivity Analysis (Priority: P3)

The system must re-run the analysis with alternative parameters (epoch length, ICA on/off, window size) and sweep the significance threshold to demonstrate result stability.

**Why this priority**: This ensures the findings are not artifacts of specific preprocessing choices or arbitrary statistical cutoffs, satisfying methodological soundness requirements for publication.

**Independent Test**: Can be fully tested by running the robustness script and verifying that the final report includes a table comparing R² and p-values across different window lengths (e.g., 2s vs 4s) and a sensitivity plot showing how the number of significant correlations changes as the p-value threshold varies from 0.01 to 0.10.

**Acceptance Scenarios**:

1. **Given** the primary analysis results (4-second windows), **When** the robustness check runs with 2-second windows, **Then** the change in R² is less than 0.05 compared to the 4-second window baseline.
2. **Given** the primary correlation p-value of 0.03, **When** the sensitivity analysis sweeps the threshold from 0.01 to 0.10, **Then** the system reports the exact threshold at which the result becomes non-significant (e.g., "Significant at p<0.04, non-significant at p<0.03").
3. **Given** the analysis without ICA cleaning, **When** compared to the ICA-cleaned analysis, **Then** the system reports the percentage difference in alpha-band power means and flags the result if the difference exceeds 20% as a high-sensitivity indicator.

### Edge Cases

- What happens when a participant's EEG recording is shorter than the minimum 5-minute epoch requirement? (System excludes participant with a log entry).
- How does the system handle a participant with missing behavioral data (no RT logs)? (System excludes participant from the feature table).
- What if the dataset contains no significant correlation after Bonferroni correction? (System reports the null result with effect sizes and confidence intervals, explicitly stating the hypothesis was not supported).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and cache the PhysioNet EEG Motor Movement/Imagery Dataset (or equivalent public resting-state EEG dataset with RT tasks) and verify file integrity before processing. (See US-1)
- **FR-002**: System MUST apply a band-pass filter (1–40 Hz) and notch filter (50/60 Hz) to raw EEG data, and reject channels with variance exceeding 3 standard deviations from the mean variance across all channels in the current session. If >30% of channels are rejected for a participant, the participant MUST be excluded from further analysis. (See US-1)
- **FR-003**: System MUST compute Welch’s Power Spectral Density (PSD) on continuous 5-minute epochs using 4-second windows with [deferred] overlap and aggregate power into delta, theta, alpha, low-beta, high-beta, and gamma bands. (See US-1)
- **FR-004**: System MUST extract median reaction time per participant from task logs. Outliers (RT < 100ms or RT > 2000ms) MUST be excluded BEFORE calculating the median. The participant is retained only if ≥70% of trials remain after outlier exclusion. (See US-1)
- **FR-005**: System MUST fit a multiple linear regression model and a LASSO model using 5-fold cross-validation, tuning the regularization parameter lambda to minimize RMSE. The goal is to predict individual differences within the dataset (cross-validation), not generalizable prediction to a new population. (See US-2)
- **FR-006**: System MUST perform Pearson correlation tests between each relative band power (band/total) and median RT, applying Bonferroni correction for 6 bands. (See US-2)
- **FR-007**: System MUST execute a permutation test with 10,000 shuffles to assess the significance of the regression model's R² value. (See US-2)
- **FR-008**: System MUST re-run the full analysis pipeline with an alternative window length (e.g., 2 seconds) and without ICA cleaning to generate robustness metrics. The 'without ICA' run is a specific robustness test only and does not replace the primary ICA-cleaned result, which remains the mandatory standard per Constitution Principle VI. (See US-3)
- **FR-009**: System MUST generate a sensitivity analysis report sweeping the significance threshold (p-value) from 0.01 to 0.10 in steps of 0.01 and recording the count of significant correlations at each step. (See US-3)
- **FR-010**: System MUST calculate relative power (band power divided by total power across 1-40 Hz) for all bands to control for total power confound. (See US-2)
- **FR-011**: System MUST perform a post-hoc power analysis to estimate the sample size required to detect an effect size of R² = 0.10 with power ≥ 0.80, and report this alongside the results. (See US-2)
- **FR-012**: System MUST explore non-linear interactions (e.g., polynomial terms for alpha and beta) as a secondary analysis and report if the non-linear model explains significantly more variance than the linear model (p < 0.05). (See US-2)

### Key Entities

- **Participant**: Represents a unique individual in the dataset, linked to one EEG recording and one behavioral task log.
- **EEGFeature**: Represents the aggregated relative power values for a specific frequency band (e.g., alpha) across specific channels for a participant.
- **BehavioralMetric**: Represents the median reaction time and standard deviation for a participant's task performance.
- **ModelResult**: Represents the output of a regression or correlation test, including coefficients, R², p-values, and confidence intervals.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Report the Adjusted R² value for the linear model predicting reaction time from EEG features. (See US-2)
- **SC-002**: Report the Bonferroni-corrected p-value for the alpha-band correlation with reaction time. (See US-2)
- **SC-003**: Report the stability of the model performance (R²) by comparing the variation observed when changing window lengths (e.g., 2s vs 4s). (See US-3)
- **SC-004**: Report the robustness of the significance finding by identifying the exact p-value threshold at which the result becomes non-significant via sensitivity analysis. (See US-3)
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier limits (≤6 hours total runtime, ≤7 GB RAM usage). (See US-1)

## Assumptions

- The PhysioNet "EEG Motor Movement/Imagery Dataset" (or equivalent public dataset) contains both resting-state EEG recordings and a simple reaction-time task for the same participants.
- The resting-state EEG recordings are of sufficient length (≥ 5 minutes) to generate stable power spectral density estimates with 4-second windows.
- The reaction-time task logs are in a machine-readable format (e.g., CSV, JSON) that can be parsed to extract individual trial latencies.
- The analysis will be performed using Python libraries (MNE-Python, scikit-learn, pandas) that are compatible with CPU-only execution and do not require GPU acceleration.
- The sample size in the public dataset is sufficient to perform a 80/20 train/test split and 5-fold cross-validation with at least 30 participants in the test set for reliable statistical testing.
- The "sensory processing speed" is adequately proxied by the median reaction time from the simple visual/auditory task included in the dataset.
- The Bonferroni correction for 6 multiple comparisons is appropriate for the number of frequency bands tested, and no further hierarchical correction is required.
- The dataset does not contain missing values for the primary outcome (reaction time) for the majority of participants; participants with missing RT data will be excluded from the analysis.
- The primary goal is to predict individual differences within the dataset (cross-validation), not to generalize to a new population or task.