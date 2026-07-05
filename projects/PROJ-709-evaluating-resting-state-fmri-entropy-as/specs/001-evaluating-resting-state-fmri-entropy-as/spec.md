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
2. **Given** a subject with excessive motion artifacts (framewise displacement > 0.5mm for > 20% of volumes), **When** the system computes entropy, **Then** the specific parcel time series affected are flagged, but the computation proceeds for remaining valid parcels without crashing.
3. **Given** the full ADHD-200 dataset, **When** the system processes all subjects, **Then** a single CSV file `subject_entropy_features.csv` is produced with columns `subject_id`, `parcel_01`...`parcel_200`, containing no missing values.

---

### User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

As a researcher, I need to train ridge regression and logistic ridge models using the entropy features to predict ADHD symptom severity and diagnosis, comparing them against a baseline connectivity model, so that I can determine if entropy adds predictive value.

**Why this priority**: This addresses the primary research question. It validates whether the generated features are actually useful for the intended clinical prediction task.

**Independent Test**: This can be tested by running the modeling script on the entropy feature matrix and the phenotypic CSV. The test passes if the script outputs cross-validated performance metrics (Pearson r and AUC) for three models (entropy-only, connectivity-only, combined) and reports the difference in performance.

**Acceptance Scenarios**:

1. **Given** the entropy feature matrix and ADHD symptom scores, **When** the system performs 5-fold stratified cross-validation with ridge regression, **Then** it outputs the mean Pearson correlation coefficient and standard deviation.
2. **Given** the same features, **When** the system trains a logistic ridge classifier for binary diagnosis, **Then** it outputs the mean Area Under the Curve (AUC) and standard deviation.
3. **Given** a baseline connectivity feature matrix, **When** the system trains the same models, **Then** it outputs comparative metrics allowing a paired t-test to be calculated between the entropy model and the baseline model.

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

- What happens when a subject's fMRI scan has fewer than 100 time points after preprocessing? (System must skip this subject or impute, but must log the exclusion).
- How does the system handle subjects in the ADHD-200 dataset who have missing ADHD-RS scores? (System must exclude them from the regression analysis but retain them for binary diagnosis if the diagnostic label is present).
- How does the system handle parcels with zero variance in the time series (e.g., signal dropouts)? (System must detect zero variance and set entropy to 0 or NaN, excluding them from the feature matrix).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST compute sample entropy for every parcel in the Schaefer 200 atlas for every valid subject in the dataset, using embedding dimension m=2 and tolerance r=0.2 * standard deviation (See US-1).
- **FR-002**: The system MUST implement a 5-fold stratified cross-validation loop that preserves the balance of diagnostic labels (ADHD vs. Control) in each fold (See US-2).
- **FR-003**: The system MUST train and evaluate three distinct models: (1) Entropy-only, (2) Connectivity-only, and (3) Combined Entropy+Connectivity, storing all cross-validated metrics (See US-2).
- **FR-004**: The system MUST perform 1,000 permutation tests by shuffling outcome labels while maintaining the feature matrix structure to derive empirical p-values (See US-3).
- **FR-005**: The system MUST execute a sensitivity analysis sweeping the entropy tolerance parameter `r` over the set {0.15, 0.20, 0.25} and report the resulting performance variance (See US-3).
- **FR-006**: The system MUST apply False Discovery Rate (FDR) correction to the parcel-level statistical tests to control for multiple comparisons (See US-3).

### Key Entities

- **Subject**: An individual participant with associated fMRI data and phenotypic scores.
- **Parcel**: A specific region of interest (ROI) defined by the Schaefer 200 atlas, indexed 1-200.
- **EntropyFeature**: A scalar value representing the complexity of the BOLD time series for a specific Subject-Parcel pair.
- **PhenotypicScore**: The ADHD-RS total score and subscale scores (Inattention, Hyperactivity) for a Subject.
- **ModelPerformance**: A record containing cross-validated metrics (r, AUC) and standard deviations for a specific model configuration.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The mean cross-validated Pearson correlation (r) of the Entropy-only model predicting continuous ADHD-RS scores is measured against the Connectivity-only baseline; the goal is a statistically significant improvement (p < 0.05) or a difference ≥ 0.05 (See US-2).
- **SC-002**: The mean cross-validated AUC for binary diagnosis using the Entropy-only model is measured against the Connectivity-only baseline; the goal is a ΔAUC ≥ 0.05 (See US-2).
- **SC-003**: The empirical p-value derived from 1,000 permutations for the primary model's performance metric is measured against the significance threshold of 0.05; the result must be < 0.05 to confirm non-chance performance (See US-3).
- **SC-004**: The variation in model performance (AUC/r) across the sensitivity sweep of `r` ∈ {0.15, 0.20, 0.25} is measured; the result must show that the performance at r=0.20 is not an outlier (i.e., within 10% of the mean of the sweep) to justify the parameter choice (See US-3).
- **SC-005**: The number of parcels identified as significant predictors after FDR correction is measured; a non-zero count of significant parcels indicates spatial specificity of the biomarker (See US-3).

## Assumptions

- The ADHD-200 dataset on OpenNeuro contains the necessary phenotypic CSV with ADHD-RS scores and diagnostic labels for a sufficient number of subjects (n ≥ 100) to achieve statistical power for the planned regression analysis, though the exact power calculation is deferred to the implementation phase.
- The minimally preprocessed fMRI data (4mm isotropic) provided by OpenNeuro is of sufficient quality to compute sample entropy without requiring additional custom motion scrubbing beyond the standard pipeline.
- The `antropy` Python library is compatible with the CPU-only GitHub Actions runner environment and does not require GPU acceleration or CUDA libraries.
- The Schaefer 200 atlas parcellation mask aligns correctly with the MNI space of the preprocessed fMRI data provided in the dataset.
- The sample entropy computation is computationally feasible within the 6-hour CI time limit for the full dataset, assuming standard CPU performance.
- The relationship between fMRI entropy and ADHD symptoms is associational, not causal, due to the observational nature of the dataset; the analysis will not claim causal inference.
