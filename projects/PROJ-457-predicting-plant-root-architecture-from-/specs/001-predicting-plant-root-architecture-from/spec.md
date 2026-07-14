# Feature Specification: Predicting Plant Root Architecture from Soil Nutrient Availability

**Feature Branch**: `001-predict-root-architecture`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Plant Root Architecture from Soil Nutrient Availability Using Public Datasets"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST successfully ingest root phenotype data from RootReader/PlantPheno and soil nutrient data from ISRIC-World Soil Information, filter for valid observations (n≥20 per species), and produce a cleaned, merged dataset ready for analysis.

**Why this priority**: Without a clean, merged dataset containing both root metrics and corresponding soil nutrient levels, no statistical modeling can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a sample subset and verifying the output CSV contains the required columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen) with no null values in the predictor columns and at least 20 rows per species.

**Acceptance Scenarios**:

1. **Given** raw dataset files from RootReader and ISRIC, **When** the ingestion script runs with the filtering parameters (n≥20 per species, explicit P/N measurements), **Then** the output dataset contains exactly the filtered rows with imputed missing values (k=5, Euclidean distance, fallback to mean) and log-transformed root metrics.
2. **Given** a dataset with species having fewer than 20 observations, **When** the filtering step executes, **Then** those species are excluded from the final merged dataset, and a log entry records the exclusion count.

---

### User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

The system MUST fit Linear Mixed-Effects Models (LMM) and baseline random forest models to quantify the relationship between soil phosphorus/nitrogen and root architectural traits, reporting model performance metrics and statistical significance.

**Why this priority**: This implements the core research question (how nutrients predict architecture). It delivers the primary scientific findings (R², p-values) required to validate the hypothesis.

**Independent Test**: The modeling step can be tested by running the training script on the preprocessed dataset and verifying the output JSON contains R², RMSE, and p-values for the LMM coefficients, ensuring the random forest baseline is also evaluated.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset split into train/validation/test sets by species (not by row) to prevent data leakage, **When** the Linear Mixed-Effects Model (LMM) is fitted, **Then** the output includes adjusted R², RMSE, and p-values for phosphorus and nitrogen coefficients, with species included as a random intercept.
2. **Given** the same dataset, **When** the random forest regressor (max_depth=5) is trained, **Then** the output includes R² and RMSE values comparable to the LMM, allowing non-linear relationship assessment.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The system MUST generate partial dependence plots visualizing the nutrient-architecture relationships and compile a final report with all statistical findings, ensuring output files are within size constraints.

**Why this priority**: Visualization is essential for interpreting the statistical results and communicating findings to biologists. The report consolidates all evidence for the research conclusion.

**Independent Test**: The reporting step can be tested by running the visualization script and verifying that PNG files are generated for partial dependence plots and that the total output size is ≤100MB.

**Acceptance Scenarios**:

1. **Given** the fitted LMM and test data, **When** the partial dependence plot generation runs, **Then** PNG files are created showing the relationship between phosphorus/nitrogen levels and root branching density/total length, using the 5th to 95th percentile range of observed values.
2. **Given** all model outputs and plots, **When** the final report is compiled, **Then** the report includes R² values, p-values, and visualizations, with the total file size not exceeding 100MB.

---

### Edge Cases

