# Feature Specification: Predicting Yield Strength of BCC Alloys

**Feature Branch**: `001-bcc-yield-strength`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of BCC Alloys Using Machine Learning and Public Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Curation and BCC Filtering (Priority: P1)

A materials scientist needs to obtain a clean, filtered dataset containing only Body-Centered Cubic (BCC) alloys with valid yield strength values and complete elemental compositions from public repositories to begin analysis.

**Why this priority**: Without a valid, filtered dataset, no feature engineering or modeling can occur. This is the foundational step; if the data contains non-BCC phases or missing yield values, the entire research question becomes unanswerable.

**Independent Test**: The system can be tested by executing the data ingestion pipeline and verifying that the output CSV contains zero entries with missing yield strength, zero entries with non-BCC crystal structures, and that all composition rows sum to 1.0 (atomic fraction).

**Acceptance Scenarios**:

1. **Given** a raw dataset containing mixed crystal structures (FCC, BCC, HCP) and missing values, **When** the filtering script runs, **Then** the output dataset contains exclusively BCC-phase alloys with non-null yield strength values.
2. **Given** a raw dataset where composition rows do not sum to 1.0 due to rounding errors, **When** the standardization step runs, **Then** all composition rows are normalized to sum exactly to 1.0, and the original atomic fractions are preserved in a log for traceability.
3. **Given** an entry with a reported yield strength of "N/A" or a non-numeric string, **When** the cleaning process runs, **Then** that entry is excluded from the final dataset and flagged in a "rejected_entries.log" file with the reason code.

---

### User Story 2 - Compositional Feature Engineering (Priority: P2)

A researcher needs to generate derived compositional descriptors (e.g., atomic radius mismatch, valence electron concentration) for each alloy in the curated dataset to serve as predictors for the machine learning model.

**Why this priority**: Raw elemental compositions are insufficient for the hypothesis. The scientific value lies in the derived descriptors. This step transforms the data into the format required for the regression analysis.

**Independent Test**: The system can be tested by selecting a known alloy composition (e.g., a standard Mo-Nb-Ta alloy) from the literature, manually calculating its descriptors, and comparing the result against the system's output for that specific row.

**Acceptance Scenarios**:

1. **Given** a valid atomic composition for a multi-principal element alloy, **When** the feature engineering module runs, **Then** it outputs a row containing the calculated atomic radius mismatch (δ), valence electron concentration (VEC), mixing entropy, and mixing enthalpy.
2. **Given** an alloy composition containing an element not found in the standard periodic table reference (e.g., a typo), **When** the feature engineering module runs, **Then** the process halts for that row and logs a "Missing Element Reference" error rather than producing NaN values.
3. **Given** a dataset of 500 alloys, **When** the feature engineering runs, **Then** the processing time is efficient and completes within the CI pipeline limits.

---

### User Story 3 - Regression Modeling and Validation (Priority: P3)

A data scientist needs to train multiple regression models (Random Forest, Gradient Boosting, Ridge) on the engineered features, evaluate their performance against a holdout test set, and generate confidence intervals for the R² metric.

**Why this priority**: This is the core research output. It directly answers the research question regarding the relationship between composition and yield strength. The inclusion of validation (cross-validation and bootstrapping) ensures the results are statistically defensible.

**Independent Test**: The system can be tested by running the training script with a fixed random seed and verifying that the reported R², MAE, and RMSE values match the expected values within a tolerance of 0.001, and that the bootstrapped confidence intervals are generated.

**Acceptance Scenarios**:

1. **Given** the engineered dataset split into [deferred] training and [deferred] testing, **When** the model training script executes, **Then** it outputs a report comparing R², MAE, and RMSE for Random Forest, Gradient Boosting, and Ridge regression models.
2. **Given** the best-performing model, **When** the permutation importance test runs, **Then** it outputs a ranked list of the top 5 features contributing to the prediction, verifying that the model is not relying on a single spurious correlation.
3. **Given** the test set predictions, **When** the validation strategy runs (using Leave-One-Out Cross-Validation for N < 100 or 100-iteration bootstrap for N ≥ 100), **Then** the system outputs a 95% confidence interval for the R² metric, formatted as [lower_bound, upper_bound].

---

### Edge Cases

