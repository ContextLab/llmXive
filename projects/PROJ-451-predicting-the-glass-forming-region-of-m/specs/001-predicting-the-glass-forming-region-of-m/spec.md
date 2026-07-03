# Feature Specification: Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

**Feature Branch**: `001-gfr-ml-prediction`  
**Created**: 2025-06-15  
**Status**: Draft  
**Input**: User description: "Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Feature Engineering (Priority: P1)

The research pipeline MUST load alloy composition data from the designated sources (Science Advances supplementary materials and Materials Project API), compute atomic-scale descriptors (atomic radius, electronegativity, valence electron concentration, atomic size mismatch, mixing enthalpy), and output a structured dataset ready for model training.

**Why this priority**: Without validated input data and correctly computed descriptors, no downstream analysis is possible. This is the foundational step that enables all subsequent modeling work.

**Independent Test**: Can be fully tested by verifying that the output dataset contains ≥1000 alloy compositions with ≥10 computed descriptors per composition, and that descriptor values fall within physically reasonable ranges (e.g., atomic size mismatch ∈ [, 1], electronegativity difference ∈ [, 3]).

**Acceptance Scenarios**:

1. **Given** a valid alloy composition dataset from the Science Advances supplementary materials, **When** the feature engineering module processes the data, **Then** the output dataset contains all required atomic descriptors with no missing values for ≥95% of compositions.
2. **Given** a Materials Project API endpoint returning alloy properties, **When** the ingestion module fetches data, **Then** the fetched records are merged with the primary dataset without duplication (verified by unique composition ID count).

---

### User Story 2 - Model Training and Performance Validation (Priority: P2)

The research pipeline MUST train Random Forest and XGBoost classifiers on the engineered dataset using -fold cross-validation, stratified by alloy system, and compare their performance against a baseline logistic regression classifier (representing traditional atomic size rules) and against each other.

**Why this priority**: This is the core analytical capability that directly addresses the research question. Performance metrics determine whether compositional descriptors encode sufficient physics to distinguish amorphous from crystalline phases, and whether non-linear models outperform linear baselines.

**Independent Test**: Can be fully tested by executing the training pipeline on a subset of compositions and verifying that the system calculates balanced accuracy, precision, recall, and F1-score for all models, and executes the statistical comparison test (paired t-test) to report p-values.

**Acceptance Scenarios**:

1. **Given** a stratified train-test split (majority/minority by alloy system), **When** the Random Forest model trains with 5-fold cross-validation, **Then** the system reports the mean balanced accuracy across folds.
2. **Given** the same stratified split, **When** the XGBoost model trains with 5-fold cross-validation, **Then** the system reports the mean balanced accuracy across folds.
3. **Given** the baseline logistic regression model, **When** it trains with 5-fold cross-validation, **Then** the system reports its balanced accuracy to establish the performance of traditional linear rules.
4. **Given** the trained models, **When** performance is compared via paired t-test on fold-level scores, **Then** the system reports the p-value indicating whether non-linear models significantly outperform the linear baseline (α = 0.05).

---

### User Story 3 - Interpretability and Visualization (Priority: P3)

The research pipeline MUST extract permutation importance scores for all descriptors and generate SHAP (SHapley Additive exPlanations) plots showing how specific descriptor values shift the predicted probability of glass formation.

**Why this priority**: This provides scientific insight into which physicochemical interactions most strongly control glass formation, informing alloy design decisions. This is valuable but secondary to establishing baseline predictive performance.

**Independent Test**: Can be fully tested by verifying that SHAP plots are generated for the top 5 most important descriptors and that permutation importance scores are non-negative and sum to 1.0 (normalized).

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model on ≥500 compositions, **When** permutation importance is computed, **Then** the system reports the top 3 descriptors and their contribution percentages.
2. **Given** the trained model, **When** SHAP values are computed for a held-out test composition, **Then** the SHAP summary plot displays at least 10 compositions with non-overlapping feature value distributions.

---

### Edge Cases

