# Feature Specification: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Feature Branch**: `001-predicting-catalytic-activity`
**Created**: 2026-06-24
**Status**: Draft
**Input**: User description: "Predicting Catalytic Activity from Electronic Structure and Reaction Path Features"

## User Scenarios & Testing

### User Story US-1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a computational chemist, I need a reproducible pipeline that downloads the OC20 dataset, retrieves Materials Project bulk descriptors, and aligns them with experimental TOF data from the 2025 CO₂ hydrogenation study (Doe et al., 2025,) so that I can begin analysis with a clean, validated dataset.

**Why this priority**: Without a unified, aligned dataset, no modeling or statistical analysis is possible. This is the foundational step that enables all subsequent research activities.

**Independent Test**: The pipeline can be tested by verifying that the output CSV contains exactly the expected columns (catalyst_id, composition, surface_facet, synthesis_condition, d_band_center, p_band_center, bader_charges, activation_barrier, reaction_energy, experimental_tof, temperature, pressure) with no NaN values in the target column after imputation, and that a SHA‑256 checksum matches the recorded value in `checksums.txt`.

**Acceptance Scenarios**:

1. **Given** the OC20 dataset, Materials Project descriptors, and the 2025 CO₂ hydrogenation study dataset are available, **When** the preprocessing script runs, **Then** a unified dataset with ≥ **1500** matched entries is generated **if** the source data contain at least that many; otherwise a dataset with ≥ **500** matched entries is produced and the reduced‑power situation is noted in `alignment_metrics.json`. The alignment_success_rate must be ≥ 0.80 and is recorded in `alignment_metrics.json`.  
2. **Given** a catalyst entry with missing d-band center, **When** the k‑nearest‑neighbor imputation (k=5) runs, **Then** the missing value is filled with the mean of the 5 nearest neighbors based on stoichiometry similarity; if fewer than 5 neighbors exist, the entry is flagged and excluded from model training.  
3. **Given** the unified dataset, **When** the scaling step runs, **Then** all numeric features are transformed to zero mean and unit variance, and the post‑scaling mean |μ| < 0.01 and |σ‑1| < 0.01 are verified in `scaling_report.json`. The output is saved as `aligned_dataset.csv`.

---

### User Story US-2 - Model Training and Baseline Comparison (Priority: P2)

As a researcher, I need to train a Gradient‑Boosted Regression Trees (XGBoost) model and compare it against a simple linear baseline using only d‑band center and activation barrier, so that I can quantify the value of the expanded descriptor set.

**Why this priority**: This story delivers the core predictive capability and establishes whether the complex descriptor set provides measurable improvement over traditional Sabatier‑volcano descriptors.

**Independent Test**: The model training can be tested by running the script and verifying that both the XGBoost and linear models produce predictions on the hold‑out test set with calculated R² and MAE metrics, and that the best hyper‑parameters are saved in `best_params.json`.

**Acceptance Scenarios**:

1. **Given** the preprocessed training set, **When** the 5‑fold cross‑validation grid search runs (max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, n_estimators ≤ 200), **Then** the hyper‑parameters maximizing cross‑validated R² are selected, saved to `best_params.json`, and the final model is saved as `best_xgboost.json`.  
2. **Given** the hold‑out test set, **When** both the XGBoost and linear baseline models generate predictions, **Then** the paired t‑test (α = 0.05) on absolute errors is computed if the Shapiro‑Wilk test (α = 0.05) indicates normality; otherwise a Wilcoxon signed‑rank test is used. The test statistic, p‑value, and decision are logged in `statistical_test.json`.  
3. **Given** the test set results, **When** the performance report is generated, **Then** it contains the Pearson R, MAE, and the p‑value for the error‑difference test, and the report is validated against `report_schema.json`.

---

### User Story US-3 - Feature Importance and Interpretability Analysis (Priority: P3)

As a domain expert, I need a SHAP‑based analysis that ranks the top descriptors by mean absolute impact and visualizes them, so that I can identify the physical determinants of catalytic activity.

**Why this priority**: This story provides the scientific insight required to answer the research question (“which specific descriptors provide the most predictive signal?”) and validates the hypothesis that a compact set captures the dominant physics.

**Independent Test**: The interpretability step can be tested by running the SHAP calculation and verifying that the top descriptors are listed in descending order of importance in `shap_rankings.csv` (checksum‑verified) and that a bar plot `shap_barplot.png` is generated.

**Acceptance Scenarios**:

1. **Given** the trained XGBoost model and test data, **When** SHAP values are computed, **Then** a ranked list of descriptors by mean absolute SHAP impact is produced and saved as `shap_rankings.csv`.  
2. **Given** the ranked descriptors, **When** the visualization script runs, **Then** a bar plot displaying the top descriptors is saved as `shap_barplot.png`.  
3. **Given** the top few descriptors, **When** the final report is compiled, **Then** it states whether these descriptors align with the Nørskov reference (d‑band center, activation barrier, reaction energy) or represent novel predictors, with the caveat that SHAP provides associative, not causal, insight.

---

### Edge Cases

- What happens when the Materials Project descriptor file is missing a specific catalyst composition? (Handled by k=5 imputation; if <5 neighbors exist, the entry is flagged and excluded from training).  
- How does the system handle experimental TOF values that are reported as “below detection limit”? (These entries are excluded from the regression training set but logged in a separate report).  
- What happens if the 5‑fold cross‑validation yields identical R² scores for multiple hyperparameter sets? (The set with the lowest n_estimators is selected to minimize overfitting risk).  
- What happens if an entry has missing descriptors but <5 neighbors exist in the reference set? (The entry is kept in the unified dataset but flagged and excluded from model training to prevent imputation failure).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the OC20 dataset, Materials Project bulk descriptors, and the recent CO₂ hydrogenation study dataset (Doe et al., 2025,) via `wget` and parse them into a unified Pandas DataFrame (See US-1). Verification: `checksums.txt` and `required_columns.json` must match, and the DataFrame must contain the required columns `catalyst_id, composition, surface_facet, synthesis_condition, d_band_center, p_band_center, bader_charges, activation_barrier, reaction_energy, experimental_tof, temperature, pressure`.  
- **FR-002**: System MUST align DFT entries to experimental TOFs using exact string matching on columns: `composition`, `surface_facet`, `synthesis_condition`, **and**, when available, `temperature` and `pressure`. Entries are excluded from the unified dataset if they cannot be aligned OR if `synthesis_condition` is not uniquely identifiable. If an entry is aligned but has missing descriptors with <5 neighbors in the reference set, it is flagged and excluded from model training (See US-1). Alignment success rate must be ≥ 0.80 and recorded in `alignment_metrics.json`.  
- **FR-003**: System MUST impute missing descriptor values using k‑nearest‑neighbors (k=5) based on Euclidean distance in stoichiometry space (normalized element counts), excluding the target variable (experimental_tof) from distance calculation. If fewer than 5 neighbors are found, the entry is flagged and excluded from model training. All numeric features must be scaled to zero mean and unit variance (See US-1); post‑scaling mean |μ| < 0.01 and |σ‑1| < 0.01 are logged in `scaling_report.json`.  
- **FR-004**: System MUST train a Gradient‑Boosted Regression Trees model (XGBoost) with a grid search over max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, and n_estimators ≤ 200, selecting the configuration that maximizes k‑fold cross‑validated R² (See US-2). The selected hyper‑parameters are saved to `best_params.json`.  
- **FR-005**: System MUST fit a linear regression baseline using only d‑band center and activation barrier, perform a Shapiro‑Wilk normality test (α = 0.05) on the distribution of absolute errors, and write the test statistic and p‑value to `normality_test.json`. Based on the p‑value, the system MUST select either a paired t‑test (if p ≥ 0.05) or a Wilcoxon signed‑rank test (if p < 0.05) and perform the chosen test on the absolute errors of the XGBoost and baseline models on the hold‑out test set. The test statistic, p‑value, and the name of the test used are recorded in `statistical_test.json`.  
- **FR-006**: System MUST compute SHAP values for the final XGBoost model, rank descriptors by mean absolute SHAP impact, and generate a bar plot of the top descriptors (See US-3). SHAP rankings are saved as `shap_rankings.csv` (checksum‑verified) and the plot as `shap_barplot.png`. SHAP values are interpreted as associative importance only, not causal evidence.  
- **FR-007**: System MUST output a final report (`report.md`) containing the Pearson R, MAE, the statistical‑test p‑value, and the ranked list of top 5 descriptors. The report must compare the top descriptors against the reference list in Nørskov et al. (d‑band center, activation barrier, reaction energy) and explicitly state matches or novel findings (See US-3). The report must validate against `report_schema.json`.  
- **FR-008**: System MUST declare the model improvement “significant” only when **both** (a) the paired‑test (or Wilcoxon) p‑value < 0.05 **and** (b) the reduction in MAE on the log‑TOF scale ΔMAE ≥ 0.1 (log‑TOF units) (See US-2, US-3). The decision is recorded in `performance_summary.json`.  
- **FR-009**: System MUST control for experimental condition confounders by requiring that temperature and pressure values be identical between a DFT entry and its matched experimental TOF before alignment; mismatched entries are excluded and logged. (See US-1).  
- **FR-010**: System MUST reserve a held‑out test set comprising **[deferred]** of the unified dataset *prior* to any hyper‑parameter tuning. This test set is never used during grid‑search or cross‑validation to prevent data leakage. (See US-2).
- **FR-011**: System MUST generate the unified CSV (`aligned_dataset.csv`) that conforms to `aligned_dataset.schema.yaml`. The schema is the authoritative source of truth for dataset structure; `dataset.schema.yaml` is deprecated. The schema will be extended to include all descriptor columns used in the study (e.g., `p_band_center`, `bader_charges`, `reaction_energy`) and will set `additionalProperties: true` to accommodate future extensions. (See US-1).

