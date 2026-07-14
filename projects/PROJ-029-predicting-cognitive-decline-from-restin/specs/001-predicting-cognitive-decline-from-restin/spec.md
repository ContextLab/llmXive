# Feature Specification: Predicting Cognitive Decline from Resting-State fMRI Network Topology

**Feature Branch**: `001-predict-cognitive-decline`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Cognitive Decline from Resting-State fMRI Network Topology"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

The researcher downloads the raw BIDS rs-fMRI data from OpenNeuro., filters the cohort to subjects with complete longitudinal cognitive scores (non-null MMSE at both timepoints OR non-null MOCA at both timepoints), and constructs brain networks using the 90-region AAL atlas to calculate graph metrics.

**Why this priority**: This is the foundational step; without valid graph metrics derived from the correct subset of data, no predictive modeling can occur. It validates the dataset-variable fit and ensures data fits within memory constraints.

**Independent Test**: The pipeline can be run on a single batch of data to produce a CSV file containing subject IDs and their calculated graph metrics (degree, efficiency, path length) without any machine learning training.

**Acceptance Scenarios**:
1. **Given** the OpenNeuro dataset ds000246 (ADNI subset) is accessible, **When** the script filters for subjects with both baseline and follow-up MMSE/MOCA scores (non-null at both timepoints for the same metric), **Then** the output dataset contains up to N=100 subjects (or all available if <100) with no missing values for the target variables.
2. **Given** a subject's connectivity matrix, **When** a standard AAL atlas is applied, **Then** An adjacency matrix of appropriate size is generated and graph metrics (node degree, global efficiency, clustering coefficient, path length) are calculated for every node and globally.
3. **Given** a subject's graph metrics, **When** the system checks memory usage during processing, **Then** the peak RAM consumption remains within safe operational bounds for the available runner limit.

---

### User Story 2 - Predictive Modeling and Validation (Priority: P2)

The researcher trains a Random Forest classifier to predict cognitive decline status (stable vs. decline) using the calculated topological features and evaluates performance using nested cross-validation with ROC-AUC, accuracy, and F1-score.

**Why this priority**: This delivers the core research value: determining if topology predicts decline. It must be independent of the validation step to allow for model tuning before statistical significance testing.

**Independent Test**: The pipeline can be executed to output a model file and a performance report (JSON/CSV) containing the ROC-AUC and F1-score for the nested cross-validation, without running the permutation test.

**Acceptance Scenarios**:
1. **Given** the feature matrix and binary labels, **When** the Random Forest classifier is trained with nested cross-validation (5-fold outer, grid search inner), **Then** the system outputs a performance report containing ROC-AUC, accuracy, and F1-score for each fold and the mean.
2. **Given** the trained model, **When** it is applied to the test fold, **Then** the predicted probabilities are generated for all subjects in that fold.
3. **Given** the model architecture, **When** it is trained on the CPU-only runner, **Then** the training time for the nested CV completes within 30 minutes, ensuring the full 6-hour job limit is respected.

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

The researcher performs a permutation test to validate that feature importance is not due to chance and conducts a sensitivity analysis on the decision threshold to ensure robustness.

**Why this priority**: This addresses the methodological soundness requirements (multiplicity, inference framing, threshold justification) ensuring the results are scientifically defensible and not artifacts of random noise or arbitrary cutoffs.

**Independent Test**: The pipeline can take an existing model and performance metric, run the permutation test, and output a p-value and a sensitivity report showing metric variation across thresholds.

**Acceptance Scenarios**:
1. **Given** the trained model and original labels, **When** A sufficient number of label permutations are performed to ensure statistical robustness, bounded by a practical runtime constraint.. and the model re-trained/re-evaluated, **Then** a p-value is calculated representing the proportion of permuted runs that achieved a higher ROC-AUC than the original model.
2. **Given** the model's probability outputs, **When** the decision threshold is swept across a set of values including and 0.55, **Then** a report is generated showing how the False Positive Rate and False Negative Rate vary for each threshold.
3. **Given** the observational nature of the data, **When** the results are summarized, **Then** the report explicitly frames findings as "associational" rather than "causal" in all text outputs.

---

### Edge Cases

