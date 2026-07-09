# Feature Specification: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Can graph theory metrics derived from resting-state fMRI data differentiate between individuals diagnosed with schizophrenia and healthy controls? Specifically, do measures of network efficiency, modularity, and centrality in prefrontal and hippocampal regions predict diagnostic status with accuracy significantly above chance?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST ingest raw resting-state fMRI data from the OpenNeuro dataset., apply standard preprocessing (motion correction, normalization, bandpass filtering 0.01-0.1 Hz), and construct subject-level functional connectivity matrices using the AAL atlas (90 ROIs).

**Why this priority**: This is the foundational step; without clean, standardized connectivity matrices, no graph metrics or classification can occur. It represents the bulk of the data engineering effort required to make the data analysis-ready.

**Independent Test**: Can be fully tested by running the preprocessing script on a small subset of the dataset (e.g., 5 subjects) and verifying that the output is a set of 90x90 correlation matrices in CSV/NumPy format with valid dimensions and no NaN values.

**Acceptance Scenarios**:

1. **Given** raw NIfTI files for a subject in the OpenNeuro ds000030 dataset, **When** the preprocessing pipeline is executed, **Then** a 90x90 functional connectivity matrix is generated for that subject.
2. **Given** a subject with excessive motion (>2mm translation), **When** the pipeline runs, **Then** the subject is flagged and excluded from the final dataset (or motion parameters are included as covariates if the pipeline supports it).
3. **Given** the full dataset, **When** the pipeline completes, **Then** a metadata file is produced mapping each subject ID to their diagnostic label (Schizophrenia vs. Control) and preprocessing status.

---

### User Story 2 - Graph Metric Computation and Feature Extraction (Priority: P2)

The system MUST compute graph theory metrics (global efficiency, local efficiency, modularity via Louvain, betweenness centrality) for each subject's connectivity matrix and extract a final feature vector of 15-20 metrics, specifically highlighting prefrontal and hippocampal regions.

**Why this priority**: This transforms the raw connectivity data into the specific variables required for the hypothesis testing. It is the core analytical engine of the study.

**Independent Test**: Can be tested by running the metric computation on a single synthetic connectivity matrix with known properties and verifying that the output metrics match theoretical expectations (e.g., a fully connected graph has efficiency = 1.0).

**Acceptance Scenarios**:

1. **Given** a valid 90x90 connectivity matrix, **When** the graph metric calculator is executed, **Then** it outputs a dictionary containing global efficiency, local efficiency, modularity, and regional centrality values.
2. **Given** the computed metrics for all subjects, **When** the feature extraction step runs, **Then** a single feature matrix (N_subjects x 15-20 features) is generated for the classifier.
3. **Given** the feature matrix, **When** a summary statistics report is generated, **Then** it includes mean and standard deviation for each metric, stratified by diagnostic group (Schizophrenia vs. Control).

---

### User Story 3 - Classification and Statistical Validation (Priority: P3)

The system MUST train logistic regression and SVM classifiers on the extracted features using stratified splits and 5-fold cross-validation, then perform statistical validation (two-sample t-tests with FDR correction, permutation testing with 1000 iterations) to determine if accuracy exceeds chance (≥65% with 95% CI excluding 50%).

**Why this priority**: This delivers the final research answer (the "predictive power" question) and provides the statistical rigor required to validate the findings. It relies on the outputs of P1 and P2.

**Independent Test**: Can be tested by running the analysis on a dataset with randomized labels; the resulting classifier accuracy should be ~50% and permutation p-values should be >0.05, confirming the pipeline isn't leaking information.

**Acceptance Scenarios**:

1. **Given** the feature matrix and diagnostic labels, **When** the classifier training runs, **Then** it outputs accuracy, precision, recall, and AUC-ROC scores for both Logistic Regression and SVM models.
2. **Given** the group difference data, **When** the statistical test suite runs, **Then** it outputs p-values for each metric with False Discovery Rate (FDR) correction applied.
3. **Given** the classifier results, **When** the permutation test runs (1000 iterations), **Then** it outputs a p-value indicating whether the observed accuracy is significantly greater than chance.

---

### Edge Cases

