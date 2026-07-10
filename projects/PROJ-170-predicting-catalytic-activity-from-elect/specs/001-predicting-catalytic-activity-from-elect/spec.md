# Feature Specification: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Feature Branch**: `001-predicting-catalytic-activity`
**Created**: 2026-06-24
**Status**: Draft
**Input**: User description: "Predicting Catalytic Activity from Electronic Structure and Reaction Path Features"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a computational chemist, I need a reproducible pipeline that downloads the OC20 dataset, retrieves Materials Project bulk descriptors, and aligns them with experimental TOF data so that I can begin analysis with a clean, validated dataset.

**Why this priority**: Without a unified, aligned dataset, no modeling or statistical analysis is possible. This is the foundational step that enables all subsequent research activities.

**Independent Test**: The pipeline can be tested by verifying that the output CSV contains exactly the expected columns (catalyst_id, d_band_center, activation_barrier, experimental_tof) with no NaN values in the target column after imputation.

**Acceptance Scenarios**:

1. **Given** the OC20 dataset, Materials Project descriptors, and the 2025 CO₂ hydrogenation study dataset are available, **When** the preprocessing script runs, **Then** a unified dataset with ≥ [deferred: n≥500, target≥3000] matched entries is generated (target justified by power analysis for α=0.05, power=0.8).
2. **Given** a catalyst entry with missing d-band center, **When** the k-nearest-neighbor imputation (k=5) runs, **Then** the missing value is filled with the mean of the 5 nearest neighbors based on stoichiometry similarity.
3. **Given** the unified dataset, **When** the scaling step runs, **Then** all numeric features are transformed to zero mean and unit variance, and the output is saved as `aligned_dataset.csv`.

---

### User Story 2 - Model Training and Baseline Comparison (Priority: P2)

As a researcher, I need to train a Gradient-Boosted Regression Trees (XGBoost) model and compare it against a simple linear baseline using only d-band center and activation barrier, so that I can quantify the value of the expanded descriptor set.

**Why this priority**: This story delivers the core predictive capability and establishes whether the complex descriptor set provides measurable improvement over traditional Sabatier-volcano descriptors.

**Independent Test**: The model training can be tested by running the script and verifying that both the XGBoost and linear models produce predictions on the hold-out test set with calculated R² and MAE metrics.

**Acceptance Scenarios**:

1. **Given** the preprocessed training set, **When** the 5-fold cross-validation grid search runs (max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, n_estimators ≤ 200), **Then** the hyperparameters maximizing R² are selected and the final model is saved.
2. **Given** the hold-out test set, **When** both the XGBoost and linear baseline models generate predictions, **Then** the paired t-test (α=0.05) on absolute errors is computed and the result (significant/not significant) is logged.
3. **Given** the test set results, **When** the performance report is generated, **Then** it contains the Pearson R, MAE, and the t-test p-value for both models.

---

### User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

As a domain expert, I need a SHAP-based analysis that ranks the top 5 descriptors by mean absolute impact and visualizes them, so that I can identify the physical determinants of catalytic activity.

**Why this priority**: This story provides the scientific insight required to answer the research question ("which specific descriptors provide the most predictive signal?") and validates the hypothesis that a compact set captures the dominant physics.

**Independent Test**: The interpretability step can be tested by running the SHAP calculation and verifying that the top 5 descriptors are listed in descending order of importance with a corresponding bar plot generated.

**Acceptance Scenarios**:

1. **Given** the trained XGBoost model and test data, **When** SHAP values are computed, **Then** a ranked list of descriptors by mean absolute SHAP impact is produced.
2. **Given** the ranked descriptors, **When** the visualization script runs, **Then** a bar plot displaying the top 5 descriptors is saved as `feature_importance.png`.
3. **Given** the top 5 descriptors, **When** the final report is compiled, **Then** it explicitly states whether these descriptors align with known physical mechanisms (e.g., d-band center, activation barrier) or reveal novel predictors.

---

### Edge Cases

