# Feature Specification: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Feature Branch**: `001-assess-dataset-imbalance-effects`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Assessing Dataset Imbalance Effects on Materials Property Predictions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1)

The researcher downloads the Materials Project, OQMD, and AFLOW datasets, computes compositional descriptors, and trains baseline Random Forest and Gradient Boosting regressors on the native, skewed distributions to establish a performance baseline for formation energy, band gap, and bulk modulus.

**Why this priority**: This is the foundational step. Without a baseline performance metric on the skewed data, no comparison can be made to determine if imbalance causes degradation. It validates data acquisition and the core modeling pipeline.

**Independent Test**: Can be fully tested by running the data ingestion and baseline training script, producing a CSV report with MAE, RMSE, and R² for the original skewed datasets, without needing the balancing logic.

**Acceptance Scenarios**:

1. **Given** the public REST APIs for Materials Project, OQMD, and AFLOW are accessible, **When** the ingestion script runs, **Then** a local dataset of ≤ 5 GB is created containing at least 3 target properties (formation energy, band gap, bulk modulus) and Magpie compositional descriptors.
2. **Given** the skewed training set is prepared, **When** the Random Forest and Gradient Boosting models are trained with identical hyperparameters, **Then** the system outputs a baseline performance report containing MAE, RMSE, and R² for each property.
3. **Given** the baseline models are trained, **When** the evaluation runs on the stratified test set, **Then** the system logs the performance metrics and stores the trained model artifacts for later comparison.

---

### User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

The researcher applies stratified undersampling/oversampling to create balanced training sets, retrains the models, and statistically compares the performance metrics (MAE, R²) against the baseline to quantify the impact of imbalance.

**Why this priority**: This directly addresses the core research question: "How does the degree of imbalance influence predictive accuracy?" It requires the baseline from US-1 to be meaningful.

**Independent Test**: Can be fully tested by running the resampling and retraining pipeline, producing a comparison table and statistical test results (paired t-test/Wilcoxon) showing the difference in performance between skewed and balanced models.

**Acceptance Scenarios**:

1. **Given** the original skewed dataset, **When** the stratified resampling algorithm is applied, **Then** a balanced training set is created where bin counts for target properties are approximately uniform (within ±10% variance).
2. **Given** the balanced training set, **When** the models are retrained and evaluated on the original skewed test set, **Then** the system calculates the difference in MAE and R² compared to the baseline.
3. **Given** results from 10 different random seeds, **When** the paired statistical test is executed, **Then** the system reports whether the performance difference is statistically significant (α = 0.05).

---

### User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

The researcher generates SHAP values for both skewed and balanced models, compares the top-10 feature importance rankings, and visualizes how imbalance distorts the inferred physical drivers of material properties.

**Why this priority**: This addresses the secondary research goal regarding "feature‑importance attribution." While valuable for understanding *why* performance changes, it depends on the models being trained (US-1 & US-2) and is secondary to the primary accuracy metric.

**Independent Test**: Can be fully tested by running the SHAP analysis script on the trained model artifacts, producing a ranked list of features and a visualization (e.g., bar chart or summary plot) comparing the two distributions.

**Acceptance Scenarios**:

1. **Given** the trained skewed and balanced models, **When** the SHAP analysis is computed, **Then** the system extracts feature importance scores for all compositional descriptors.
2. **Given** the SHAP scores, **When** the top-10 features are ranked and compared, **Then** the system outputs a delta metric indicating the rank shift for each feature between the two models.
3. **Given** the rank shifts, **When** the visualization is generated, **Then** the output clearly highlights features that changed rank position significantly (e.g., top 5 in skewed vs. top 20 in balanced).

---

### Edge Cases

