# Feature Specification: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Feature Branch**: `001-predict-solder-hardness`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1)

A materials scientist can aggregate published Vickers hardness measurements and compositional data for ≥100 unique solder alloy compositions from open sources (Materials Project, NIST, OpenAlloy, published literature, and systematic literature review) into a unified dataset, with validation that each record contains complete elemental composition and corresponding room-temperature hardness values. If <100 but ≥50 unique compositions are available, the system proceeds with the reduced N and explicitly reports the statistical power limitation in the final output.

**Why this priority**: This is the foundational data layer; without ≥100 validated records, no predictive modeling can proceed with sufficient statistical power for cross-validation comparisons. This represents the minimum viable research artifact.

**Independent Test**: Can be fully tested by executing the data ingestion pipeline on a GitHub Actions free-tier runner and verifying the output dataset contains ≥100 unique compositions with non-null hardness values and complete elemental breakdowns. If the dataset is between 50 and 100, the system must emit a specific warning.

**Acceptance Scenarios**:

1. **Given** access to Materials Project, NIST, OpenAlloy, and literature sources, **When** the ingestion pipeline runs, **Then** ≥100 unique solder compositions with Vickers hardness measurements are collected into the unified dataset
2. **Given** the aggregated dataset, **When** validation checks run, **Then** [deferred] of records contain non-null hardness values and elemental compositions summing to ≥95% of total alloy composition

---

### User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

A materials scientist can train gradient boosting (XGBoost) and linear regression models on the aggregated dataset using 5-fold cross-validation, with performance comparison via paired t-test on cross-validation folds and feature importance analysis via SHAP values. The system MUST also diagnose predictor collinearity using Variance Inflation Factor (VIF) scores.

**Why this priority**: This delivers the core predictive capability and identifies dominant compositional drivers, representing the primary research contribution.

**Independent Test**: Can be fully tested by running model training on the dataset and verifying cross-validation metrics (R², RMSE) are computed, VIF scores are reported, and feature importance rankings are generated.

**Acceptance Scenarios**:

1. **Given** the validated dataset from US-001, **When** model training completes, **Then** both XGBoost and linear regression models produce cross-validated R² scores with 95% confidence intervals via 1000 bootstrap resamples on the held-out test set
2. **Given** trained models, **When** feature importance analysis runs, **Then** SHAP values identify the top 3 compositional features (e.g., electronegativity variance, atomic radius variance, weighted mean atomic mass) with ranked contribution scores
3. **Given** the compositional descriptors, **When** collinearity diagnostics run, **Then** VIF scores are reported for all predictors, flagging any with VIF ≥ 5

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

- What happens when the aggregated dataset contains <50 unique compositions after filtering? → System emits warning: "Data volume below target (N < 50). Statistical power limited." and reports power limitation
- How does system handle alloys with >5 elements? → System excludes them from the dataset per the methodology constraint to reduce feature complexity
- What happens when hardness measurements come from different testing protocols (e.g., different load forces)? → System standardizes to HV units and flags measurements requiring conversion for manual review

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST aggregate ≥100 unique solder alloy compositions with Vickers hardness measurements from Materials Project, NIST, OpenAlloy, published literature, and systematic literature review. If <100 but ≥50 are available, the system MUST proceed and report a power limitation (See US-001)
- **FR-002**: System MUST validate that [deferred] of dataset records contain non-null hardness values and elemental compositions summing to ≥95% of total alloy composition (See US-001)
- **FR-003**: System MUST compute compositional descriptors including weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration on log-ratio transformed composition data (See US-002)
- **FR-004**: System MUST train both XGBoost gradient boosting regressor and linear regression baseline using k-fold cross-validation with hyperparameter grid limited to ≤10 combinations (See US-002)
- **FR-005**: System MUST report model performance metrics (R², RMSE) with confidence intervals via bootstrap resamples on held-out test set (See US-002)
- **FR-006**: System MUST generate SHAP-based feature importance rankings identifying the top 3 compositional drivers (See US-002)
- **FR-007**: System MUST frame all composition-hardness findings as ASSOCIATIONAL rather than causal, given the observational nature of the dataset (See US-002)
- **FR-009**: System MUST include a sensitivity analysis that sweeps the R² performance threshold over a range of values and reports the fraction of bootstrap samples where the model's R² exceeds each threshold. (See US-002)
- **FR-010**: System MUST run all computations on CPU-only infrastructure without GPU, CUDA, or accelerator dependencies (See US-001)
- **FR-011**: System MUST ensure total dataset size fits within available RAM and disk capacity, with sampling if needed (See US-001)
- **FR-012**: System MUST complete full analysis pipeline within ≤6 hours of CPU time on GitHub Actions free-tier runner (See US-001)
- **FR-013**: System MUST diagnose and report predictor collinearity (e.g., VIF scores ≥5) when compositional features are definitionally related (See US-002)
- **FR-014**: System MUST apply a centered log-ratio (CLR) transform to the elemental composition data before computing descriptors to address the compositional closure problem (See US-002)

