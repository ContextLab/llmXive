# Feature Specification: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Feature Branch**: `001-predict-heusler-hysteresis`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Aggregation and Preprocessing (Priority: P1)

A materials researcher needs to aggregate scattered experimental measurements of Heusler alloy compositions and magnetic hysteresis parameters from multiple sources (NIST, published supplements, and manual literature curation) into a single, standardized dataset to enable quantitative analysis.

**Why this priority**: Without a unified, clean dataset of *experimental* data, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: Can be fully tested by successfully ingesting data from at least 3 distinct sources (including at least one published journal supplement and manual curation from raw literature), standardizing composition to atomic fractions, normalizing hysteresis parameters to consistent units, and producing a validated CSV with all available valid data points (non-null composition and hysteresis values).

**Acceptance Scenarios**:

1. **Given** raw data files from NIST repository, published journal supplements, and manually curated data from raw literature, **When** the ingestion script is executed, **Then** the output CSV contains all unique alloy entries with standardized composition (atomic fractions summing to 1.0) and normalized hysteresis parameters (coercivity in Oe, saturation magnetization in emu/g), preserving zero values as valid numerical entries. Composition data may be supplemented from Materials Project, but hysteresis targets must be experimental.
2. **Given** entries with missing values for non-critical fields, **When** the preprocessing pipeline runs, **Then** listwise deletion is applied if the missing rate exceeds 15% for a column; otherwise, mean imputation is applied, with a documented imputation rate <15%. Entries where the hysteresis target is derived from DFT calculations (e.g., from Materials Project) are excluded from the target variable list.
3. **Given** composition strings in various formats (e.g., "Co2MnGa", "Co:2 Mn:1 Ga:1"), **When** the parser processes them, **Then** all are converted to precise atomic fractions with ≥4 decimal places of precision.

---

### User Story 2 - Feature Engineering and Model Training (Priority: P2)

A computational materials scientist needs to transform elemental compositions into meaningful descriptors (electronegativity averages, valence electron concentration, atomic radii variance) and train regression models to quantify the composition-hysteresis relationship.

**Why this priority**: This step translates raw chemical data into predictive features and establishes the baseline quantitative model, directly addressing the research question.

**Independent Test**: Can be fully tested by successfully computing ≥5 composition-based descriptors for all dataset entries, training both linear regression and random forest models with 5-fold cross-validation on the fixed [deferred] training split, and producing performance metrics (R², MAE) for each.

**Acceptance Scenarios**:

1. **Given** a standardized composition dataset, **When** the feature engineering module runs, **Then** at least 5 descriptors are computed for each entry: average electronegativity, valence electron concentration (VEC), atomic radii variance, average number of valence d-electrons, and atomic size mismatch.
2. **Given** the engineered feature set, **When** the model training pipeline executes with 5-fold cross-validation on the fixed [deferred] training split, **Then** both a baseline linear regression and a random forest regressor are trained with hyperparameter tuning via cross-validation, producing cross-validation R² and MAE for each model.
3. **Given** trained models, **When** feature importance is assessed via permutation importance, **Then** the top 3 most influential composition descriptors are identified and ranked for each target hysteresis parameter.

---

### User Story 3 - Statistical Validation and Interpretation (Priority: P3)

A research team needs to validate model performance against a null hypothesis, assess statistical significance, and interpret the composition-property relationships through partial dependence plots to guide future synthesis efforts.

**Why this priority**: This step provides the scientific rigor needed to claim meaningful relationships and offers actionable insights for materials design, completing the research loop.

**Independent Test**: Can be fully tested by successfully performing F-test comparison against a null model, computing 95% confidence intervals via bootstrapping, generating partial dependence plots for top features, and holding out [deferred] of data for final evaluation.

**Acceptance Scenarios**:

1. **Given** trained models and a held-out [deferred] test set, **When** the validation suite executes, **Then** model performance (MAE, RMSE, R²) is reported against the null model (mean prediction) and the F-test p-value is reported, with explicit reference to the hypothesis threshold (R² ≥ 0.6) for scientific interpretation.
2. **Given** cross-validation results, **When** bootstrapping with 1000 resamples is performed, **Then** 95% confidence intervals are computed and reported for R² values, demonstrating model stability.
3. **Given** the trained random forest model, **When** partial dependence plots are generated for the top 3 features, **Then** visualizations show the marginal effect of each composition descriptor on hysteresis parameters, revealing interpretable trends (e.g., linear, threshold, or monotonic relationships).
4. **Given** the validation results, **When** the report is generated, **Then** a specific section titled "Statistical Limitations" is included stating that the F-test validates fit not mechanism and notes microstructural confounders.

### Edge Cases

