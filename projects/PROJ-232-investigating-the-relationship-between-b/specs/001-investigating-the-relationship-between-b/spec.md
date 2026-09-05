# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Feature Branch**: `001-brain-music-emotion`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST retrieve resting-state fMRI data and paired musical emotion behavioral scores from the HCP 1200 Subjects Release (specifically the subset with Music Task behavioral data) and preprocess the fMRI data to extract functional connectivity matrices.

**Why this priority**: Without clean, matched neural and behavioral data from the same subjects, no analysis can occur. This is the foundational step for the entire research question.

**Independent Test**: A researcher can run the data pipeline script on a subset of 5 subjects and verify that output files contain valid connectivity matrices (symmetric, elements in range [-1, 1], diagonal = 1.0) and corresponding behavioral scores without errors.

**Acceptance Scenarios**:

1. **Given** the HCP Music Task database is accessible, **When** the pipeline requests data for a specific subject ID, **Then** the raw fMRI NIfTI files and the paired BMRQ scores are downloaded and stored locally.
2. **Given** raw fMRI data exists, **When** fMRIPrep (CPU-only mode) is executed, **Then** the output includes motion-corrected, bandpass-filtered (0.01-0.1 Hz) data with a framewise displacement (FD) metric calculated.
3. **Given** preprocessed fMRI data and the Schaefer 200 atlas, **When** the extraction script runs, **Then** a functional connectivity matrix (Pearson correlation) is generated for each subject.

---

### User Story 2 - Network Metric Calculation and Merging (Priority: P2)

The system MUST calculate global network integration/segregation metrics (global efficiency, modularity, participation coefficient), network-specific metrics (within-network efficiency for DMN, Salience, and Visual networks), and edge-level connectivity strengths, then merge these with the BMRQ scores for subjects with complete data.

**Why this priority**: This transforms raw connectivity data into the specific predictors required to test the research hypothesis. Including network-specific and edge-level features addresses the methodological need for specificity beyond global scalars.

**Independent Test**: The system can process a single subject's connectivity matrix and output a JSON object containing the keys `global_efficiency`, `modularity`, `participation_coefficient`, `network_efficiency`, and `edge_strength`, which can be successfully joined with a mock behavioral score.

**Acceptance Scenarios**:

1. **Given** a functional connectivity matrix, **When** the NetworkX/bctpy analysis runs, **Then** global efficiency, modularity, participation coefficient, network-specific efficiencies, and edge strengths are calculated and stored.
2. **Given** a dataset of subjects with both connectivity features and BMRQ scores, **When** the merge operation executes, **Then** the final analysis dataset contains only subjects with non-missing values for all variables.
3. **Given** the merged dataset, **When** a summary statistic is requested, **Then** the system reports the number of valid subjects (N) and the distribution of the behavioral scores.

---

### User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

The system MUST perform partial correlation analyses controlling for covariates and fit a regularized linear regression model to predict BMRQ total scores, applying multiple comparison corrections.

**Why this priority**: This directly addresses the research question by quantifying the relationship between brain dynamics and musical emotion perception (trait) while adhering to statistical rigor.

**Independent Test**: The analysis script runs on the full dataset, produces a CSV of correlation coefficients with p-values, and generates a scatter plot of predicted vs. actual BMRQ scores with a regression line and R² annotation.

**Acceptance Scenarios**:

1. **Given** the merged dataset, **When** partial correlation is run, **Then** correlation coefficients between network metrics and BMRQ scores are reported, controlling for age, sex, and FD.
2. **Given** the predictor matrix, **When** Ridge/Lasso regression is fitted with 5-fold cross-validation, **Then** the model outputs the explained variance ($R^2$) and the most predictive connectivity features.
3. **Given** a set of hypothesis tests, **When** multiple comparison correction is applied, **Then** all reported p-values are adjusted using FDR (q<0.05).

---

### Edge Cases

- What happens when a subject has excessive motion (FD > 0.5 mm) during scanning? -> The pipeline must exclude this subject from the final analysis dataset.
- How does the system handle missing behavioral data for a subject who has fMRI data? -> The merge operation must exclude subjects with incomplete data to avoid listwise deletion bias or imputation errors.
- What if the HCP data download fails for a specific subject? -> The pipeline must log the error and continue with remaining subjects rather than crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data and paired BMRQ scores from the HCP 1200 Subjects Release (Music Task subset), ensuring data integrity via checksums (See US-1).
- **FR-002**: System MUST preprocess fMRI data using fMRIPrep in CPU-only mode, applying motion correction and bandpass filtering (0.01-0.1 Hz) to generate cleaned time series (See US-1).
- **FR-003**: System MUST extract time series from the Schaefer 200 atlas parcellation and compute Pearson correlation functional connectivity matrices (See US-1, US-2).
- **FR-004**: System MUST calculate global efficiency, modularity, participation coefficient, network-specific efficiency (DMN, Salience, Visual), and edge-level connectivity strengths using CPU-tractable graph theory libraries (NetworkX/bctpy) (See US-2).
- **FR-005**: System MUST perform partial correlation analyses controlling for age, sex, and framewise displacement, and fit a regularized linear regression model with 5-fold cross-validation to predict BMRQ total scores (See US-3).
- **FR-006**: System MUST apply False Discovery Rate (FDR) correction (q<0.05) to all hypothesis tests involving multiple comparisons (See US-3).

### Key Entities

- **Subject**: An individual participant containing a unique ID, demographic data (age, sex), fMRI data, and behavioral scores.
- **ConnectivityMatrix**: A 200x200 symmetric matrix representing functional connectivity strength between brain regions for a specific subject.
- **NetworkMetrics**: A record containing derived graph theory values (global efficiency, modularity, participation coefficient, network-specific efficiencies, edge strengths) for a subject.
- **BehavioralScore**: The BMRQ total score representing an individual's musical reward sensitivity (trait).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation strength (Pearson's r) between global network integration metrics and BMRQ scores is measured against the null hypothesis of no correlation (r=0) (See US-3).
- **SC-002**: The explained variance ($R^2$) of the regularized regression model predicting BMRQ total scores is measured against the baseline of a null model (intercept only) (See US-3).
- **SC-003**: The false discovery rate of significant findings is measured against the threshold of q<0.05 after FDR correction (See US-3).
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the free-tier GitHub Actions limit (7 GB RAM, 2 CPU cores, 6 hours) to ensure feasibility (See US-1, US-2).
- **SC-005**: The sample size (N) of the final analysis dataset is measured against the power requirements to detect an effect size of r ≥ 0.20 with a power ≥ 0.80 and significance level α = 0.05 (See US-2).

## Assumptions

- The Human Connectome Project (HCP) Subjects Release contains a specific subset of subjects with paired resting-state fMRI and BMRQ (or equivalent Music Reward) behavioral data, accessible via the HCP database or a cited linked dataset (e.g., HCP Music Task data).
- fMRIPrep can run successfully in CPU-only mode on the GitHub Actions free tier without requiring CUDA or GPU acceleration.
- The Schaefer 200 atlas is compatible with the HCP data preprocessing pipeline and provides a valid parcellation for the brain regions of interest.
- The computational load of graph theory metrics on 200x200 matrices fits within the 7 GB RAM limit of the CI runner.
- The study design is observational; therefore, all findings will be framed as associational rather than causal.
- Effect sizes for resting-state connectivity predicting individual differences in musical traits are expected to be small to moderate, consistent with current literature in neuroaesthetics and connectomics.