- What happens when the OpenNeuro dataset download fails or times out within the GitHub Actions 6-hour window? (System retries up to 3 times with exponential backoff, then fails with a clear error code).
- How does the system handle subjects with missing MMSE/MOCA scores at follow-up? (These subjects are excluded from the final N=100 cohort, and a log of excluded subjects is generated).
- What if the calculated graph metrics result in perfect collinearity (e.g., degree and strength are identical)? (The system detects collinearity > 0.95, flags the features, and excludes one from the model training to prevent overfitting).
- How does the system handle the case where the permutation test yields a p-value of exactly 0.00? (The system reports p < 0.001 and logs the exact count of successful permutations).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the raw BIDS rs-fMRI data from a designated OpenNeuro dataset (ADNI subset) and filter the cohort to a target sample size sufficient for robust statistical power, limited by the number of available eligible subjects., where 'eligible' means non-null MMSE at both timepoints OR non-null MOCA at both timepoints. (See US-1)
- **FR-002**: System MUST preprocess the raw BIDS data (motion correction, normalization, parcellation) using the AAL atlas to generate connectivity matrices. and calculate graph metrics (node degree, efficiency, clustering coefficient, path length) for every subject. (See US-1)
- **FR-003**: System MUST train a Random Forest classifier (n_estimators=100, max_depth=None, random_seed=42) to predict cognitive decline status using topological features and perform 5-fold cross-validation. (See US-2)
- **FR-004**: System MUST evaluate model performance using ROC-AUC, accuracy, and F1-score and output these metrics for each fold. (See US-2)
- **FR-005**: System MUST perform a permutation test with n=500 label shuffles (bounded by max_runtime=2 hours) and random_seed=42 to calculate the statistical significance (p-value) of the model's predictive power. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis by sweeping the decision threshold over the set {0.45, 0.50, 0.55} (standard ±0.05 bounds) and reporting the variation in false-positive and false-negative rates. (See US-3)
- **FR-007**: System MUST explicitly label all reported findings as "associational" and avoid causal language in the final output report, given the observational nature of the data. (See US-3)
- **FR-008**: System MUST detect and handle predictor collinearity (correlation > 0.95) by excluding the feature with lower variance before model training. (See US-1)
- **FR-010**: System MUST implement nested cross-validation with an outer loop of folds and an inner loop grid search over n_estimators and max_depth ∈ {5, 10, None} to prevent overfitting. The range of values for n_estimators will be explored to optimize performance. (See US-2)
- **FR-011**: System MUST validate the model against an external clinical outcome (e.g., MCI conversion) where available in the dataset; if unavailable, the system MUST document this limitation in the final report. (See US-2)
- **FR-012**: System MUST perform a sensitivity analysis on the cognitive decline threshold definition (±1 point variation) to assess the robustness of the label definition. (See US-3)

### Key Entities

- **Subject**: Represents an individual participant with a unique ID, baseline cognitive score, follow-up cognitive score, and status (stable/decline).
- **Connectivity Matrix**: A 90x90 symmetric matrix representing functional connectivity between brain regions for a specific subject.
- **Graph Metrics**: A set of numerical values (degree, efficiency, etc.) derived from the connectivity matrix for a subject.
- **Model**: The trained Random Forest classifier instance used to predict cognitive decline status.
- **Permutation Result**: The distribution of performance metrics generated from shuffling labels, used to calculate the p-value.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of subjects with valid data after filtering is measured against the total available subjects in the OpenNeuro dataset ds000246 (ADNI subset) to ensure the N=100 target is met or documented as a limitation. (See US-1)
- **SC-002**: The system outputs the ROC-AUC value; verification confirms it is > 0.50 with p < 0.05. (See US-2)
- **SC-003**: The p-value from the permutation test is measured against a standard significance threshold to validate that the model's performance is not due to random label shuffling. (See US-3)
- **SC-004**: The variation in False Positive and False Negative rates across the threshold sweep is measured to assess the robustness of the decision boundary. (See US-3)
- **SC-005**: The total runtime of the analysis (download, processing, training, testing) is measured against the GitHub Actions job limit to ensure feasibility. (See US-2)
- **SC-006**: The presence of external clinical outcome data (MCI conversion) is checked during filtering; if absent, the limitation is documented. (See US-2)

## Assumptions

- The OpenNeuro dataset (ADNI subset) contains raw BIDS rs-fMRI data and longitudinal MMSE/MOCA scores for the required subjects.
- The AAL atlas is the standard and appropriate parcellation scheme for the provided connectivity matrices.
- The "decline" status can be reliably defined by a specific drop in MMSE/MOCA scores (e.g., ≥ 3 points), though this is a known methodological limitation; sensitivity analysis (FR-012) will assess robustness.
- The Random Forest algorithm is computationally tractable on a 2-core, 7GB RAM CPU-only runner for N=100 subjects with 90+ features.
- The dataset contains no missing values for the primary graph metric calculations; if missing, the subject is excluded.
- The "stable" vs. "decline" labels are pre-defined in the dataset or can be derived from the difference between baseline and follow-up scores without ambiguity.
- The computational cost of 500 permutations is within the 6-hour job limit (estimated at < 2 hours).
- The sensitivity analysis thresholds {0.45, 0.50, 0.55} are sufficient to capture the variability in classification performance for this dataset.