- What happens when the dataset contains fewer than 50 data points after preprocessing? The system MUST log a warning and proceed with available data, but the final report MUST explicitly state the reduced statistical power and potential for overfitting.
- How does the system handle elements not found in standard periodic table databases? The system MUST flag these entries and exclude them from analysis, logging the specific missing elements for manual review.
- What if a hysteresis parameter value is reported as "not measurable" or "zero" in the source? The system MUST treat "not measurable" as missing data (excluded) and "zero" as a valid numerical value, with documentation of this distinction in the data dictionary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST aggregate experimental data from at least 3 distinct sources (NIST repository, at least one published journal supplement, and manually curated data from raw literature identified in the gap analysis) into a unified dataset containing all available valid entries (See US-1).
- **FR-002**: System MUST standardize all composition data to atomic fractions summing to 1.0 with ≥4 decimal places of precision and normalize hysteresis parameters to consistent units (coercivity in Oe, saturation magnetization in emu/g), preserving zero values as valid numerical entries (See US-1).
- **FR-003**: System MUST compute at least 5 composition-based descriptors including average electronegativity, valence electron concentration (VEC), atomic radii variance, average number of valence d-electrons, and atomic size mismatch (See US-2).
- **FR-004**: System MUST train both a baseline linear regression and a random forest regressor with 5-fold cross-validation and hyperparameter tuning via cross-validation on the fixed [deferred] training split (See US-2).
- **FR-005**: System MUST perform statistical validation including F-test comparison against a null model, 95% confidence interval computation via 1000-resample bootstrapping, and generation of partial dependence plots for top 3 features (See US-3).
- **FR-008**: System MUST explicitly flag DFT (calculated) data entries and exclude them from the target variable training set (hysteresis prediction); use Materials Project only for composition metadata if experimental hysteresis is missing, but do not use its calculated magnetic properties as targets; if experimental data is insufficient, the system MUST report a 'data scarcity warning' (See US-1).
- **FR-009**: System MUST explicitly state in the final report that the F-test validates the statistical fit of the model, not the physical mechanism, and interpret results with caution regarding microstructural confounders (See US-3).
- **FR-010**: System MUST log the 'synthesis method' if available as a metadata field and include a note in the report that hysteresis is heavily influenced by microstructure, not just composition (See US-3).

### Key Entities

- **AlloyEntry**: Represents a single Heusler alloy measurement with attributes for composition (atomic fractions of constituent elements), hysteresis parameters (coercivity, remanence, saturation magnetization), and source metadata.
- **CompositionDescriptor**: Represents engineered features derived from elemental composition, including electronegativity averages, VEC, atomic radii variance, average number of valence d-electrons, and size mismatch metrics.
- **ModelResult**: Encapsulates trained model outputs including performance metrics (R², MAE, RMSE), feature importance rankings, and confidence intervals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive performance (R², MAE) is measured against the null model (mean prediction) using an F-test with reported p-value to establish statistical significance (See US-3).
- **SC-002**: Cross-validation stability is measured via 95% confidence intervals computed from 1000 bootstrap resamples, with the system reporting the interval bounds for the R² metric (See US-3).
- **SC-003**: Feature interpretability is measured by the system generating partial dependence plots for the top 3 composition descriptors, with a note that expert review is required for physical plausibility (See US-3).
- **SC-004**: Dataset completeness is measured by the proportion of data points with non-null composition and non-null hysteresis parameters successfully ingested from each source (See US-1).
- **SC-005**: Computational feasibility is measured by successful execution of the entire pipeline on GitHub Actions free-tier (2 CPU cores, ~7 GB RAM, ≤6 hours) without GPU acceleration (See US-2).
- **SC-006**: Model statistical significance is measured by an F-test p-value < 0.05 AND an R² ≥ 0.6 on the held-out test set (See US-3).

## Assumptions

- The project will aggregate data from APIs and, where necessary, manually curate data from raw literature to reach a target of ≥50 data points, acknowledging that no pre-existing unified dataset exists and that the 50-point target is a goal, not a guarantee of API availability.
- All required elemental properties (electronegativity, atomic radii, valence electrons) are available in standard periodic table databases for the elements commonly found in Heusler alloys (Mn, Co, Fe, Ga, Al, etc.).
- The relationship between composition and hysteresis parameters can be reasonably approximated by classical regression models without requiring deep learning or GPU-accelerated computation.
- Published experimental measurements use consistent units for hysteresis parameters that can be standardized to Oe and emu/g without ambiguity or loss of precision.
- The GitHub Actions free-tier environment provides sufficient disk space (~14 GB) to store the aggregated dataset, intermediate feature sets, and model artifacts without exceeding limits.
- If fewer than 50 experimental data points are available, the statistical power of the study will be reduced, and results should be interpreted with caution.