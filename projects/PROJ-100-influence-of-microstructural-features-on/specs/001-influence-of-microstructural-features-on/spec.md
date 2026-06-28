# Feature Specification: Influence of Microstructural Features on Fatigue Life in Aluminum Alloys

**Feature Branch**: `001-fatigue-microstructure-analysis`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "How do specific microstructural features (grain size, secondary phase distribution, and dislocation density) quantitatively influence fatigue life in aluminum alloys, and can these features be used to predict fatigue performance using machine learning models trained on public datasets?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a materials researcher, I need to download and preprocess publicly available aluminum alloy fatigue datasets with documented microstructural and fatigue test parameters, so that I have clean, structured data ready for feature extraction and model training.

**Why this priority**: This is the foundational step; without clean data, no subsequent analysis can proceed. It delivers immediate value by establishing the research dataset.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads ≥100 specimen records from specified repositories, removes incomplete records, and produces a validated CSV with all required columns.

**Acceptance Scenarios**:

1. **Given** a HuggingFace Datasets or NIST Materials Data Repository URL for aluminum fatigue data, **When** the pipeline executes, **Then** at least 100 specimen records with documented microstructural and fatigue test parameters are downloaded and validated.
2. **Given** records with missing fatigue cycle counts or unverified microstructure documentation, **When** the data cleaning step runs, **Then** those records are excluded and logged in an exclusion report.
3. **Given** the cleaned dataset, **When** the validation check runs, **Then** all 3 required microstructural features (grain size, secondary phase distribution, dislocation density) and the outcome variable (fatigue life cycles) are present for ≥90% of remaining records.

---

### User Story 2 - Microstructural Feature Extraction and Model Training (Priority: P2)

As a materials researcher, I need to extract quantitative microstructural features from microscopy images and train regression models to predict fatigue life, so that I can quantify the relationship between microstructure and fatigue performance.

**Why this priority**: This is the core research activity; it directly addresses the research question but depends on P1 data being ready.

**Independent Test**: Can be fully tested by running the feature extraction on sample microscopy images and verifying that the trained model produces predictions with R² > 0.7 on held-out test data.

**Acceptance Scenarios**:

1. **Given** 512×512 microscopy image crops, **When** the feature extraction pipeline runs, **Then** grain size (equivalent diameter distribution), secondary phase fraction (area percentage), and dislocation density proxies (texture analysis metrics) are quantified and saved.
2. **Given** the extracted feature matrix with fatigue life outcomes, **When** model training completes with 5-fold cross-validation, **Then** at least 3 regression models (Random Forest, Gradient Boosting, ElasticNet) are fitted with ≤100 trees/estimators each.
3. **Given** a trained model, **When** it evaluates on held-out test data, **Then** the R² score exceeds 0.7 and mean absolute error is within 20% of experimental values.

---

### User Story 3 - Statistical Analysis and Results Visualization (Priority: P3)

As a materials researcher, I need to perform statistical significance testing and generate visualizations of model results, so that I can interpret which microstructural features significantly influence fatigue life and communicate findings.

**Why this priority**: This adds interpretability and scientific rigor to the analysis; it depends on P2 models being trained.

**Independent Test**: Can be fully tested by running the statistical analysis module and verifying that ANOVA results, confidence intervals, and visualizations are generated for all trained models.

**Acceptance Scenarios**:

1. **Given** a trained regression model, **When** ANOVA testing runs with α = 0.05, **Then** p-values for each microstructural feature are computed and features with p < 0.05 are flagged as statistically significant.
2. **Given** model predictions, **When** bootstrapping with 1000 resamples completes, **Then** 95% confidence intervals are computed for R², RMSE, and mean absolute error metrics.
3. **Given** the final selected model, **When** visualization generation runs, **Then** partial dependence plots and feature importance charts are saved as PNG files ≤500 KB each.

---

### Edge Cases

