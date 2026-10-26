# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Feature Branch**: `001-brain-music-emotion`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) (User Story ID: US-1)

The system MUST retrieve resting‑state fMRI data from the Human Connectome Project (HCP) extensive subject release and retrieve Music Emotion Rating (MER) scores from an external publicly available dataset (e.g., the Barcelona Music Reward Questionnaire dataset). It MUST match subjects across the two datasets using the unique HCP Subject ID (or, when the ID is not directly available, via a deterministic matching key based on demographic attributes). The matched dataset is then preprocessed to extract functional connectivity matrices.

**Why this priority**: Without clean, matched neural and behavioral data from the same subjects, no analysis can occur. This is the foundational step for the entire research question.

**Independent Test**: A researcher can run the data pipeline script on a representative subset of subjects and verify that output files contain valid connectivity matrices (symmetric, elements in range [-1, 1], diagonal = 1.0) and corresponding MER scores without errors.

**Acceptance Scenarios**:

1. **Given** the HCP data repository and the external MER dataset are accessible, **When** the pipeline requests data for a specific subject ID, **Then** the raw fMRI NIfTI files and the paired MER score for that same subject are downloaded and stored locally.
2. **Given** raw fMRI data exists, **When** fMRIPrep (CPU‑only mode) is executed, **Then** the output includes motion‑corrected, bandpass‑filtered (low‑frequency cutoff to 0.1 Hz) data with a framewise displacement (FD) metric calculated.
3. **Given** preprocessed fMRI data and the Schaefer atlas, **When** the extraction script runs, **Then** a functional connectivity matrix (Pearson correlation) is generated for each subject.

---

### User Story 2 - Network Metric Calculation and Merging (Priority: P2) (User Story ID: US-2)

The system MUST calculate global network integration/segregation metrics (global efficiency, modularity, participation coefficient), network‑specific metrics (within‑network efficiency for DMN, Salience, Visual, and Reward networks), and edge‑level connectivity strengths, then merge these with the MER scores for subjects with complete data.

**Why this priority**: This transforms raw connectivity data into the specific predictors required to test the research hypothesis. Including network‑specific and edge‑level features addresses the methodological need for specificity beyond global scalars.

**Independent Test**: The system can process a single subject's connectivity matrix and output a JSON object containing the keys `global_efficiency`, `modularity`, `participation_coefficient`, `network_efficiency`, and `edge_strength`, which can be successfully joined with a mock MER score.

**Acceptance Scenarios**:

1. **Given** a functional connectivity matrix, **When** the NetworkX/bctpy analysis runs, **Then** global efficiency, modularity, participation coefficient, network‑specific efficiencies (including Reward), and edge strengths are calculated and stored.
2. **Given** a dataset of subjects with both connectivity features and MER scores, **When** the merge operation executes, **Then** the final analysis dataset contains only subjects with non‑missing values for all variables.
3. **Given** the merged dataset, **When** a summary statistic is requested, **Then** the system reports the number of valid subjects (N) and the distribution of the behavioral scores.

---

### User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3) (User Story ID: US-3)

The system MUST perform partial correlation analyses controlling for covariates and fit a regularized linear regression model to predict MER total scores, applying multiple comparison corrections.

**Why this priority**: This directly addresses the research question by quantifying the relationship between brain dynamics and musical emotion perception (trait) while adhering to statistical rigor.

**Independent Test**: The analysis script runs on the full dataset, produces a CSV of correlation coefficients with p‑values, and generates a scatter plot of predicted vs. actual MER scores with a regression line and R² annotation.

**Acceptance Scenarios**:

1. **Given** the merged dataset, **When** partial correlation is run, **Then** correlation coefficients between network metrics and MER scores are reported, controlling for age, sex, and FD.
2. **Given** the predictor matrix, **When** Ridge/Lasso regression is fitted with k‑fold cross‑validation (with an appropriate number of folds), **Then** the model outputs the explained variance (R²) and the most predictive connectivity features.
3. **Given** a set of hypothesis tests, **When** multiple comparison correction is applied, **Then** all reported p‑values are adjusted using FDR (q < 0.05).

---

### User Story 4 - Resource Monitoring and Reporting (Priority: P2) (User Story ID: US-4)

The system MUST monitor RAM and CPU usage during data download, preprocessing, and analysis phases, and must generate a report indicating whether usage stays within the GitHub Actions free‑tier limits (≤ 7 GB RAM, ≤ 6 hours runtime, modest CPU core count). Logs of any exceedances must be recorded.

**Why this priority**: Ensures that the pipeline is feasible to run on the intended CI infrastructure and prevents hidden resource failures.

**Independent Test**: Run the full pipeline on the CI runner; after completion, inspect the generated resource‑usage report to confirm that reported RAM and CPU time are within the specified limits.

**Acceptance Scenarios**:

1. **Given** the pipeline is executing, **When** the monitoring module records resource metrics, **Then** a JSON summary of peak RAM, total CPU time, and wall‑clock time is produced.
2. **Given** the summary exceeds any limit, **When** the pipeline finishes, **Then** an error flag is raised and the log contains a clear message about which limit was breached.