- **What happens when** the public dataset contains fewer than 80 BCC alloys after filtering? The system MUST flag a "Data Scarcity Warning" and halt the training step, as statistical power will be insufficient for reliable regression and valid 80/20 splitting.
- **How does the system handle** alloys with multiple reported yield strength values for the same composition? The system MUST average the values and record the standard deviation, or select the median, and log the selection method.
- **What happens when** a calculated descriptor (e.g., mixing entropy) results in a mathematical domain error (e.g., log of zero)? The system MUST catch the exception, assign a value of 0.0 (if physically justified) or NaN, and log the specific alloy ID for manual review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the MPEA database and Materials Project data, filtering for BCC-phase alloys with reported yield strength (See US-1).
- **FR-002**: System MUST normalize elemental compositions to atomic fractions summing to 1.0 and exclude entries with missing yield strength data (See US-1).
- **FR-003**: System MUST calculate atomic radius mismatch (δ), valence electron concentration (VEC), electronegativity difference, mixing entropy, and mixing enthalpy for every valid alloy (See US-2).
- **FR-003.1**: System MUST apply Isometric Log-Ratio (ILR) or similar log-ratio transformations to the compositional features prior to modeling to address compositional closure and multicollinearity (See US-2).
- **FR-004**: System MUST perform a stratified 80/20 train-test split based on binned compositional ranges (to prevent data leakage) IF the dataset size is ≥ 80; ELSE the system MUST halt with a Data Scarcity Warning (See US-3).
- **FR-005**: System MUST train Random Forest, Gradient Boosting, and Ridge Regression models using the selected validation strategy (LOOCV for N < 100, 5-fold CV for N ≥ 100) and report R², MAE, and RMSE on the holdout set (See US-3).
- **FR-006**: System MUST perform permutation importance testing and generate 95% confidence intervals for the R² metric using the appropriate resampling strategy (See US-3).

### Key Entities

- **AlloyRecord**: Represents a single alloy entry; attributes include `elemental_composition` (dict), `yield_strength` (float, MPa), `crystal_structure` (string), `system_id` (string).
- **CompositionalDescriptor**: Represents derived features; attributes include `delta_radius` (float), `vec` (float), `mixing_entropy` (float), `mixing_enthalpy` (float), `ilr_transformed_features` (list).
- **ModelPerformance**: Represents evaluation results; attributes include `model_type` (string), `r_squared` (float), `mae` (float), `rmse` (float), `confidence_interval` (tuple).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The coefficient of determination (R²) for the best-performing model is measured against the null hypothesis baseline (predicting the mean yield strength of the training set) to determine if composition explains significant variance (See US-3).
- **SC-002**: The mean absolute error (MAE) of the model predictions is measured against the experimental uncertainty range of the source dataset (≤ 50 MPa) to assess practical utility (See US-3).
- **SC-003**: The stability of feature importance rankings is measured against 100 bootstrap resamples (or LOOCV iterations) to ensure that the identified descriptors are robust and not artifacts of specific data splits (See US-3).
- **SC-004**: The computational runtime of the full pipeline (data download to final report) is measured against the 6-hour GitHub Actions free-tier limit to ensure feasibility (See US-3).

## Assumptions

- The public MPEA database (https://doi.org/10.1038/s41597-020-00768-9) contains sufficient entries (≥ 80) of BCC-phase alloys with reported yield strength values to support a statistical regression analysis.
- Elemental properties (atomic radius, electronegativity, valence) can be reliably retrieved from a standard periodic table reference (e.g., NIST or a local static dictionary) without requiring external API calls that might fail or rate-limit during CI.
- The relationship between composition and yield strength in BCC alloys can be approximated by the selected compositional descriptors (δ, VEC, etc.) after appropriate log-ratio transformation, without needing explicit microstructural data (grain size, dislocation density) for this initial screening model.
- The GitHub Actions free-tier runner (multi-core CPU, ~7 GB RAM) is sufficient to process the filtered dataset and train the specified scikit-learn models within the 6-hour job limit, provided the dataset is not expanded beyond the initial public source.
- The yield strength values reported in the source datasets are measured under comparable conditions (room temperature, standard strain rates) such that they can be pooled without complex normalization for testing conditions.