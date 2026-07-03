# Feature Specification: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Does the amplitude (standard deviation) of the resting‑state fMRI global signal predict individual differences in self‑reported mind‑wandering frequency as measured by the Mind‑Wandering Questionnaire (MWQ)?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Metric Computation (Priority: P1)

**Researcher** downloads the HCP 1200-subject resting-state fMRI data and Mind-Wandering Questionnaire (MWQ) scores, computes the global signal amplitude (standard deviation) for each subject, and exports a clean CSV containing the predictor, outcome, and covariates.

**Why this priority**: This is the foundational step; without valid, reproducible data extraction and metric computation, no modeling or statistical inference can occur. It delivers the core dataset required for the entire study.

**Independent Test**: Can be fully tested by running the ingestion script on a small subset of HCP data (e.g., a limited number of subjects) and verifying that the output CSV contains the expected columns (Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, FD, DVARS) with no missing values and correct data types.

**Acceptance Scenarios**:

1. **Given** a directory containing minimally preprocessed HCP resting-state fMRI runs and a CSV of MWQ scores, **When** the ingestion script executes, **Then** it produces a single CSV file where every row corresponds to a unique subject with non-null values for Global_Signal_SD and MWQ_Score.
2. **Given** a subject with missing fMRI runs, **When** the ingestion script executes, **Then** that subject is excluded from the output CSV with a log entry documenting the exclusion reason.
3. **Given** the computed global signal time series, **When** the standard deviation is calculated, **Then** the value matches a manual calculation on a short sample of the time series within a tolerance of 0.0001.

---

### User Story 2 - Association Modeling and Baseline Comparison (Priority: P2)

**Researcher** runs a ridge regression model to predict MWQ scores from global signal amplitude (adjusted for covariates), compares the performance against a null model (permuted outcomes), and generates a report with Pearson r, MAE, and p-values.

**Why this priority**: This directly addresses the primary research question (association between global signal and mind-wandering). It delivers the core statistical evidence required to validate or refute the hypothesis.

**Independent Test**: Can be fully tested by running the modeling script on a synthetic dataset with a known correlation (r=0.3) and verifying that the reported out-of-fold Pearson r falls within the expected range and that the null model performance is near zero.

**Acceptance Scenarios**:

1. **Given** a dataset of 200 subjects with valid global signal and MWQ scores, **When** the ridge regression pipeline executes with 5-fold cross-validation, **Then** it outputs a JSON report containing the mean out-of-fold MAE, Pearson r, and R².
2. **Given** the same dataset with permuted MWQ scores, **When** the null model pipeline executes, **Then** the observed model's MAE is lower than the null model's MAE in at least 95% of 100 permutation iterations (p < 0.05).
3. **Given** a subject with extreme motion artifacts (FD > 0.5mm), **When** the covariate regression step executes, **Then** the subject's residuals are included in the final model but flagged in the log for manual review.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Researcher** validates the findings by repeating the analysis with alternative metrics (variance vs. SD), adjusting for additional confounds, and sweeping the regularization parameter to ensure the correlation is not an artifact of a specific threshold.

**Why this priority**: This ensures the scientific rigor and reproducibility of the findings, addressing potential methodological biases and confirming that the result is robust to reasonable variations in the analysis pipeline.

**Independent Test**: Can be fully tested by running the robustness script which automatically generates three alternative model variants and a sensitivity sweep, then verifying that the reported correlation coefficients remain above a minimal threshold in any variant.

**Acceptance Scenarios**:

1. **Given** the primary model results, **When** the robustness script runs with global-signal variance instead of standard deviation, **Then** the reported Pearson r remains within ±0.05 of the primary model's r.
2. **Given** the primary model results, **When** the sensitivity analysis sweeps the regularization parameter (α) across {0.01, 0.1, 1.0, 10.0}, **Then** the model's MAE does not increase by more than a modest margin compared to the optimal α.
3. **Given** the primary model results, **When** the analysis is repeated with an additional control predictor (average framewise displacement), **Then** the partial correlation between global signal and MWQ remains statistically significant (p < 0.05).

---

### Edge Cases