---

### User Story 5 - Power Analysis and Sample Size Planning (Priority: P2) (User Story ID: US-5)

Prior to the main statistical analysis, the system MUST compute the required sample size to detect a correlation of at least r = 0.20 with statistical power ≥ 0.80 at α = 0.05, based on the number of subjects remaining after matching. The computed required N and the actual N must be reported.

**Why this priority**: Guarantees that the study is adequately powered to detect the hypothesized effect, addressing methodological rigor.

**Independent Test**: After matching, the power‑analysis script outputs a table with required N and actual N; the researcher can verify that actual N ≥ required N or note the shortfall.

**Acceptance Scenarios**:

1. **Given** the matched subject list, **When** the power‑analysis function runs, **Then** it returns the minimum N needed for r ≥ 0.20, power ≥ 0.80, α = 0.05.
2. **Given** the required N, **When** the actual matched N is computed, **Then** the report states whether the dataset meets the power requirement.

---

### Edge Cases

- What happens when a subject has excessive motion (FD > 0.5 mm) during scanning? → The pipeline must exclude this subject from the final analysis dataset.
- How does the system handle missing behavioral data for a subject who has fMRI data? → The merge operation must exclude subjects with incomplete data to avoid listwise deletion bias or imputation errors.
- What if the HCP data download fails for a specific subject? → The pipeline must log the error and continue with remaining subjects rather than crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download resting‑state fMRI data from the HCP Subjects Release. and download Music Emotion Rating (MER) scores from an external publicly available dataset (e.g., Barcelona Music Reward Questionnaire). The system MUST match subjects across datasets using the unique HCP Subject ID (or a deterministic matching key) and verify data integrity via checksums (See US-1).
- **FR-002**: System MUST preprocess the downloaded HCP resting‑state fMRI data using fMRIPrep in CPU‑only mode, applying motion correction and bandpass filtering (0.01–0.1 Hz) to generate cleaned time series (See US-1).
- **FR-003**: System MUST extract time series from the Schaefer atlas with a high‑resolution regional parcellation. applied to the preprocessed fMRI data and compute Pearson correlation functional connectivity matrices for each subject (See US-1, US-2).
- **FR-004**: System MUST calculate global efficiency, modularity, participation coefficient, network‑specific efficiency for DMN, Salience, Visual, and Reward (nucleus accumbens & ventral striatum) networks, and edge‑level connectivity strengths using CPU‑tractable graph theory libraries (NetworkX/bctpy) (See US-2).
- **FR-005**: System MUST perform partial correlation analyses controlling for age, sex, and framewise displacement, and fit a regularized linear regression model with k‑fold cross‑validation to predict MER total scores (See US-3).
- **FR-006**: System MUST apply False Discovery Rate (FDR) correction (q < 0.05) to all hypothesis tests involving multiple comparisons (See US-3).

### Key Entities

- **Subject**: An individual participant containing a unique ID, demographic data (age, sex), fMRI data, and behavioral scores.
- **ConnectivityMatrix**: A 200×200 symmetric matrix representing functional connectivity strength between brain regions for a specific subject.
- **NetworkMetrics**: A record containing derived graph theory values (global efficiency, modularity, participation coefficient, network‑specific efficiencies, edge strengths) for a subject.
- **BehavioralScore**: The MER total score representing an individual's musical emotion perception (trait).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation strength (Pearson's r) between global network integration metrics and MER scores is measured against the null hypothesis of no correlation (r = 0) (See US-3).
- **SC-002**: The explained variance (R²) of the regularized regression model predicting MER total scores is measured against the baseline of a null model (intercept only) (See US-3).
- **SC-003**: The false discovery rate of significant findings is measured against the threshold of q < 0.05 after FDR correction (See US-3).
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the free‑tier GitHub Actions limit (7 GB RAM, modest CPU cores, 6 hours) to ensure feasibility (See US-4).
- **SC-005**: The sample size (N) of the final analysis dataset is measured against the power requirements to detect an effect size of r ≥ 0.20 with power ≥ 0.80 and significance level α = 0.05 (See US-5).

## Assumptions

- The Human Connectome Project (HCP) Subjects Release provides high‑quality resting‑state fMRI data for a large cohort of participants.
- Music Emotion Rating (MER) scores are obtained from an external publicly available dataset (e.g., Barcelona Music Reward Questionnaire) that includes subject identifiers or sufficient demographic information to allow deterministic matching to HCP participants.
- fMRIPrep can run successfully in CPU‑only mode on the GitHub Actions free tier without requiring CUDA or GPU acceleration.
- The Schaefer atlas is compatible with the HCP data preprocessing pipeline and provides a valid parcellation for the brain regions of interest.
- The computational load of graph theory metrics on 200×200 matrices fits within the 7 GB RAM limit of the CI runner.
- The study design is observational; therefore, all findings will be framed as associational rather than causal.
- Effect sizes for resting‑state connectivity predicting individual differences in musical‑emotion traits are expected to be small to moderate, consistent with current literature in neuroaesthetics and connectomics (see Zatorre et al., 2020, *Nature Reviews Neuroscience*).