- What happens when the HuggingFace or NIST repository is temporarily unavailable? → System retries download 3 times with exponential backoff (1s, 2s, 4s), then logs failure and halts.
- How does system handle images with no detectable grain boundaries after thresholding? → System flags the image in a quality report and excludes it from feature extraction, logging the exclusion reason.
- What happens when model R² fails to exceed 0.7 threshold on validation set? → System logs all model performances, selects the best available model, and records the shortfall in the results report for methodological review.
- How does system handle datasets where dislocation density is not directly measurable? → System uses texture analysis metrics as proxies and records this assumption in the methodology documentation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download aluminum alloy fatigue datasets from HuggingFace Datasets and NIST Materials Data Repository with target N ≥ 100 specimens containing documented microstructural and fatigue test parameters (See US-1)
- **FR-002**: System MUST remove records with missing fatigue cycle counts or unverified microstructure documentation and log all exclusions in an exclusion report (See US-1)
- **FR-003**: System MUST validate that all 3 required microstructural features (grain size, secondary phase distribution, dislocation density) and fatigue life cycles outcome are present for ≥90% of remaining records (See US-1)
- **FR-004**: System MUST load 512×512 microscopy image crops, convert to grayscale, and apply thresholding for grain boundary detection using CPU-based OpenCV processing (See US-2)
- **FR-005**: System MUST quantify grain size (equivalent diameter distribution), secondary phase fraction (area percentage via segmentation), and dislocation density proxies (texture analysis metrics) using scikit-image (See US-2)
- **FR-006**: System MUST fit Random Forest, Gradient Boosting, and ElasticNet regression models with 5-fold cross-validation, limiting each model to ≤100 trees/estimators to stay within 7 GB RAM (See US-2)
- **FR-007**: System MUST evaluate trained models on held-out test data and compute R², RMSE, and mean absolute error metrics (See US-2)
- **FR-008**: System MUST perform ANOVA testing with α = 0.05 to assess statistical significance of individual microstructural features on fatigue life (See US-3)
- **FR-009**: System MUST compute 95% confidence intervals via bootstrapping with 1000 resamples for all performance metrics (See US-3)
- **FR-010**: System MUST generate partial dependence plots and feature importance charts as PNG files ≤500 KB each (See US-3)
- **FR-011**: System MUST frame all findings as associational rather than causal, given the observational nature of the dataset (See US-3)
- **FR-012**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) when testing >1 hypothesis to control family-wise error rate (See US-3)

### Key Entities

- **Specimen Record**: Represents a single aluminum alloy test sample with attributes: specimen_id, alloy_composition, grain_size_μm, secondary_phase_fraction, dislocation_density_proxy, fatigue_life_cycles, microscopy_image_path
- **Microstructural Feature**: Represents a quantified microstructural metric with attributes: feature_name, feature_value, feature_unit, measurement_method, validation_status
- **Model Performance**: Represents model evaluation metrics with attributes: model_type, r_squared, rmse, mean_absolute_error, confidence_interval_95, validation_fold

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the target of N ≥ 100 specimens with all required microstructural features and fatigue life outcome (See US-1)
- **SC-002**: Model predictive accuracy is measured against the threshold of R² > 0.7 on held-out test data (See US-2)
- **SC-003**: Prediction error is measured against the threshold of ≤20% mean absolute error relative to experimental fatigue life values (See US-2)
- **SC-004**: Statistical significance of microstructural features is measured against the α = 0.05 threshold with multiple-comparison correction applied (See US-3)
- **SC-005**: Confidence interval coverage is measured against the [deferred] target computed via 1000-resample bootstrapping (See US-3)
- **SC-006**: Computational feasibility is measured against the constraint of ≤6 hours total runtime on 2 CPU cores with ≤7 GB RAM usage (See US-2)

## Assumptions

- Public datasets from HuggingFace Datasets and NIST Materials Data Repository contain all required variables (grain size, secondary phase distribution, dislocation density, fatigue life cycles); if any variable is missing, a [NEEDS CLARIFICATION] marker will be recorded
- The aluminum alloy fatigue datasets are observational (no random assignment), so all statistical findings must be framed as associational rather than causal
- Microscopy images are available at sufficient resolution (≥512×512) for grain boundary detection and texture analysis using OpenCV and scikit-image
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, no GPU) can execute the complete analysis pipeline within the 6-hour job limit
- Validated instruments or established literature precedents exist for the texture analysis metrics used as dislocation density proxies
- Predictor collinearity between grain size and secondary phase fraction may exist; joint relationships will be described rather than claiming independent predictive effects, with collinearity diagnostics (VIF) computed
- The 20% prediction error threshold and R² > 0.7 target are community-standard defaults for materials science ML prediction studies; sensitivity analysis will sweep thresholds over {15%, 20%, 25%} and {0.6, 0.7, 0.8} to assess robustness
- The 100 tree/estimator limit per model is sufficient to achieve target performance while maintaining CPU tractability; if performance is inadequate, model complexity will be increased incrementally with documented justification
- The 1000-resample bootstrapping count provides stable confidence interval estimates; a sensitivity check will verify stability across {500, 1000, 2000} resamples
- All cited URLs in Related work are accessible and will not require authentication beyond standard academic repository access
