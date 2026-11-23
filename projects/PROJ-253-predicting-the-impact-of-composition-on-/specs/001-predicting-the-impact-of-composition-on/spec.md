# Feature Specification: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

**Feature Branch**: `001-predicting-composition-band-gap`  
**Created**: 2026-08-05  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Band Gap of Perovskite Materials"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Compositional Feature Generation (Priority: P1)

The researcher needs to automatically retrieve a curated dataset of perovskite formulas and DFT-calculated band gaps, then transform these raw chemical formulas into a set of quantitative compositional descriptors (e.g., electronegativity variance, Goldschmidt tolerance factor) to serve as model inputs.

**Why this priority**: This is the foundational step; without valid, preprocessed features derived from composition, no predictive modeling or scientific inference can occur. It establishes the data integrity required for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains the original formulas alongside **at least 5 distinct compositional descriptors** (mean electronegativity, variance of atomic radius, tolerance factor, oxidation‑state variance, octahedral factor), with zero missing values in the target band gap column and no physically impossible values (band gap ≤ 0 eV or ≥ 6 eV).

**Acceptance Scenarios**:

1. **Given** a valid Materials Project API key or Zenodo mirror URL, **When** the data ingestion script runs, **Then** it must download at least 500 unique perovskite entries with complete elemental composition and a valid band gap value.
2. **Given** a dataset containing raw chemical formulas (e.g., "CsPbI3"), **When** the feature engineering module processes them, **Then** it must generate at least 5 distinct compositional descriptors (mean electronegativity, variance of atomic radius, tolerance factor, oxidation‑state variance, octahedral factor) for every row.
3. **Given** a dataset with entries having band gaps ≤ 0 eV or ≥ 6 eV, **When** the preprocessing filter runs, **Then** those specific entries must be removed, and the final dataset must contain only values within the **strict** range (0 < band gap < 6 eV).

### User Story 2 - Composition-Only Model Training and Validation (Priority: P2)

The researcher needs to train a Random Forest and Gradient Boosting regressor using only the compositional descriptors to predict band gaps, performing hyperparameter tuning via 5-fold cross-validation, and evaluating performance against a mean baseline.

**Why this priority**: This implements the core hypothesis testing mechanism. It determines whether composition alone is sufficient to predict the property, directly addressing the research question's accuracy component.

**Independent Test**: Can be fully tested by running the training script and confirming that the model achieves a test‑set R² > 0.0 (sanity‑check against a mean baseline) **and** that the statistical comparison shows a **significant** improvement (p < 0.05 after multiple‑comparison correction).

**Acceptance Scenarios**:

1. **Given** the preprocessed feature matrix and target vector, **When** the 5-fold cross-validation loop executes, **Then** it must select the hyperparameters (number of trees, max depth, learning rate for Gradient Boosting) that yield the lowest mean RMSE across folds.
2. **Given** a trained model and a held‑out test set, **When** the evaluation metric is computed, **Then** the system must report the RMSE, MAE, and R² values, and the Random Forest model must show an R² that is **statistically significantly greater** than the baseline mean predictor (p < 0.05 after correction).
3. **Given** multiple hypothesis tests are performed (e.g., comparing RF vs. GB), **When** the statistical comparison runs, **Then** it must apply a multiple‑comparison correction (e.g., Bonferroni or Holm) to the p‑values before declaring a significant difference between models.

### User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

The researcher needs to interpret the trained model to identify which compositional descriptors most strongly influence band gaps (via SHAP or feature importance) and validate the model's ranking capability against a separate experimental dataset.

**Why this priority**: This provides the scientific insight (which descriptors govern the gap) and ensures the model captures physical reality rather than DFT artifacts, addressing the "mechanism" part of the research question.