### Key Entities

- **CatalystEntry**: Represents a unique catalyst configuration; attributes include `composition`, `surface_facet`, `synthesis_condition`, `temperature`, `pressure`, `d_band_center`, `p_band_center`, `bader_charges`, `activation_barrier`, `reaction_energy`, `experimental_tof`.  
- **ModelMetrics**: Stores performance statistics; attributes include `model_type`, `r_squared`, `mean_absolute_error`, `pearson_r`, `t_test_p_value`.  
- **FeatureImportance**: Represents descriptor impact; attributes include `descriptor_name`, `mean_absolute_shap_value`, `rank`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (Pearson R and MAE) of the XGBoost model is measured against the linear baseline model on the hold‑out test set. Improvement is declared **significant** if the paired test p‑value < 0.05 **and** ΔMAE ≥ 0.1 log‑TOF (minimum important difference). Additionally, the XGBoost model must achieve **Pearson R ≥ 0.80** and **MAE ≤ 20 %** of the experimental TOF range to satisfy the original scientific goal.  
- **SC-002**: The alignment success rate (matched entries / total experimental entries) is measured and must be ≥ 0.80 (See FR‑002).  
- **SC-003**: The combined significance rule from FR‑008 must be satisfied for the result to be reported as a meaningful improvement.  
- **SC-004**: The computational runtime of the full pipeline (download to report generation) is measured and must be ≤ 6 hours (≤ 21600 seconds). Runtime is captured in `metrics.json` as `total_seconds`.  
- **SC-005**: The statistical significance of the model improvement is measured against the α = 0.05 threshold using the paired t‑test or Wilcoxon signed‑rank test (See FR‑005).  
- **SC-006**: No data leakage: the held‑out test set (FR‑010) must remain untouched during hyper‑parameter selection; verification is performed by confirming that `best_params.json` was generated without accessing `test_set/*.csv`.  
- **SC-007**: SHAP‑based descriptor rankings are reported as associative evidence only; the report must contain a disclaimer that causality is not implied.

## Assumptions

- The Materials Project bulk descriptor CSV contains valid d‑band center, p‑band center, and Bader charge values for the catalyst compositions present in the OC20 dataset.  
- The experimental TOF values in the 2025 CO₂ hydrogenation study are reported in consistent units (e.g., s⁻¹) and do not require unit conversion.  
- The OC20 dataset and Materials Project data can be downloaded and stored within the disk limit of the free‑tier runner.  
- The k‑nearest‑neighbor imputation (k=5) is sufficient to handle missing values without introducing significant bias, as the dataset is assumed to be dense in composition space. Entries with fewer than 5 neighbors are excluded from model training to avoid bias.  
- The XGBoost model with n_estimators ≤ 200 and default precision will complete training within the ≤ 6 hour time limit on CPU cores.  
- The paired t‑test assumption of normality for the distribution of absolute errors is checked; if not met, a non‑parametric alternative (Wilcoxon signed‑rank test) is used as documented in FR‑005.  
- The “2025 CO₂ hydrogenation study” dataset is publicly available as supplementary material of the referenced publication and is stable at the provided DOI.  
- The d‑band center and activation barrier are definitionally distinct from other descriptors; multicollinearity diagnostics will be performed but are not expected to prevent model training.  
- The target of ≥ 1500 matched entries is based on a power analysis capable of detecting an R² increase of 0.05 with 80 % power at α = 0.05 (see Cohen, *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., 1988). If fewer entries are available (but ≥ 500), the analysis proceeds with the available data, noting reduced power.  
- Temperature and pressure are required to match exactly between computational and experimental records to avoid confounding (see FR‑009).  
- The SHAP interpretation is limited to associative insights; causal claims are expressly avoided (see SC‑007).  
