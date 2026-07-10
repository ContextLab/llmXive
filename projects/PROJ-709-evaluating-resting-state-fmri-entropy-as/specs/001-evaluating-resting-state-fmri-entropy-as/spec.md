# Feature Specification: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

**Feature Branch**: `001-evaluating-resting-state-fmri-entropy-as-biomarker`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits"

## User Scenarios & Testing

### User Story 1 - Compute Parcel-wise Sample Entropy from Preprocessed fMRI (Priority: P1)

As a researcher, I need to compute the sample entropy of resting-state BOLD time series for each cortical parcel in the Schaefer 200 atlas so that I can generate the primary feature matrix for predictive modeling.

**Why this priority**: This is the core novelty of the study. Without valid entropy values, no downstream analysis or biomarker validation can occur. It is the foundational data generation step.

**Independent Test**: This can be tested by running the entropy computation pipeline on a small subset of the ADHD-200 dataset (e.g., 5 subjects) and verifying that the output is a numeric matrix of shape (5, 200) with no NaN values, and that the entropy values fall within a biologically plausible range (e.g., 0.1 to 1.5).

**Acceptance Scenarios**:

1. **Given** a preprocessed 4D fMRI NIfTI file and the Schaefer 200 parcellation mask, **When** the system computes sample entropy (m=2, r=0.2*SD) for each parcel, **Then** a 1D array of 200 entropy values is returned for that subject.
2. **Given** a subject with excessive motion artifacts (framewise displacement > 0.2mm for > 20% of volumes), **When** the system performs motion scrubbing and subsampling to N=120, **Then** the subject is excluded if the remaining time points are < 100, or included with a fixed length of 120; any parcels with zero variance are flagged and imputed.
3. **Given** the full ADHD-200 dataset, **When** the system processes all valid subjects, **Then** a single CSV file `subject_entropy_features.csv` is produced with columns `subject_id`, `parcel_01`...`parcel_200`, containing no missing values (imputed where necessary).

---

### User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

As a researcher, I need to train ridge regression and logistic ridge models using the entropy features to predict ADHD symptom severity and diagnosis, comparing them against a baseline connectivity model, so that I can determine if entropy adds predictive value.

**Why this priority**: This addresses the primary research question. It validates whether the generated features are actually useful for the intended clinical prediction task.

**Independent Test**: This can be tested by running the modeling script on the entropy feature matrix and the phenotypic CSV. The test passes if the script outputs cross-validated performance metrics (Pearson r and AUC) for three models (entropy-only, connectivity-only, combined) and reports the difference in performance.

**Acceptance Scenarios**:

1. **Given** the entropy feature matrix and ADHD symptom scores, **When** the system performs 5-fold stratified cross-validation with ridge regression, **Then** it outputs the mean Pearson correlation coefficient and standard deviation.
2. **Given** the same features, **When** the system trains a logistic ridge classifier for binary diagnosis, **Then** it outputs the mean Area Under the Curve (AUC) and standard deviation.
3. **Given** the computed connectivity baseline feature matrix (200 PCA components), **When** the system trains the same models, **Then** it outputs comparative metrics allowing a paired t-test to be calculated between the entropy model and the baseline model.

---

### User Story 3 - Perform Statistical Significance and Sensitivity Analysis (Priority: P3)

As a researcher, I need to validate the model results via permutation testing and assess the robustness of the entropy parameters (r) to ensure findings are not due to chance or arbitrary parameter choices.

**Why this priority**: This ensures methodological rigor. Without permutation testing, results are not statistically defensible; without sensitivity analysis, the specific entropy parameters (r=0.2) are arbitrary and potentially overfit.

**Independent Test**: This can be tested by running the permutation script (1,000 iterations) and the sensitivity sweep (r values: 0.15, 0.20, 0.25). The test passes if the script generates an empirical p-value < 0.05 for the primary metric and a plot showing performance stability across the r values.

**Acceptance Scenarios**:

1. **Given** the trained entropy model, **When** the system performs 1,000 permutations of the symptom labels, **Then** it calculates an empirical p-value representing the fraction of permuted models that outperform the observed model.
2. **Given** the entropy computation parameters, **When** the system sweeps the tolerance `r` across {0.15, 0.20, 0.25}, **Then** it reports the variation in cross-validated AUC/R for each value, confirming that the primary result (r=0.2) is not an outlier.
3. **Given** the set of 200 parcel-level p-values from the coefficient analysis, **When** the system applies a False Discovery Rate (FDR) correction, **Then** it outputs a list of parcels that remain significant after correction.

### Edge Cases

- **Short Time Series**: If a subject has fewer than 100 time points after motion scrubbing, the system MUST exclude the subject and log the exclusion to `exclusions.log` with the subject ID and reason.
- **Missing Phenotypic Data**: If a subject has missing ADHD-RS scores, the system MUST exclude them from the regression analysis but retain them for binary diagnosis if the diagnostic label is present.
- **Zero Variance Parcels**: If a parcel has zero variance in the time series (e.g., signal dropouts), the system MUST set the entropy to the median value of that parcel across the cohort and log the event.
- **Motion Confound**: If the correlation between entropy features and Framewise Displacement (FD) exceeds a predefined significance threshold, the system MUST flag the result as potentially confounded by motion in the final report..

## Requirements

### Functional Requirements

