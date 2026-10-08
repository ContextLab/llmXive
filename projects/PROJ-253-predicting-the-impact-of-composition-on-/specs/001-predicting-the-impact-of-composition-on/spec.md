# Feature Specification: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

**Feature Branch**: `001-predicting-composition-band-gap`  
**Created**: 2026-08-05  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Band Gap of Perovskite Materials"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Compositional Feature Generation (Priority: P1)

The researcher needs to automatically retrieve a curated dataset of perovskite formulas and DFT-calculated band gaps, then transform these raw chemical formulas into a set of quantitative compositional descriptors (e.g., electronegativity variance, Goldschmidt tolerance factor) to serve as model inputs.

**Why this priority**: This is the foundational step; without valid, preprocessed features derived from composition, no predictive modeling or scientific inference can occur. It establishes the data integrity required for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains the original formulas alongside exactly 15-20 derived compositional columns, with zero missing values in the target band gap column and no physically impossible values (<0 or >6 eV).

**Acceptance Scenarios**:

1. **Given** a valid Materials Project API key or Zenodo mirror URL, **When** the data ingestion script runs, **Then** it must download at least 500 unique perovskite entries with complete elemental composition and a valid band gap value.
2. **Given** a dataset containing raw chemical formulas (e.g., "CsPbI3"), **When** the feature engineering module processes them, **Then** it must generate at least 5 distinct compositional descriptors (mean electronegativity, variance of atomic radius, tolerance factor, etc.) for every row.
3. **Given** a dataset with entries having band gaps <0 eV or >6 eV, **When** the preprocessing filter runs, **Then** those specific entries must be removed, and the final dataset must contain only values within the [0.0, 6.0] eV range.

---

### User Story 2 - Composition-Only Model Training and Validation (Priority: P2)

The researcher needs to train a Random Forest and Gradient Boosting regressor using only the compositional descriptors to predict band gaps, performing hyperparameter tuning via 5-fold cross-validation, and evaluating performance against a mean baseline.

**Why this priority**: This implements the core hypothesis testing mechanism. It determines whether composition alone is sufficient to predict the property, directly addressing the research question's accuracy component.

**Independent Test**: Can be fully tested by running the training script and confirming that the model achieves a test-set R² > 0.0 (outperforming a mean baseline) and that the RMSE is calculated and logged for both the Random Forest and Gradient Boosting models.

**Acceptance Scenarios**:

1. **Given** the preprocessed feature matrix and target vector, **When** the 5-fold cross-validation loop executes, **Then** it must select the hyperparameters (number of trees, max depth) that yield the lowest mean RMSE across folds.
2. **Given** a trained model and a held-out test set, **When** the evaluation metric is computed, **Then** the system must report the RMSE, MAE, and R² values, and the Random Forest model must show an R² score strictly greater than the baseline mean predictor.
3. **Given** multiple hypothesis tests are performed (e.g., comparing RF vs. GB), **When** the statistical comparison runs, **Then** it must apply a multiple-comparison correction (e.g., Bonferroni or Holm) to the p-values before declaring a significant difference between models.

---

### User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

The researcher needs to interpret the trained model to identify which compositional descriptors most strongly influence band gaps (via SHAP or feature importance) and validate the model's ranking capability against a separate experimental dataset.

**Why this priority**: This provides the scientific insight (which descriptors govern the gap) and ensures the model captures physical reality rather than DFT artifacts, addressing the "mechanism" part of the research question.

**Independent Test**: Can be fully tested by generating a SHAP summary plot (or equivalent importance list) and verifying that the model's predicted ranking of a small set of experimental compounds correlates positively (Spearman rho > 0.5) with their known experimental band gaps.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the interpretability module runs, **Then** it must output a ranked list of the top 5 most important compositional descriptors and generate a visualization (SHAP summary) showing their impact direction.
2. **Given** a separate experimental dataset (e.g., from NREL) not used in training, **When** the model predicts band gaps for these entries, **Then** the Spearman rank correlation between predicted and experimental values must be calculated and reported.
3. **Given** a decision threshold for "high-accuracy" prediction (e.g., error < 0.35 eV), **When** the sensitivity analysis runs, **Then** it must sweep this threshold over {0.30, 0.35, 0.40} eV and report the variation in the false-negative rate for identifying lead-free candidates.

### Edge Cases

