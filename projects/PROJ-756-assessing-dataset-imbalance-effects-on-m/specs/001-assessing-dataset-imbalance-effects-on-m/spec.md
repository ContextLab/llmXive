# Feature Specification: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Feature Branch**: `001-assess-dataset-imbalance-effects`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Assessing Dataset Imbalance Effects on Materials Property Predictions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1)

The researcher downloads the OQMD and AFLOW datasets (or OQMD, AFLOW, and Materials Project if a verified API key is available), computes compositional descriptors, and trains baseline Random Forest and Gradient Boosting regressors on the native, skewed distributions to establish a performance baseline for formation energy, band gap, and bulk modulus. If Materials Project data is unavailable, the scope is automatically restricted to OQMD and AFLOW.

**Why this priority**: This is the foundational step. Without a baseline performance metric on the skewed data, no comparison can be made to determine if imbalance causes degradation. It validates data acquisition and the core modeling pipeline.

**Independent Test**: Can be fully tested by running the data ingestion and baseline training script, producing a CSV report with MAE, RMSE, and R² for the original skewed datasets (OQMD/AFLOW or MP+OQMD+AFLOW), without needing the balancing logic.

**Acceptance Scenarios**:

1. **Given** the public REST APIs for OQMD and AFLOW are accessible (and Materials Project if credentials are verified), **When** the ingestion script runs, **Then** a local dataset of ≤ 5 GB is created containing at least 3 target properties (formation energy, band gap, bulk modulus) and Magpie compositional descriptors.
2. **Given** the skewed training set is prepared, **When** the Random Forest and Gradient Boosting models are trained with identical hyperparameters, **Then** the system outputs a baseline performance report containing MAE, RMSE, and R² for each property.
3. **Given** the baseline models are trained, **When** the evaluation runs on the stratified test set, **Then** the system logs the performance metrics and stores the trained model artifacts for later comparison.

---

### User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

The researcher applies stratified undersampling/oversampling (or cost-sensitive learning/SMOTE if binning fails) to create balanced training sets, retrains the models, and statistically compares the performance metrics (MAE, R²) against the baseline to quantify the impact of imbalance on the bottom [deferred] of the target distribution.

**Why this priority**: This directly addresses the core research question: "How does the degree of imbalance influence predictive accuracy?" It requires the baseline from US-1 to be meaningful.

**Independent Test**: Can be fully tested by running the resampling and retraining pipeline, producing a comparison table and statistical test results (paired t-test/Wilcoxon) showing the difference in performance between skewed and balanced models on the bottom [deferred] minority subset.

**Acceptance Scenarios**:

1. **Given** the original skewed dataset, **When** the stratified resampling algorithm (using equal-frequency binning into 20 bins) is applied, **Then** a balanced training set is created where real-data bin counts are uniform within a Coefficient of Variation (CV) of ≤ 0.10.
2. **Given** the balanced training set, **When** the models are retrained and evaluated on the bottom [deferred] of the target distribution, **Then** the system calculates the absolute percentage change in MAE compared to the baseline on that specific subset.
3. **Given** results from a dynamically determined number of random seeds (based on power analysis), **When** the paired statistical test is executed, **Then** the system reports whether the performance difference is statistically significant (α = 0.05).

---

### User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

The researcher generates SHAP values for both skewed and balanced models, compares the top-10 feature importance rankings, and visualizes how imbalance distorts the inferred physical drivers of material properties, validated against a synthetic ground-truth baseline.

**Why this priority**: This addresses the secondary research goal regarding "feature‑importance attribution." While valuable for understanding *why* performance changes, it depends on the models being trained (US-1 & US-2) and is secondary to the primary accuracy metric.

**Independent Test**: Can be fully tested by running the SHAP analysis script on the trained model artifacts and the synthetic ground-truth dataset, producing a ranked list of features and a visualization comparing the two distributions and validating against known weights.

**Acceptance Scenarios**:

1. **Given** the trained skewed and balanced models, **When** the SHAP analysis is computed, **Then** the system extracts feature importance scores for all compositional descriptors.
2. **Given** the SHAP scores, **When** the top-10 features are ranked and compared, **Then** the system outputs a delta metric indicating the rank shift for each feature between the two models.
3. **Given** the rank shifts, **When** the visualization is generated, **Then** the output clearly highlights features that changed rank position significantly (e.g., top 5 in skewed vs. top 20 in balanced) and validates against the synthetic ground truth.

---

### Edge Cases

- What happens if a specific target property (e.g., bulk modulus) has an insufficient number of data points in the entire merged dataset? (System MUST skip that property for that specific dataset, log a warning, and exclude it from the ImbalanceScore calculation).
- How does the system handle API rate limits when downloading large volumes of data? (System MUST implement exponential backoff with a configurable number of retries and a timeout per request).
- What if the equal-frequency binning (20 bins) results in a bin with zero samples or excessive data loss (>20%)? (System MUST automatically switch to 'cost-sensitive learning' or 'SMOTE for regression' as defined in FR-003, noting that the CV ≤ 0.10 constraint applies only to the real data portion, while the synthetic portion allows CV ≤ 0.30).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and merge data from OQMD and AFLOW APIs. If a verified API key for Materials Project is available, it MUST also download from Materials Project. The total dataset size MUST be manageable within standard computational constraints and MUST include at least formation energy, band gap, and bulk modulus as targets. If Materials Project is unavailable, the system MUST proceed with OQMD and AFLOW only. (See US-1)
- **FR-002**: System MUST compute Magpie compositional descriptors (all 14 features, L2-normalized) for all entries and calculate an "ImbalanceScore" defined as the Gini coefficient of the compositional feature space (derived from K-Means clustering with k=50 and Euclidean distance). If a property has <100 samples, it is skipped and excluded from this calculation. (See US-1)
- **FR-003**: System MUST implement a stratified resampling algorithm using equal-frequency binning into a sufficient number of bins. If this results in >20% data loss or empty bins, the system MUST switch to cost-sensitive learning (class weights) or SMOTE for regression. The resulting training set must have bin counts with a Coefficient of Variation (CV) ≤ 0.10 for the *real* data distribution. If synthetic data (SMOTE) is used, the synthetic portion must not exceed 30% of the total training set, and the combined distribution must have CV ≤ 0.30. (See US-2)
- **FR-004**: System MUST train Random Forest and Gradient Boosting regressors on both skewed and balanced datasets using identical hyperparameters and evaluate them on a stratified test set preserving the original imbalance. (See US-2)
- **FR-005**: System MUST perform paired statistical tests (paired t-test or Wilcoxon signed-rank) across multiple random seeds (determined by power analysis) to determine the significance of performance differences between skewed and balanced models. (See US-2)
- **FR-006**: System MUST generate SHAP values for the trained models and output a comparison of the top-10 feature importance rankings between skewed and balanced conditions. (See US-3)
- **FR-007**: System MUST log all API errors and data ingestion failures, including a configurable retry count per endpoint before marking the dataset as incomplete. (See US-1)
- **FR-008**: System MUST detect if Materials Project data is unavailable (e.g., API error, 403, timeout) and automatically switch to a fallback mode using only OQMD and AFLOW, logging the scope change. (See US-1)
- **FR-009**: System MUST calculate "performance degradation" as the difference in MAE on the minority subset: MAE_skewed_minority - MAE_balanced_minority. (See US-2)
- **FR-010**: System MUST identify and isolate the bottom [deferred] of the target distribution (e.g., formation energy) for evaluation and calculate per-bin MAE for this subset. (See US-2)
- **FR-011**: System MUST calculate and report a "Target Imbalance Score" defined as the Gini coefficient of the *target property* distribution (e.g., formation energy values). (See US-2)
- **FR-012**: System MUST compute and report the correlation coefficient between the compositional ImbalanceScore (FR-002) and the performance degradation (FR-009), and separately test the correlation between the Target Imbalance Score (FR-011) and performance degradation. (See US-2)
- **FR-013**: System MUST limit the amount of synthetic data generated by SMOTE to a maximum of 30% of the total training set to prevent artificial inflation of performance metrics. (See US-2)
- **FR-014**: System MUST generate a synthetic dataset with known feature weights (ground truth) to validate SHAP values and distinguish between "bias correction" and "distortion". (See US-3)
- **FR-015**: System MUST perform a power analysis to determine the minimum number of random seeds required to detect a medium effect size (Cohen's d = 0.5) with power ≥ 0.8 at α = 0.05. (See US-2)

### Key Entities

- **MaterialEntry**: Represents a single material record with composition, target properties (energy, gap, modulus), and computed descriptors.
- **ImbalanceScore**: A derived metric quantifying the skewness of the dataset based on the Gini coefficient of the compositional feature space (K-Means, k=50).
- **TargetImbalanceScore**: A derived metric quantifying the skewness of the target property distribution (Gini of target values).
- **ModelArtifact**: A container for the trained model, hyperparameters, and performance metrics (MAE, R²) associated with a specific training strategy (skewed vs. balanced).
- **SHAPComparison**: A dataset linking features to their importance ranks in both skewed and balanced models, used to calculate rank shifts.
- **SyntheticGroundTruth**: A generated dataset with known feature weights used to validate SHAP analysis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The absolute percentage change in MAE (|MAE_baseline - MAE_balanced| / MAE_baseline * 100) for the bottom [deferred] target subset is measured against the baseline performance of the skewed model. (See US-2)
- **SC-002**: The statistical significance of performance differences (p-value) is measured against the threshold α = 0.05 across a dynamically determined number of random seeds (based on power analysis). (See US-2)
- **SC-003**: The magnitude of feature importance distortion is measured by the mean rank shift of the top-10 features (ties broken by average rank) between skewed and balanced models, validated against the synthetic ground-truth baseline. (See US-3)
- **SC-004**: The correlation between the compositional ImbalanceScore and the performance degradation (MAE_skewed_minority - MAE_balanced_minority) is measured, and the correlation between the Target Imbalance Score and performance degradation is measured to determine the causal link between feature space diversity and target imbalance. (See US-2)

### Operational Constraints

> These are hard limits required for the system to function within the available infrastructure.

- **Constraint-001**: The full pipeline (ingestion, training, evaluation) MUST complete within 6 hours on a CPU-only GitHub Actions runner.
- **Constraint-002**: The memory footprint MUST stay within 7 GB RAM during the training and SHAP analysis phases.

## Assumptions

- **Assumption about data availability**: The public REST APIs for OQMD and AFLOW will remain accessible and free of charge. If the Materials Project API is unavailable (due to credentials or rate limits), the scope is restricted to OQMD and AFLOW only.
- **Assumption about computational resources**: The analysis will run on a standard GitHub Actions free-tier runner (a multi-core CPU configuration, ~7 GB RAM, ~14 GB disk) with no GPU acceleration; therefore, no deep learning models (e.g., GNNs) will be trained, and only CPU-tractable methods (Random Forest, Gradient Boosting) will be used.
- **Assumption about imbalance definition**: The research design hypothesizes that target property imbalance is often a consequence of compositional imbalance. This hypothesis will be tested via FR-012 (correlation analysis) rather than assumed as fact.
- **Assumption about statistical power**: The sample size of the merged datasets is assumed to be sufficient to perform a power analysis (FR-015) to determine the required number of random seeds dynamically.
- **Assumption about resampling method**: Stratified undersampling/oversampling (or SMOTE/cost-sensitive learning) is assumed to be the primary method for balancing, as it is computationally cheaper than deep generative models and fits within the CPU constraints.
- **Assumption about SHAP validity**: SHAP values are assumed to be a valid proxy for feature importance in the context of Random Forest and Gradient Boosting models, but this validity will be tested against a synthetic ground-truth baseline (FR-014) rather than assumed.