- **FR-001**: The system MUST compute sample entropy for every parcel in the Schaefer 200 atlas for every subject that meets the validity criteria (≥100 time points post-scrubbing), using embedding dimension m=2 and tolerance r=0.2 * standard deviation (See US-1).
- **FR-002**: The system MUST implement a stratified cross-validation loop that preserves the balance of diagnostic labels (ADHD vs. Control) in each fold. (See US-2).
- **FR-003**: The system MUST train and evaluate three distinct models: () Entropy-only, (2) Connectivity-only, and (3) Combined Entropy+Connectivity, storing all cross-validated metrics (See US-2).
- **FR-004**: The system MUST perform a sufficient number of permutation tests by shuffling outcome labels while maintaining the feature matrix structure to derive empirical p-values. (See US-3).
- **FR-005**: The system MUST execute a sensitivity analysis sweeping the entropy tolerance parameter `r` over a representative range of values and report the resulting performance variance. (See US-3).
- **FR-006**: The system MUST apply False Discovery Rate (FDR) correction to the parcel-level statistical tests to control for multiple comparisons (See US-3).
- **FR-007**: The system MUST exclude subjects with insufficient time points after motion scrubbing and log the exclusion to `exclusions.log` with the subject ID and reason. (See US-1 Edge Cases).
- **FR-008**: The system MUST compute the baseline connectivity features by calculating the full 200x200 functional connectivity matrix ([deferred] features) for each subject, then applying Principal Component Analysis (PCA) to reduce the dimensionality to 200 components (See US-2).
- **FR-009**: The system MUST impute missing or zero-variance parcel entropy values using the median entropy value of that specific parcel across the entire cohort (See US-1 Edge Cases).
- **FR-010**: The system MUST calculate the standard deviation (SD) used for the entropy tolerance parameter `r` using ONLY the time points remaining after motion scrubbing (See US-1).
- **FR-011**: The system MUST subsample all valid subjects to a fixed time series length of N=120 volumes (via truncation or interpolation) after motion scrubbing to ensure consistent SampEn length bias (See US-1).
- **FR-012**: The system MUST perform motion scrubbing by removing volumes with Framewise Displacement (FD) > 0.2mm prior to entropy calculation (See US-1).

### Key Entities

- **Subject**: An individual participant with associated fMRI data and phenotypic scores.
- **Parcel**: A specific region of interest (ROI) defined by the Schaefer 200 atlas, indexed 1-200.
- **EntropyFeature**: A scalar value representing the complexity of the BOLD time series for a specific Subject-Parcel pair.
- **PhenotypicScore**: The ADHD-RS total score and subscale scores (Inattention, Hyperactivity) for a Subject.
- **ModelPerformance**: A record containing cross-validated metrics (r, AUC) and standard deviations for a specific model configuration.
- **ConnectivityMatrix**: The full 200x200 functional connectivity matrix derived from the BOLD time series.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Success is verified if the empirical p-value for the Entropy-only model predicting continuous ADHD-RS scores is < 0.05 AND the difference in mean Pearson correlation (Δr) between the Entropy-only and Connectivity-only models is ≥ 0.05 (See US-2). *Justification: 0.05 is the community-standard minimum effect size for neuroimaging biomarker studies.*
- **SC-002**: Success is verified if the lower bound of the 95% confidence interval for the difference in AUC (ΔAUC) between the Entropy-only and Connectivity-only models is ≥ 0.05 (See US-2). *Justification: 0.05 is the community-standard minimum effect size for neuroimaging biomarker studies.*
- **SC-003**: The empirical p-value derived from 1,000 permutations for the primary model's performance metric is measured against the significance threshold of 0.05; the result must be < 0.05 to confirm non-chance performance (See US-3).
- **SC-004**: The variation in model performance (AUC/r) across the sensitivity sweep of `r` ∈ {0.15, 0.20, 0.25} is measured; success is verified if |perf(0.20) - mean(perf)| / mean(perf) ≤ 0.10 (See US-3).
- **SC-005**: The number of parcels identified as significant predictors after FDR correction is measured; a non-zero count of significant parcels indicates spatial specificity of the biomarker (See US-3).
- **SC-006**: The absolute correlation coefficient between the mean entropy feature vector and the mean Framewise Displacement (FD) vector across subjects is measured; success requires |r| < 0.3 to confirm the biomarker is not primarily a proxy for motion (See US-3 Edge Cases).

## Assumptions

- The ADHD-200 dataset on OpenNeuro contains the necessary phenotypic CSV with ADHD-RS scores and diagnostic labels for a sufficient number of subjects (n ≥ 100) to achieve statistical power for the planned regression analysis.
- Motion scrubbing (removing volumes with FD > 0.2mm) is sufficient to mitigate the confounding effects of head motion on entropy calculations, provided the remaining time series length is standardized.
- The `antropy` Python library is compatible with the CPU-only GitHub Actions runner environment and does not require GPU acceleration or CUDA libraries.
- The Schaefer 200 atlas parcellation mask aligns correctly with the MNI space of the preprocessed fMRI data provided in the dataset.
- The sample entropy computation is computationally feasible within the CI time limit for the full dataset, assuming standard CPU performance.
- The relationship between fMRI entropy and ADHD symptoms is associational, not causal, due to the observational nature of the dataset; the analysis will not claim causal inference.
- The correlation between entropy and motion (SC-006) is expected to be low (< 0.3) if the scrubbing and standardization steps are effective.