- What happens when the dataset contains subjects with missing diagnostic labels? (System MUST exclude these subjects and log the count).
- How does the system handle connectivity matrices that are not positive semi-definite (if required by specific graph algorithms)? (System MUST apply a small regularization term or use a method robust to this, documented in the logs).
- How does the system handle the case where the permutation test p-value is exactly 0.001 (due to limited iterations)? (System MUST report p < 0.001 and note the resolution limit).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess resting-state fMRI data from OpenNeuro ds000030 using motion correction, normalization, and bandpass filtering (0.01-0.1 Hz) to generate subject-level connectivity matrices. (See US-1)
- **FR-002**: System MUST compute graph theory metrics (global efficiency, local efficiency, modularity, betweenness centrality) for each subject's connectivity matrix using the AAL atlas. (See US-2)
- **FR-003**: System MUST construct a feature matrix of 15-20 network metrics per subject, explicitly extracting prefrontal and hippocampal centrality values. (See US-2)
- **FR-004**: System MUST train Logistic Regression and SVM classifiers on the feature matrix using an 80/20 stratified split and 5-fold cross-validation. (See US-3)
- **FR-005**: System MUST perform statistical validation including two-sample t-tests with FDR correction and permutation testing (1000 iterations) to assess significance against chance. (See US-3)

### Key Entities

- **Subject**: An individual participant in the study, characterized by a unique ID, diagnostic label (Schizophrenia/Control), and a set of preprocessing status flags.
- **Connectivity Matrix**: A 90x90 symmetric matrix representing the functional connectivity strength between AAL regions for a specific subject.
- **Feature Vector**: A 15-20 dimensional vector containing computed graph metrics (efficiency, modularity, centrality) for a single subject.
- **Classifier Model**: A trained machine learning model (Logistic Regression or SVM) capable of mapping Feature Vectors to diagnostic labels.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Classifier accuracy is measured against the chance baseline. using a 95% Confidence Interval; the lower bound of the CI must be >50% to claim significance. (See US-3)
- **SC-002**: Group differences in graph metrics are measured against a null hypothesis of no difference using two-sample t-tests with FDR correction; significance is defined as adjusted p < 0.05. (See US-3)
- **SC-003**: Permutation test p-values are measured against the significance threshold of 0.05; a p-value < 0.05 indicates the classifier performance is not due to random chance. (See US-3)
- **SC-004**: Effect sizes (Cohen's d) for significant group differences are measured to quantify the magnitude of the biomarker signal. (See US-3)
- **SC-005**: The entire analysis pipeline (data download, preprocessing, metric computation, classification, stats) is measured against the compute constraint of ≤6 hours on a 2-core CPU, 7GB RAM runner. (See US-1, US-2, US-3)

## Assumptions

- The OpenNeuro ds000030 (or similar) dataset contains sufficient subjects with both Schizophrenia and Healthy Control labels to achieve statistical power for the planned t-tests and classification (sample size is assumed to be ≥30 per group, otherwise power is noted as a limitation).
- The AAL atlas (90 ROIs) is an appropriate and standard node definition for this specific dataset and research question.
- The preprocessing pipeline (FSL/AFNI scripts) will run successfully on the free-tier CI environment without requiring specialized hardware or GPU acceleration.
- The dataset variables (diagnosis, fMRI scans) are sufficient for the analysis; no additional clinical covariates (e.g., medication dosage, symptom severity) are required for the primary analysis, though they may be noted as `[NEEDS CLARIFICATION: does dataset contain medication status?]` if the idea implies controlling for them later.
- The graph metrics (efficiency, modularity) can be computed using standard Python libraries (e.g., `networkx`, `bctpy`) within the memory limits of the CI runner (≤7GB RAM).
- The analysis is observational; therefore, all findings regarding "predictive power" will be framed as associational, not causal, unless the dataset includes a randomized intervention component (which is not implied).
- The threshold for "significant above chance" is fixed at ≥65% accuracy with a 95% CI excluding 50%, as specified in the idea; a sensitivity analysis for this threshold is not required as it is a primary outcome metric, not a tuning parameter.
- The dataset contains the necessary variables (resting-state fMRI, diagnostic labels) and no critical missing variables (e.g., motion parameters) that would invalidate the preprocessing or analysis.