- **Missing Data**: What happens when a subject has fMRI data but no MWQ score (or vice versa)? The system must exclude such subjects and log the count of excluded pairs.
- **Motion Artifacts**: How does the system handle subjects with excessive motion (FD > 0.5mm)? The system must flag these subjects in the log and exclude them if the mean FD exceeds 0.5mm (See FR-008).
- **Zero Variance**: What happens if the global signal time series has zero variance for a subject? The system must raise a warning and exclude the subject from analysis, as standard deviation is undefined.
- **Null Results**: What happens if the observed correlation is not statistically significant? The system must still generate a full report with the null distribution and p-value, explicitly stating the null finding.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse minimally preprocessed HCP resting-state fMRI runs and MWQ scores for N subjects with complete data, where N is the number of available subjects (target study size sufficient for statistical power). (See US-1).
- **FR-002**: System MUST compute the voxel-wise mean time series (global signal) and calculate its standard deviation per run, then average across runs for each subject (See US-1).
- **FR-003**: System MUST include standard motion confounds (FD, DVARS) and demographic covariates (age, sex) as predictors in the ridge regression model alongside the global-signal metric; the outcome (MWQ) MUST remain raw and unadjusted (See US-2).
- **FR-004**: System MUST perform ridge regression with nested k-fold cross-validation to tune the regularization parameter (α) and record out-of-fold performance metrics (Pearson r, MAE, R²), using the model structure Y ~ Global_Signal_SD + FD + DVARS + Age + Sex (See US-2).
- **FR-005**: System MUST generate a null distribution of performance metrics by training the same ridge pipeline on a set of permuted MWQ score vectors and calculate the empirical p-value as the proportion of null MAEs that are less than or equal to the observed MAE (See US-2).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the regularization parameter (α) over a range of values spanning multiple orders of magnitude. and report how the MAE varies across these values (See US-3).
- **FR-007**: System MUST repeat the primary analysis using global-signal variance instead of standard deviation and report the resulting correlation coefficient (See US-3).
- **FR-008**: System MUST exclude subjects from analysis if the mean framewise displacement (FD) exceeds 0.5mm and log the exclusion count (See Edge Cases).
- **FR-009**: System MUST validate that every subject in the dataset has both valid fMRI data and a corresponding MWQ score before processing; if a pair is missing, the subject is excluded and logged (See US-1).

### Key Entities

- **Subject**: Represents a single participant in the HCP dataset, containing attributes: Subject_ID, Age, Sex, MWQ_Score, Global_Signal_SD, Global_Signal_Variance, Mean_FD, Mean_DVARS.
- **Run**: Represents a single resting-state fMRI scan session for a subject, containing attributes: Run_ID, Subject_ID, Time_Series (array of voxel-wise means), Duration_Samples.
- **Model_Result**: Represents the output of a single modeling iteration, containing attributes: Model_Type (ridge/null), Alpha_Value, Out_Of_Fold_MAE, Out_Of_Fold_Pearson_r, Out_Of_Fold_R2, Permutation_Index (if null).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between global-signal amplitude and MWQ scores is measured against the null distribution generated by a permutation of the MWQ scores (See US-2).
- **SC-002**: The out-of-fold MAE of the ridge regression model is measured against the null distribution of MAEs to determine statistical significance via an empirical p-value (p < 0.05) (See US-2).
- **SC-003**: The stability of the correlation coefficient is measured against the variation observed when using global-signal variance instead of standard deviation (See US-3).
- **SC-004**: The robustness of the model performance is measured against the change in MAE when sweeping the regularization parameter (α) over a range of representative values (See US-3).
- **SC-005**: The independence of the global-signal effect is measured against the partial correlation after controlling for mean framewise displacement (See US-3).

## Assumptions

- The HCP large-scale release contains minimally preprocessed resting-state fMRI data (multiple runs of [deferred] each) and corresponding MWQ scores for a sufficient number of subjects to achieve the target study size.
- The global signal amplitude (standard deviation) is a valid and computable metric from the preprocessed fMRI data without requiring additional denoising steps beyond motion confound regression.
- The MWQ scores are normally distributed or sufficiently close to normal to support parametric statistical testing (Pearson correlation, t-tests).
- The computational resources of a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, ≤6 h) are sufficient to process the available subjects, compute global signals, and run the ridge regression with 100 permutations.
- The HCP data access credentials (if required) are available to the CI environment via environment variables or a pre-configured token.
- The relationship between global signal amplitude and mind-wandering is associative, not causal, given the observational nature of the data (no random assignment).
- The sample size of available subjects provides adequate power to detect a modest correlation (r ≈ 0.2–0.3) with 80% power at α = 0.05 (power calculation deferred to implementation phase).
- The regularization parameter (α) for ridge regression can be effectively tuned via nested cross-validation without requiring a separate validation set.
- The motion confounds (FD, DVARS) provided by HCP are sufficient to control for residual motion artifacts in the global signal.
- The demographic covariates (age, sex) are available in the HCP dataset and can be used to adjust the model predictors.