- What happens when a species has data for only one nutrient (e.g., phosphorus but no nitrogen)? The system MUST exclude that species from the multivariate analysis and log the exclusion.
- How does the system handle extreme outliers in root metrics? The system MUST apply log-transformation and verify that no values remain NaN or infinite after transformation.
- What happens if the ISRIC data for a specific geographic coordinate is missing? The system MUST use nearest neighbor interpolation within a 10km radius or exclude the observation, logging the method used.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse root phenotype data from RootReader and PlantPheno, filtering for datasets with explicit phosphorus and nitrogen measurements and at least 20 observations per species (See US-1).
- **FR-002**: System MUST merge root phenotype data with soil nutrient data from ISRIC-World Soil Information using geographic and experimental metadata, ensuring no data leakage across species via nearest neighbor interpolation within a 10km radius and adherence to Constitution Principle VI (Cross-Species Stratified Validation) (See US-1).
- **FR-003**: System MUST preprocess data by applying z-score normalization (global, across all species) to nutrient values, log-transforming root metrics, and imputing missing values using k-nearest neighbors (k=5, Euclidean distance, using numeric predictors only) with a fallback to mean imputation if fewer than 5 neighbors exist (See US-1).
- **FR-004**: System MUST fit Linear Mixed-Effects Models (LMM) with root metrics as outcomes and phosphorus/nitrogen as predictors, including species as a random intercept, using the statsmodels library with REML estimation and Satterthwaite approximation for p-values, and report adjusted R², RMSE, and p-values (See US-2).
- **FR-005**: System MUST fit a baseline random forest regression model (max_depth=5) to compare non-linear vs. linear relationship strength and report R² and RMSE (See US-2).
- **FR-006**: System MUST perform 5-fold cross-validation with folds split strictly by species (not by row) to assess generalization performance and prevent data leakage, reporting mean out-of-sample R² for both LMM and random forest models (See US-2).
- **FR-007**: System MUST generate partial dependence plots visualizing nutrient-architecture relationships using the 5th to 95th percentile range of observed nutrient values in the training set and save figures as PNG files with total size ≤100MB (See US-3).
- **FR-008**: System MUST conduct an F-test for overall model significance and report p-values for individual nutrient coefficients (See US-2).
- **FR-009**: System MUST frame all findings as associational relationships, avoiding causal claims unless randomization is specified in the input data (See US-2).
- **FR-010**: System MUST implement multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) when testing multiple hypotheses across species or traits (See US-2).
- **FR-011**: System MUST conduct a sensitivity analysis of nutrient coefficients against literature-reported physiological ranges (e.g., ±10% variation) to validate biological plausibility (See US-2).
- **FR-012**: System MUST exclude experimental root data where nutrients were manipulated (controlled conditions) and use only observational root data for the primary analysis to prevent category error (See US-1).

### Key Entities

- **RootPhenotypeRecord**: Represents a single observation of root architecture, including attributes: species, root_length, branching_density, surface_area, geographic_location, experimental_id, data_source_type (observational/experimental).
- **SoilNutrientRecord**: Represents soil chemical properties, including attributes: phosphorus_concentration, nitrogen_concentration, geographic_location, measurement_date, depth.
- **MergedDataset**: The combined dataset linking root and soil data, including attributes: species, root_metrics, nutrient_levels, sample_size_per_species, data_source_type.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of root phenotype datasets successfully merged with soil nutrient data is measured against the total number of available datasets in RootReader/PlantPheno (See US-1).
- **SC-002**: The adjusted R² of the Linear Mixed-Effects Model (full fit) is measured against the mean out-of-sample R² of the baseline random forest model; success is defined as the LMM R² being within 5 percentage points of the RF R² (See US-2).
- **SC-003**: The p-values for phosphorus and nitrogen coefficients are measured against the significance threshold (p < 0.05) to determine statistical association (See US-2).
- **SC-004**: The total size of generated visualization files is measured against the 100MB constraint to ensure compute feasibility (See US-3).
- **SC-005**: The number of species excluded due to insufficient sample size (n < 20) is measured against the total number of species in the input data to assess data coverage (See US-1).
- **SC-006**: The biological plausibility of nutrient coefficients is measured against literature-reported physiological ranges (See US-2, FR-011).

## Assumptions

- The RootReader and PlantPheno datasets contain explicit phosphorus and nitrogen concentration measurements for the required geographic locations; if not, the system will exclude those observations.
- The ISRIC-World Soil Information data provides sufficient spatial resolution to match with root phenotype experimental sites; interpolation will be used if exact matches are unavailable.
- The computational environment (GitHub Actions free-tier) provides sufficient CPU resources (2 cores, ~7 GB RAM) to process the dataset and fit the models within 6 hours.
- The root phenotype datasets are available in a format compatible with direct parsing (CSV/JSON); if not, a conversion step will be added to the preprocessing pipeline.
- The log-transformation of root metrics is appropriate for reducing skew in the data distribution; if the data contains zero or negative values, a small constant will be added before transformation.
- The species variable in the dataset is categorical and suitable for inclusion as a random effect in mixed-effects modeling; if the dataset lacks species labels, the analysis will be limited to a single-species model.
- The observational root data in the source datasets is distinct from controlled experimental data, and the `data_source_type` field is available to distinguish them.