**Independent Test**: Can be fully tested by generating a SHAP summary plot (or equivalent importance list) and verifying that the model's predicted ranking of a small set of experimental compounds correlates positively (**Spearman ρ ≥ 0.5**) with their known experimental band gaps, **as reported in Jain et al., 2022**.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the interpretability module runs, **Then** it must output a ranked list of the most important compositional descriptors and generate a visualization (SHAP summary) showing their impact direction.
2. **Given** a separate experimental dataset (e.g., from NREL) not used in training, **When** the model predicts band gaps for these entries, **Then** the Spearman rank correlation between predicted and experimental values must be calculated and reported (ρ ≥ 0.5, see literature baseline).

### Edge Cases

- What happens when the dataset contains a perovskite formula with an element not present in the `matminer` elemental property database? **System must log a warning and exclude that specific entry** rather than crashing.
- How does the system handle a scenario where the DFT‑calculated band gap is exactly 0 eV (metallic) but the entry is labeled as a perovskite semiconductor? **System must log a warning and exclude the entry** (strict bounds enforced per Constitution VII).
- What occurs if the external experimental validation dataset is too small (<10 entries) to compute a statistically significant correlation? **System must report the correlation coefficient but mark the p‑value as “insufficient sample size”** rather than claiming significance.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the perovskite subset from the Materials Project (via API or a verified Zenodo perovskite collection) containing chemical formulas and DFT‑calculated band gaps, ensuring **≥ 500** entries after filtering. (See US-1)
- **FR-002**: System MUST generate compositional descriptors using `matminer`, specifically calculating mean/variance of electronegativity, atomic radius, ionization energy, **oxidation‑state variance**, and the Goldschmidt tolerance factor **plus the octahedral factor**. (See US-1)
- **FR-003**: System MUST filter the dataset to remove entries with band gaps **outside the strict range (0 < gap < 6 eV)**. (See US-1)
- **FR-004**: System MUST train both a Random Forest Regressor and a Gradient Boosting Regressor, performing 5‑fold cross‑validation for hyperparameter tuning on the training set. (See US-2)
- **FR-005**: System MUST evaluate model performance using RMSE, MAE, and R² on a held‑out test set and compare results against a mean baseline predictor using a **bootstrap‑based paired significance test** with multiple‑comparison correction. (See US-2)
- **FR-006**: System MUST extract feature importances from the Random Forest model and generate SHAP summary plots to identify top descriptors. (See US-3)
- **FR-007**: System MUST validate model ranking capability against a separate, held‑out experimental dataset (e.g., NREL) using Spearman rank correlation. (See US-3)
- **FR-008** (removed – out of scope)
- **FR-009**: System MUST log a warning and **exclude** any entry whose elemental composition includes an element absent from the `matminer` property database. (See US-1)
- **FR-010**: System MUST log a warning and **exclude** any entry with a band gap ≤ 0 eV (metallic) while still recording the occurrence for audit purposes. (See US-1)
- **FR-011**: System MUST report correlation coefficients for external validation even when the sample size < 10, but must annotate the p‑value as “insufficient sample size”. (See US-3)
- **FR-012**: System MUST standardize all compositional features to zero mean and unit variance **before** model training, including hyperparameter tuning, ensuring consistent preprocessing across all models. (See US-2)
- **FR-013**: System MUST split the curated dataset into stratified training ([deferred]), validation ([deferred]), and test ([deferred]) sets, preserving the distribution of band‑gap values across splits. (See US-2)
- **FR-014**: System MUST tune the learning rate hyperparameter for the Gradient Boosting Regressor during cross‑validation. (See US-2)
- **FR-015** (removed – out of scope)
- **FR-016**: System MUST quantify the explanatory power of the top‑5 descriptors (selected a priori based on established physical relevance: mean electronegativity, variance of atomic radius, Goldschmidt tolerance factor, octahedral factor, oxidation‑state variance) by fitting a secondary model using only those descriptors and reporting the resulting R²; this R² must be at least **[deferred] of the full‑model R²**. **Justified**: assessing whether a reduced, physically interpretable descriptor set retains most predictive performance isolates the truly governing features. (See US-3)
- **FR-017**: System MUST conduct a statistical power analysis for the external validation Spearman correlation, targeting **power ≥ 0.8 (80 %)** to detect ρ = 0.5 at α = 0.05, and must report the required sample size (≥ 30) and achieved power. (See US-3)
- **FR-018**: System MUST generate a comprehensive final report (PDF) summarizing dataset statistics, model performance metrics, feature‑importance results, sensitivity analysis outcomes, and external validation findings. (See US-3)
- **FR-019**: System MUST apply the zero‑mean, unit‑variance scaler to the feature matrix after descriptor generation and **before** any model training or hyperparameter tuning, ensuring consistent preprocessing across all models. (See US-2)
- **FR-020**: System MUST execute a reporting phase (Phase 11) that invokes FR‑018 to produce the final PDF deliverable. (See US-3)