- What happens if a specific target property (e.g., bulk modulus) has fewer than 100 data points in the entire merged dataset? (System should skip that property for that specific dataset and log a warning).
- How does the system handle API rate limits when downloading 5 GB of data? (System must implement exponential backoff with a max retry count of 5 and a 60-second timeout per request).
- What if the stratified binning results in a bin with zero samples after undersampling? (System must enforce a minimum bin size of 10 samples and merge adjacent bins if necessary).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and merge data from Materials Project, OQMD, and AFLOW APIs, ensuring the total dataset size does not exceed 5 GB and includes at least formation energy, band gap, and bulk modulus as targets. (See US-1)
- **FR-002**: System MUST compute Magpie compositional descriptors for all entries and calculate an "imbalance score" based on the inverse frequency of target property bins. (See US-1)
- **FR-003**: System MUST implement a stratified resampling algorithm that creates a balanced training set with bin counts uniform within ±10% variance. (See US-2)
- **FR-004**: System MUST train Random Forest and Gradient Boosting regressors on both skewed and balanced datasets using identical hyperparameters and evaluate them on a stratified test set preserving the original imbalance. (See US-2)
- **FR-005**: System MUST perform paired statistical tests (paired t-test or Wilcoxon signed-rank) across 10 random seeds to determine the significance of performance differences between skewed and balanced models. (See US-2)
- **FR-006**: System MUST generate SHAP values for the trained models and output a comparison of the top-10 feature importance rankings between skewed and balanced conditions. (See US-3)
- **FR-007**: System MUST log all API errors and data ingestion failures, including a retry count of at most 3 attempts per endpoint before marking the dataset as incomplete. (See US-1)

### Key Entities

- **MaterialEntry**: Represents a single material record with composition, target properties (energy, gap, modulus), and computed descriptors.
- **ImbalanceScore**: A derived metric quantifying the skewness of the dataset based on target property bin frequencies.
- **ModelArtifact**: A container for the trained model, hyperparameters, and performance metrics (MAE, R²) associated with a specific training strategy (skewed vs. balanced).
- **SHAPComparison**: A dataset linking features to their importance ranks in both skewed and balanced models, used to calculate rank shifts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The reduction in MAE and increase in R² for under-represented bins is measured against the baseline performance of the skewed model. (See US-2)
- **SC-002**: The statistical significance of performance differences (p-value) is measured against the threshold α = 0.05 across 10 random seeds. (See US-2)
- **SC-003**: The magnitude of feature importance distortion is measured by the average rank shift of the top-10 features between skewed and balanced models. (See US-3)
- **SC-004**: The computational efficiency is measured against the constraint of completing the full pipeline (ingestion, training, evaluation) within 6 hours on a CPU-only runner. (See Assumptions)
- **SC-005**: The memory footprint is measured against the constraint of staying within 7 GB RAM during the training and SHAP analysis phases. (See Assumptions)

## Assumptions

- **Assumption about data availability**: The public REST APIs for Materials Project, OQMD, and AFLOW will remain accessible and free of charge for the duration of the analysis, and the total merged dataset will not exceed 5 GB.
- **Assumption about computational resources**: The analysis will run on a standard GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk) with no GPU acceleration; therefore, no deep learning models (e.g., GNNs) will be trained, and only CPU-tractable methods (Random Forest, Gradient Boosting) will be used.
- **Assumption about imbalance definition**: The "imbalance" is defined strictly by the frequency distribution of target property bins (e.g., formation energy ranges), and compositional imbalance is treated as a secondary factor unless explicitly correlated.
- **Assumption about statistical power**: The sample size of the merged datasets is assumed to be sufficient to perform 10 random splits with adequate power for paired t-tests, though specific power calculations are deferred to the implementation phase.
- **Assumption about resampling method**: Stratified undersampling/oversampling is assumed to be the primary method for balancing, as it is computationally cheaper than synthetic generation (SMOTE) for regression tasks and fits within the CPU constraints.
- **Assumption about SHAP validity**: SHAP values are assumed to be a valid proxy for feature importance in the context of Random Forest and Gradient Boosting models, despite the inherent approximations of the method.
