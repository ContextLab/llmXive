# Feature Specification: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Feature Branch**: `001-predict-solder-hardness`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1)

A materials scientist can aggregate published Vickers hardness measurements and compositional data for ≥50 unique solder alloy compositions from open sources (Materials Project, NIST, OpenAlloy, published literature) into a unified dataset, with validation that each record contains complete elemental composition and corresponding room-temperature hardness values.

**Why this priority**: This is the foundational data layer; without ≥50 validated records, no predictive modeling can proceed. This represents the minimum viable research artifact.

**Independent Test**: Can be fully tested by executing the data ingestion pipeline and verifying the output dataset contains ≥50 unique compositions with non-null hardness values and complete elemental breakdowns.

**Acceptance Scenarios**:

1. **Given** access to Materials Project, NIST, and OpenAlloy APIs, **When** the ingestion pipeline runs, **Then** ≥50 unique solder compositions with Vickers hardness measurements are collected into the unified dataset
2. **Given** the aggregated dataset, **When** validation checks run, **Then** [deferred] of records contain non-null hardness values and elemental compositions summing to ≥95% of total alloy composition

---

### User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

A materials scientist can train gradient boosting (XGBoost) and linear regression models on the aggregated dataset using 5-fold cross-validation, with performance comparison via paired t-test on cross-validation folds and feature importance analysis via SHAP values.

**Why this priority**: This delivers the core predictive capability and identifies dominant compositional drivers, representing the primary research contribution.

**Independent Test**: Can be fully tested by running model training on the dataset and verifying cross-validation metrics (R², RMSE) are computed and feature importance rankings are generated.

**Acceptance Scenarios**:

1. **Given** the validated dataset from US-001, **When** model training completes, **Then** both XGBoost and linear regression models produce cross-validated R² scores with 95% confidence intervals via 1000 bootstrap resamples
2. **Given** trained models, **When** feature importance analysis runs, **Then** SHAP values identify the top 3 compositional features (e.g., electronegativity variance, atomic radius variance, weighted mean atomic mass) with ranked contribution scores

---

### User Story 3 - Generate interpretable visualizations and partial dependence plots (Priority: P3)

A materials scientist can generate a scatter plot of predicted vs. measured hardness with error bars and partial dependence plots for the top 3 features, enabling visual inspection of the composition-hardness relationship.

**Why this priority**: Visualization supports interpretation and publication; it is valuable but not required for model training to succeed.

**Independent Test**: Can be fully tested by executing the visualization pipeline and verifying output files (scatter plot, 3 partial dependence plots) are generated with correct axis labels and units.

**Acceptance Scenarios**:

1. **Given** trained model predictions on the test set, **When** the visualization pipeline runs, **Then** a scatter plot is generated with predicted vs. measured hardness, including 95% confidence interval error bars
2. **Given** SHAP feature importance rankings, **When** partial dependence analysis runs, **Then** 3 partial dependence plots are generated showing the relationship between each top feature and predicted hardness

---

### Edge Cases

- What happens when the aggregated dataset contains <50 unique compositions after filtering? → System flags `[NEEDS CLARIFICATION: proceed with reduced N or halt?]` and reports power limitation
- How does system handle alloys with >5 elements? → System excludes them from the dataset per the methodology constraint to reduce feature complexity
- What happens when hardness measurements come from different testing protocols (e.g., different load forces)? → System standardizes to HV units and flags measurements requiring conversion for manual review

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST aggregate ≥50 unique solder alloy compositions with Vickers hardness measurements from Materials Project, NIST, OpenAlloy, and published literature (See US-001)
- **FR-002**: System MUST validate that [deferred] of dataset records contain non-null hardness values and elemental compositions summing to ≥95% of total alloy composition (See US-001)
- **FR-003**: System MUST compute compositional descriptors including weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration (See US-002)
- **FR-004**: System MUST train both XGBoost gradient boosting regressor and linear regression baseline using 5-fold cross-validation with hyperparameter grid limited to ≤10 combinations (See US-002)
- **FR-005**: System MUST report model performance metrics (R², RMSE) with 95% confidence intervals via 1000 bootstrap resamples on held-out test set (See US-002)
- **FR-006**: System MUST generate SHAP-based feature importance rankings identifying the top 3 compositional drivers (See US-002)
- **FR-007**: System MUST frame all composition-hardness findings as ASSOCIATIONAL rather than causal, given the observational nature of the dataset (See US-002)
- **FR-008**: System MUST apply family-wise error rate correction when comparing model performance across multiple cross-validation folds (See US-002)
- **FR-009**: System MUST include a sensitivity analysis that sweeps the R² performance threshold over {0.5, 0.6, 0.7} and reports how test-set pass rates vary across it (See US-002)
- **FR-010**: System MUST run all computations on CPU-only infrastructure without GPU, CUDA, or accelerator dependencies (See Assumptions)
- **FR-011**: System MUST ensure total dataset size fits within ~7 GB RAM and ~14 GB disk, with sampling if needed (See Assumptions)
- **FR-012**: System MUST complete full analysis pipeline within ≤6 hours of CPU time on GitHub Actions free-tier runner (See Assumptions)
- **FR-013**: System MUST diagnose and report predictor collinearity (e.g., VIF scores ≥5) when compositional features are definitionally related (See US-002)