### Key Entities

- **PerovskiteEntry**: Represents a single material instance; key attributes include chemical_formula, dft_band_gap (eV), experimental_band_gap (eV, optional), and derived_compositional_features (vector).
- **ModelConfig**: Represents the configuration for a trained model; key attributes include model_type (RF/GB), hyperparameters (n_trees, max_depth, learning_rate), and training_metrics (cv_rmse, cv_r2).
- **FeatureImportance**: Represents the contribution of a descriptor; key attributes include descriptor_name, importance_score, and shap_value_range.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The test‑set RMSE of the best‑performing composition‑only model is measured against the target of ≤ 0.35 eV (derived from the idea's expected results). (See US-2)
- **SC-002**: The R² score of the trained model is measured against the baseline mean predictor to confirm a **statistically significant improvement (p < 0.05 after correction)**. (See US-2)
- **SC-003**: The Spearman rank correlation between model predictions and external experimental band gaps must be ≥ 0.5 **and** the analysis must achieve ≥ 80 % statistical power (or report that the achieved power is below this target). The external dataset must contain **≥ 30** entries. (See US-3)
- **SC-004** (removed – out of scope)
- **SC-005**: The variance in band gaps explained by the top 5 compositional descriptors is measured as **≥ 80 % of the full‑model R²** using the refit‑R² method described in FR‑016. (See US-3)
- **SC-006**: The data acquisition pipeline must produce a cleaned CSV containing **≥ 500** perovskite entries, each with **≥ 5** compositional descriptors, and all band‑gap values within (0 eV, 6 eV). (See US-1)
- **SC-007**: The final report generated by FR‑018 must be a non‑empty PDF file stored at the designated output path and must include sections for dataset summary, model metrics, feature importance, sensitivity analysis, and external validation. (See US-3)

## Assumptions

- **Assumption about data availability**: The Materials Project API or a verified Zenodo perovskite collection provides a dataset with at least 500 entries containing both valid chemical formulas and DFT‑calculated band gaps sufficient for training a Random Forest model without overfitting.
- **Assumption about computational limits**: The entire pipeline (data download, feature engineering, model training, and validation) can complete within the GitHub Actions free‑tier limits (2 CPU cores, ~7 GB RAM, 6 hours) without requiring GPU acceleration or large‑model inference.
- **Assumption about compositional sufficiency**: The physical properties of perovskite band gaps are sufficiently correlated with bulk compositional descriptors (electronegativity, ionic radii, oxidation states, etc.) such that a model trained on these features can achieve the target RMSE of ≤ 0.35 eV, even without explicit structural data (e.g., lattice constants).
- **Assumption about external validation data**: A separate experimental dataset (e.g., from NREL) with at least 30 unique perovskite entries and measured band gaps is available to serve as a hold‑out set for ranking validation.
- **Assumption about inference framing**: Since the data is observational (no random assignment of elements), all findings regarding "governing descriptors" will be framed as associational correlations rather than causal mechanisms, unless the specific dataset includes randomized synthesis conditions (which is assumed not to be the case).
- **Assumption about threshold justification**: The sensitivity analysis sweep thresholds {0.30, 0.35, 0.40} eV are chosen based on the community standard for "acceptable" DFT error margins in high‑throughput screening, as referenced in the idea's expected results.