### Key Entities

- **SolderComposition**: Represents a unique solder alloy with attributes: elemental breakdown (a map of element symbol to concentration percentage), room-temperature Vickers hardness (HV or GPa), alloy family classification (Sn-Pb, Sn-Ag-Cu, Sn-Zn, etc.), data source citation
- **CompositionalDescriptor**: Represents engineered features derived from elemental properties: weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, valence electron concentration
- **ModelPerformance**: Represents cross-validation and test-set metrics: R², RMSE, 95% confidence intervals, feature importance rankings (SHAP values)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Cross-validated R² performance is measured against the null baseline (mean predictor) on held-out test set (See US-002)
- **SC-002**: Model comparison significance is measured against paired t-test on 5 cross-validation folds (See US-002)
- **SC-003**: Feature importance rankings are measured against SHAP value magnitudes identifying top 3 compositional drivers (See US-002)
- **SC-004**: Dataset completeness is measured against the ≥100 unique compositions target with [deferred] non-null hardness validation (See US-001)
- **SC-005**: Sensitivity analysis outcomes are measured against R² threshold sweep {0.3, 0.5, 0.6, 0.7} reporting the fraction of bootstrap samples exceeding each threshold (See US-002)
- **SC-006**: Collinearity diagnostics are measured against VIF scores ≥5 for definitionally related predictors (See US-002)
- **SC-007**: Compute feasibility is measured against ≤6 hours CPU time, ~7 GB RAM, ~14 GB disk on free-tier runner (See Assumptions)

## Assumptions

- **Assumption about data availability**: Public materials databases (Materials Project, NIST, OpenAlloy) and published literature contain ≥100 unique solder compositions with Vickers hardness measurements and complete elemental breakdowns; if <100 but ≥50 records are available, the project proceeds with reduced N and explicitly reports power limitation
- **Assumption about measurement validity**: Vickers hardness measurements in the aggregated dataset come from validated testing protocols with citable sources; measurements from non-standardized protocols are excluded or flagged for manual review
- **Assumption about scope boundaries**: Alloys with >5 elements are excluded to reduce feature complexity; room-temperature measurements only are included (thermal cycling effects are out of scope)
- **Assumption about compute constraints**: All model training and inference runs on CPU-only infrastructure (no GPU, CUDA, bitsandbytes, or accelerator dependencies); XGBoost and linear regression are selected as CPU-tractable methods
- **Assumption about inference framing**: The composition-hardness relationship is framed as associational (not causal) given the observational nature of the aggregated dataset; randomization or identification strategies are not present
- **Assumption about threshold justification**: The R² ≥ 0.6 target follows community-standard benchmarks for materials property prediction models; sensitivity analysis sweeps a range of values to verify robustness
- **Assumption about predictor collinearity**: Compositional features (e.g., atomic mass, atomic radius, electronegativity) may exhibit definitional correlation; collinearity diagnostics (VIF) are required to frame joint relationships descriptively rather than claiming independent effects
- **Assumption about dataset-variable fit**: The aggregated datasets contain all required variables (elemental composition, Vickers hardness, elemental property tables for descriptor computation); The aggregated dataset does NOT include post-processing history variables (e.g., annealing time, cooling rate) or microstructure descriptors as primary features. The scope is strictly limited to elemental composition and room-temperature Vickers hardness. If microstructure effects are significant, this is treated as a confounding factor; the system must flag this limitation in the 'Limitations' section of the report, stating that the model captures compositional effects only and may not generalize to alloys with divergent thermal histories.
- **Assumption about statistical power**: A dataset size of N ≥ 100 is required to support a robust paired t-test on 5 cross-validation folds; if N < 100, the results are considered exploratory and a power limitation report is mandatory.

## Related Work

- [Deep Learning-Driven Microstructure Characterization and Vickers Hardness Prediction of Mg-Gd Alloys (2024)](http://arxiv.org/abs/2410.20402v1) — Establishes that deep learning can predict hardness from composition and microstructure in Mg-Gd systems, demonstrating the general feasibility of composition-to-property ML models in metallurgy.