- What happens when the dataset contains a perovskite formula with an element not present in the `matminer` elemental property database? (System must log a warning and exclude that specific entry rather than crashing).
- How does the system handle a scenario where the DFT-calculated band gap is exactly 0 eV (metallic) but the entry is labeled as a perovskite semiconductor? (System must include it but flag it as a potential outlier for manual review if the distribution is bimodal).
- What occurs if the external experimental validation dataset is too small (<10 entries) to compute a statistically significant correlation? (System must report the correlation coefficient but mark the p-value as "insufficient sample size" rather than claiming significance).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the perovskite subset from the Materials Project (via API or Zenodo mirror) containing chemical formulas and DFT-calculated band gaps. (See US-1)
- **FR-002**: System MUST generate compositional descriptors using `matminer`, specifically calculating mean/variance of electronegativity, atomic radius, and ionization energy, plus the Goldschmidt tolerance factor. (See US-1)
- **FR-003**: System MUST filter the dataset to remove entries with band gaps outside the physically valid range of [0.0, 6.0] eV. (See US-1)
- **FR-004**: System MUST train both a Random Forest Regressor and a Gradient Boosting Regressor, performing 5-fold cross-validation for hyperparameter tuning on the training set. (See US-2)
- **FR-005**: System MUST evaluate model performance using RMSE, MAE, and R² on a held-out test set and compare results against a mean baseline predictor using a paired t-test with multiple-comparison correction. (See US-2)
- **FR-006**: System MUST extract feature importances from the Random Forest model and generate SHAP summary plots to identify top descriptors. (See US-3)
- **FR-007**: System MUST validate model ranking capability against a separate, held-out experimental dataset (e.g., NREL) using Spearman rank correlation. (See US-3)
- **FR-008**: System MUST perform a sensitivity analysis on the prediction error threshold, sweeping the cutoff over {0.30, 0.35, 0.40} eV and reporting the resulting variation in false-negative rates. (See US-3)

### Key Entities

- **PerovskiteEntry**: Represents a single material instance; key attributes include chemical_formula, dft_band_gap (eV), experimental_band_gap (eV, optional), and derived_compositional_features (vector).
- **ModelConfig**: Represents the configuration for a trained model; key attributes include model_type (RF/GB), hyperparameters (n_trees, max_depth), and training_metrics (cv_rmse, cv_r2).
- **FeatureImportance**: Represents the contribution of a descriptor; key attributes include descriptor_name, importance_score, and shap_value_range.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The test-set RMSE of the best-performing composition-only model is measured against the target of ≤ 0.35 eV (derived from the idea's expected results). (See US-2)
- **SC-002**: The R² score of the trained model is measured against the baseline mean predictor to confirm a statistically significant improvement (p < 0.05 after correction). (See US-2)
- **SC-003**: The Spearman rank correlation between model predictions and external experimental band gaps is measured against the literature baseline to verify the model captures physical trends rather than DFT artifacts. (See US-3)
- **SC-004**: The false-negative rate for identifying lead-free candidates is measured across the sensitivity sweep (thresholds 0.30, 0.35, 0.40 eV) to quantify the stability of the "high-accuracy" classification. (See US-3)
- **SC-005**: The variance in band gaps explained by the top 5 compositional descriptors is measured against the total variance to confirm >80% explanatory power. (See US-3)

## Assumptions

- **Assumption about data availability**: The Materials Project API or Zenodo mirror provides a dataset with at least 500 entries containing both valid chemical formulas and DFT-calculated band gaps sufficient for training a Random Forest model without overfitting.
- **Assumption about computational limits**: The entire pipeline (data download, feature engineering, model training, and validation) can complete within the GitHub Actions free-tier limits (2 CPU cores, ~7 GB RAM, 6 hours) without requiring GPU acceleration or large-model inference.
- **Assumption about compositional sufficiency**: The physical properties of perovskite band gaps are sufficiently correlated with bulk compositional descriptors (electronegativity, ionic radii) such that a model trained on these features can achieve the target RMSE of ≤ 0.35 eV, even without explicit structural data (e.g., lattice constants).
- **Assumption about external validation data**: A separate experimental dataset (e.g., from NREL) with at least 20 unique perovskite entries and measured band gaps is available to serve as a hold-out set for ranking validation.
- **Assumption about inference framing**: Since the data is observational (no random assignment of elements), all findings regarding "governing descriptors" will be framed as associational correlations rather than causal mechanisms, unless the specific dataset includes randomized synthesis conditions (which is assumed not to be the case).
- **Assumption about threshold justification**: The sensitivity analysis sweep thresholds {0.30, 0.35, 0.40} eV are chosen based on the community standard for "acceptable" DFT error margins in high-throughput screening, as referenced in the idea's expected results.