- What happens when the The Materials Project API returns a limited set of alloy compositions. (insufficient for stratified splitting)?
- How does the system handle compositions with missing elemental property values (e.g., unknown electronegativity for rare earths)?
- What is the behavior when the paired t-test returns p = 0.05 exactly (boundary condition for significance)?
- How does the pipeline handle alloy systems with a limited number of samples (insufficient for meaningful stratification)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load alloy composition data from the Science Advances supplementary materials (DOI: 10.1126/sciadv.aaq1566) and Materials Project API, ensuring all required elemental properties (atomic radius, electronegativity, valence electron concentration) are present for ≥95% of compositions (See US-1)
- **FR-002**: System MUST compute atomic-scale interaction descriptors including atomic size mismatch (δ), electronegativity difference (Δχ), and mixing enthalpy (ΔHmix) for each alloy composition using standard thermodynamic formulas (See US-1)
- **FR-003**: System MUST partition the dataset into [deferred] training and [deferred] test sets, stratified by alloy system (e.g., Zr-Cu-Al vs. Mg-Cu-Y) to ensure generalization testing across chemistries (See US-2)
- **FR-004**: System MUST train both Random Forest and XGBoost classifiers using scikit-learn and xgboost libraries, optimizing hyperparameters via k-fold cross-validation with balanced accuracy as the primary metric (See US-2)
- **FR-005**: System MUST apply a paired t-test to compare model performance against a baseline logistic regression classifier (representing traditional atomic size rules), reporting p-value at α = 0.05 significance threshold (See US-2)
- **FR-006**: System MUST extract permutation importance scores for all descriptors and generate SHAP summary plots for the top 5 most influential features (See US-3)
- **FR-007**: System MUST enforce a dataset size cap of ≤10,000 compositions to ensure all analysis runs within 7 GB RAM and 6 hours on a 2-core CPU runner (See US-2)
- **FR-008**: System MUST apply Bonferroni correction for multiple hypothesis testing when comparing more than 2 model configurations (family-wise error rate ≤ 0.05) (See US-2)
- **FR-009**: System MUST exclude any alloy composition lacking a definitive phase label (amorphous/crystalline) from training and testing. Compositions with ambiguous or missing labels (expected proportion < 2%) MUST be dropped to ensure ≥98% label completeness in the final dataset (See US-1)
- **FR-010**: System MUST deduplicate compositions across sources by unique chemical formula (normalized atomic fractions). If duplicate compositions exist across Science Advances and Materials Project, the system MUST retain the record from the primary source (Science Advances) and discard the secondary record. This ensures a unique dataset of ≥1000 compositions (See US-1)

### Key Entities

- **AlloyComposition**: Represents a specific metallic glass alloy with elemental fractions (e.g., Zr₅₀Cu₃₅Al₁₅), phase label (amorphous/crystalline), and source metadata
- **AtomicDescriptor**: Represents a computed feature value (e.g., atomic size mismatch = 0.08) associated with a specific AlloyComposition
- **ModelPerformance**: Captures balanced accuracy, precision, recall, and F1-score metrics for a trained classifier on a specific dataset split

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Balanced accuracy of Random Forest and XGBoost models is measured against a baseline logistic regression classifier (representing traditional atomic size rules) using a paired t-test (See US-2)
- **SC-002**: Feature importance rankings from permutation analysis are measured against novel descriptor contributions and non-linear interactions to validate scientific insight (See US-3)
- **SC-003**: Dataset size (number of alloy compositions) is measured against the [deferred] composition cap defined in FR-007 to ensure CPU-only execution (See US-2)
- **SC-004**: Cross-validation standard deviation of balanced accuracy is measured against a predefined threshold to verify model stability across alloy systems. (See US-2)
- **SC-005**: Mean balanced accuracy on the held-out test set is measured against a target of ≥75% to validate the research hypothesis regarding predictive capability (See US-2)
- **SC-006**: Concentration of feature importance (top 3 descriptors) is measured against a target of ≥60% to assess model interpretability and dominant physics (See US-3)

## Assumptions

- The Science Advances supplementary materials (DOI: 10.1126/sciadv.aaq1566) contain ≥1000 alloy compositions with both compositional data and phase labels (amorphous/crystalline)
- The Materials Project API provides elemental properties (atomic radius, electronegativity, valence electron concentration) for ≥95% of elements appearing in the alloy compositions
- Atomic size mismatch (δ), electronegativity difference (Δχ), and mixing enthalpy (ΔHmix) are sufficient descriptors to capture non-linear interactions governing glass formation
- The dataset is sufficiently balanced (≥40% amorphous, ≥40% crystalline) to enable stratified splitting without severe class imbalance
- All analysis will use single-precision floating-point arithmetic (no GPU/CUDA requirements) to maintain CPU-only feasibility
- The 5-fold cross-validation stratification by alloy system will result in ≥50 samples per fold for each major alloy family (Zr-based, Mg-based, etc.)
- Mixing enthalpy (ΔHmix) values are NOT included in the source datasets; the system MUST compute them from elemental properties using standard thermodynamic formulas (See US-1).