### Key Entities

- **SolderComposition**: Represents a unique solder alloy with attributes: elemental breakdown (e.g., Sn: [deferred], Pb: [deferred]), room-temperature Vickers hardness (HV or GPa), alloy family classification (Sn-Pb, Sn-Ag-Cu, Sn-Zn, etc.), data source citation
- **CompositionalDescriptor**: Represents engineered features derived from elemental properties: weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, valence electron concentration
- **ModelPerformance**: Represents cross-validation and test-set metrics: R², RMSE, 95% confidence intervals, feature importance rankings (SHAP values)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Cross-validated R² performance is measured against the null baseline (mean predictor) on held-out test set (See US-002)
- **SC-002**: Model comparison significance is measured against paired t-test on 5 cross-validation folds with family-wise error rate correction (See US-002)
- **SC-003**: Feature importance rankings are measured against SHAP value magnitudes identifying top 3 compositional drivers (See US-002)
- **SC-004**: Dataset completeness is measured against the ≥50 unique compositions target with [deferred] non-null hardness validation (See US-001)
- **SC-005**: Sensitivity analysis outcomes are measured against R² threshold sweep {0.5, 0.6, 0.7} reporting pass rate variation (See US-002)
- **SC-006**: Collinearity diagnostics are measured against VIF scores ≥5 for definitionally related predictors (See US-002)
- **SC-007**: Compute feasibility is measured against ≤6 hours CPU time, ~7 GB RAM, ~14 GB disk on free-tier runner (See Assumptions)

## Assumptions

- **Assumption about data availability**: Public materials databases (Materials Project, NIST, OpenAlloy) and published literature contain ≥50 unique solder compositions with Vickers hardness measurements and complete elemental breakdowns; if <50 records are available, the project proceeds with reduced N and explicitly reports power limitation
- **Assumption about measurement validity**: Vickers hardness measurements in the aggregated dataset come from validated testing protocols with citable sources; measurements from non-standardized protocols are excluded or flagged for manual review
- **Assumption about scope boundaries**: Alloys with >5 elements are excluded to reduce feature complexity; room-temperature measurements only are included (thermal cycling effects are out of scope)
- **Assumption about compute constraints**: All model training and inference runs on CPU-only infrastructure (no GPU, CUDA, bitsandbytes, or accelerator dependencies); XGBoost and linear regression are selected as CPU-tractable methods
- **Assumption about inference framing**: The composition-hardness relationship is framed as associational (not causal) given the observational nature of the aggregated dataset; randomization or identification strategies are not present
- **Assumption about threshold justification**: The R² ≥ 0.6 target follows community-standard benchmarks for materials property prediction models; sensitivity analysis sweeps {0.5, 0.6, 0.7} to verify robustness
- **Assumption about predictor collinearity**: Compositional features (e.g., atomic mass, atomic radius, electronegativity) may exhibit definitional correlation; collinearity diagnostics (VIF) are required to frame joint relationships descriptively rather than claiming independent effects
- **Assumption about dataset-variable fit**: The aggregated datasets contain all required variables (elemental composition, Vickers hardness, elemental property tables for descriptor computation); `[NEEDS CLARIFICATION: does the aggregated dataset contain post-processing history variables if microstructure effects are significant?]`

## Related Work

- [Deep Learning-Driven Microstructure Characterization and Vickers Hardness Prediction of Mg-Gd Alloys (2024)](http://arxiv.org/abs/2410.20402v1) — Establishes that deep learning can predict hardness from composition and microstructure in Mg-Gd systems, demonstrating the general feasibility of composition-to-property ML models in metallurgy.