- What happens when the Materials Project descriptor file is missing a specific catalyst composition? (Handled by k=5 imputation; if <5 neighbors exist, the entry is flagged and excluded from training).
- How does the system handle experimental TOF values that are reported as "below detection limit"? (These entries are excluded from the regression training set but logged in a separate report).
- What happens if the 5-fold cross-validation yields identical R² scores for multiple hyperparameter sets? (The set with the lowest n_estimators is selected to minimize overfitting risk).
- What happens if an entry has missing descriptors but <5 neighbors exist in the reference set? (The entry is kept in the unified dataset but flagged and excluded from model training to prevent imputation failure).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the OC dataset (≈5k entries), Materials Project bulk descriptors, and the 2025 CO₂ hydrogenation study dataset () via `wget` and parse them into a unified Pandas DataFrame (See US-1).
- **FR-002**: System MUST align DFT entries to experimental TOFs using exact string matching on columns: `composition`, `surface_facet`, `synthesis_condition`. Entries are excluded from the unified dataset if they cannot be aligned OR if `synthesis_condition` is not uniquely identifiable to prevent circular validation. If an entry is aligned but has missing descriptors with <5 neighbors in the reference set, it is flagged and excluded from model training (See US-1).
- **FR-003**: System MUST impute missing descriptor values using k-nearest-neighbors (k=5) based on Euclidean distance in stoichiometry space (normalized element counts), excluding the target variable (experimental_tof) from distance calculation. If fewer than 5 neighbors are found, the entry is flagged and excluded from model training. All numeric features must be scaled to zero mean and unit variance (See US-1).
- **FR-004**: System MUST train a Gradient-Boosted Regression Trees model (XGBoost) with a grid search over max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, and n_estimators ≤ 200, selecting the configuration that maximizes 5-fold cross-validated R² (See US-2).
- **FR-005**: System MUST fit a linear regression baseline using only d-band center and activation barrier, perform a Shapiro-Wilk test (α=0.05) on the distribution of absolute errors; if normality is rejected, use Wilcoxon signed-rank test instead of paired t-test; otherwise, perform a two-tailed paired t-test (α=0.05, H0: mean difference = 0) on the absolute errors of the XGBoost and baseline models on the hold-out test set (See US-2).
- **FR-006**: System MUST compute SHAP values for the final XGBoost model, rank descriptors by mean absolute SHAP impact, and generate a bar plot of the top 5 descriptors (See US-3).
- **FR-007**: System MUST output a final report containing the Pearson R, MAE, t-test p-value, and the ranked list of top 5 descriptors. The report must compare the top 5 descriptors against the reference list in Nørskov et al., 2005 (d-band center, activation barrier, reaction energy) and explicitly state matches or novel findings (See US-3).

### Key Entities

- **CatalystEntry**: Represents a unique catalyst configuration; attributes include `composition`, `surface_facet`, `synthesis_condition`, `d_band_center`, `p_band_center`, `bader_charges`, `activation_barrier`, `reaction_energy`, `experimental_tof`.
- **ModelMetrics**: Stores performance statistics; attributes include `model_type`, `r_squared`, `mean_absolute_error`, `pearson_r`, `t_test_p_value`.
- **FeatureImportance**: Represents descriptor impact; attributes include `descriptor_name`, `mean_absolute_shap_value`, `rank`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (Pearson R and MAE) of the XGBoost model is measured against the linear baseline model on the hold-out test set to determine if the expanded descriptor set provides statistically significant improvement (See US-2).
- **SC-002**: The alignment success rate (number of matched entries / total experimental entries) is measured against the total number of experimental TOF entries to assess data coverage (See US-1).
- **SC-003**: A model trained independently on the top 5 SHAP-ranked descriptors must achieve an R² ≥ 0.50 * R²_full, measuring feature redundancy rather than physical validation (See US-3).
- **SC-004**: The computational runtime of the full pipeline (download to report generation) is measured against the GitHub Actions runner time limit. to verify feasibility (See US-1, US-2, US-3).
- **SC-005**: The statistical significance of the model improvement is measured against the α=0.05 threshold using a paired t-test or Wilcoxon signed-rank test on absolute errors (See US-2).

## Assumptions

- The Materials Project bulk descriptor CSV contains valid d-band center, p-band center, and Bader charge values for the catalyst compositions present in the OC20 dataset.
- The experimental TOF values in the 2025 CO₂ hydrogenation study are reported in consistent units (e.g., s⁻¹) and do not require unit conversion.
- The OC dataset and Materials Project data can be downloaded and stored within the disk limit of the free-tier runner.
- The k-nearest-neighbor imputation (k=5) is sufficient to handle missing values without introducing significant bias, as the dataset is assumed to be dense in composition space. If <5 neighbors exist, the entry is excluded from training to avoid bias.
- The XGBoost model with n_estimators ≤ 200 and default precision (no quantization) will complete training within the 6-hour time limit on 2 CPU cores.
- The paired t-test assumption of normality for the distribution of absolute errors is checked; if not met, a non-parametric alternative (Wilcoxon signed-rank test) is used as a fallback (documented in code).
- The "2025 CO₂ hydrogenation study" refers to the publicly available supplementary CSV linked in the paper mentioned in the idea, and the URL is stable.
- The d-band center and activation barrier are definitionally distinct from other descriptors, so multicollinearity diagnostics will be performed but are not expected to prevent model training.
- The target of ≥3000 matched entries is a guideline based on power analysis for α=0.05 and power=0.8; if fewer entries are available (but ≥500), the analysis proceeds with the available data.