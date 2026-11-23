# Feature Specification: Predicting Yield Strength of BCC Alloys

**Feature Branch**: `001-bcc-yield-strength`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of BCC Alloys Using Machine Learning and Public Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Curation and BCC Filtering (Priority: P1)

A materials scientist needs to obtain a clean, filtered dataset containing only Body-Centered Cubic (BCC) alloys with valid yield strength values and complete elemental compositions from the MPEA database to begin analysis.

**Why this priority**: Without a valid, filtered dataset, no feature engineering or modeling can occur. This is the foundational step; if the data contains non‑BCC phases or missing yield values, the entire research question becomes unanswerable.

**Independent Test**: The system can be tested by executing the data ingestion pipeline and verifying that the output CSV contains zero entries with missing yield strength, zero entries with non‑BCC crystal structures, and that all composition rows sum to a normalized total. (atomic fraction).

**Acceptance Scenarios**:

1. **Given** a raw dataset containing mixed crystal structures (FCC, BCC, HCP) and missing values, **When** the filtering script runs, **Then** the output dataset contains exclusively BCC-phase alloys with non‑null yield strength values.
2. **Given** a raw dataset where composition rows do not sum to 1.0 due to rounding errors, **When** the standardization step runs, **Then** All composition rows are normalized so that each row sums to a consistent total., and the original atomic fractions are preserved in a log for traceability.
3. **Given** an entry with a reported yield strength of "N/A" or a non‑numeric string, **When** the cleaning process runs, **Then** that entry is excluded from the final dataset and flagged in a `rejected_entries.log` file with the appropriate reason code.

---

### User Story 2 - Compositional Feature Engineering (Priority: P2)

A researcher needs to generate derived compositional descriptors (e.g., atomic radius mismatch, valence electron concentration) **and** Isometric Log‑Ratio (ILR) transformed features for each alloy in the curated dataset to serve as predictors for the machine learning model.

**Why this priority**: Raw elemental compositions are insufficient for the hypothesis. The scientific value lies in the derived descriptors **and** the mathematically robust ILR transformation to address compositional closure. This step transforms the data into the format required for the regression analysis.

**Independent Test**: The system can be tested by running the feature engineering module on a fixed reference alloy (Mo‑25Nb‑25Ta‑25W in atomic percent) and verifying that the calculated descriptors (δ, VEC, mixing entropy, mixing enthalpy, electronegativity difference) match the manually calculated reference values within a relative tolerance of ≤ 1e‑6.

**Acceptance Scenarios**:

1. **Given** a valid atomic composition for a multi‑principal element alloy, **When** the feature engineering module runs, **Then** it outputs a row containing the calculated atomic radius mismatch (δ), valence electron concentration (VEC), mixing entropy, mixing enthalpy, and electronegativity difference.
2. **Given** an alloy composition containing an element not found in the standard periodic table reference (e.g., a typo), **When** the feature engineering module runs, **Then** the process halts for that row and logs a `"Missing Element Reference"` error rather than producing NaN values.
3. **Given** a dataset of 500 alloys, **When** the feature engineering runs, **Then** the processing time is efficient and completes within **300 seconds** (the CI pipeline limit).

---

### User Story 3 - Regression Modeling and Validation (Priority: P3)

A data scientist needs to train multiple regression models (Random Forest, Gradient Boosting, Ridge) on the engineered features, evaluate their performance using **Repeated 5‑Fold Cross‑Validation (10 repeats)**, and generate confidence intervals for the R² metric.

**Why this priority**: This is the core research output. It directly answers the research question regarding the relationship between composition and yield strength. The inclusion of validation (Repeated 5‑Fold CV) ensures the results are statistically defensible and robust for small datasets.

**Independent Test**: The system can be tested by running the training script with a fixed random seed and verifying that the reported R², MAE, and RMSE values match the expected values within a relative tolerance of **≤ 1e‑5**, and that the bootstrapped confidence intervals are generated using the specified method.

**Acceptance Scenarios**:

1. **Given** the engineered dataset split into training and testing sets, **When** the model training script executes, **Then** it outputs a report comparing R², MAE, and RMSE for Random Forest, Gradient Boosting, and Ridge regression models, explicitly identifying the best‑performing model by the highest R² score.
2. **Given** the best‑performing model, **When** the permutation importance test runs, **Then** it outputs a ranked list of the top 5 features contributing to the prediction, verifying that the model is not relying on a single spurious correlation. **Note:** Feature importance is reported for predictive insight only and is **not** interpreted as evidence of causal effect.
3. **Given** the test set predictions, **When** the validation strategy runs (using Repeated 5‑Fold CV), **Then** the system outputs a 95 % confidence interval for the R² metric, formatted as `[lower_bound, upper_bound]`, calculated via bootstrapping over **1000 resamples of the holdout‑set predictions**.

---

### User Story 4 - Data Quality and Scarcity Handling (Priority: P4)

- **What happens when** the public dataset contains fewer than 80 BCC alloys after filtering? The system **MUST** halt immediately, exit with code 1, and write the exact log message `"DATA_SCARCITY: Insufficient BCC alloys (N < 80)"` to stderr.
- **How does the system handle** alloys with multiple reported yield strength values for the same composition? The system **MUST** **average** the values, record the standard deviation, and log the aggregation method (`"average"`). This deterministic rule ensures reproducibility.
- **What happens when** a calculated descriptor (e.g., mixing entropy) results in a mathematical domain error (e.g., log of zero)? The system **MUST** catch the exception, assign a value of **0.0** (physically justified) and log the specific alloy ID for manual review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the MPEA database (DOI: 10.1038/s41597-020-00768-9), filtering for BCC-phase alloys with reported yield strength (See US-1).
- **FR-002**: System MUST normalize elemental compositions to atomic fractions summing to 1.0, exclude entries with missing yield strength data, **and log all rejected entries with reason codes to `rejected_entries.log`** (See US-1).
- **FR-003**: System MUST calculate atomic radius mismatch (δ), valence electron concentration (VEC), electronegativity difference, mixing entropy, and mixing enthalpy for every valid alloy. The binary interaction parameters (Ω_ij) for mixing enthalpy MUST be sourced from **NIST‑JANAF Thermochemical Tables (2022 edition)**, distinct from the experimental yield strength source to ensure predictor independence (See US-2).
- **FR-003.1**: System MUST apply Isometric Log‑Ratio (ILR) or similar log‑ratio transformations to the compositional features prior to modeling to address compositional closure and multicollinearity. These ILR features are used in **COMPLEMENT** with the scalar descriptors (δ, VEC, etc.) to capture both geometric constraints and specific physical mechanisms (See US-2).
- **FR-004**: System MUST perform a stratified 80/20 train‑test split based on 4 quantile‑based bins of the target variable (yield strength) **IF** the dataset size is ≥ 80; **ELSE** the system MUST halt with exit code 1 and the message `"DATA_SCARCITY: Insufficient BCC alloys (N < 80)"`. The split must also ensure that any duplicate compositions (after aggregation per US‑4) are assigned to the same partition to avoid data leakage (See US-4).
- **FR-005**: System MUST train Random Forest, Gradient Boosting, and Ridge Regression models using **Repeated 5‑Fold Cross‑Validation (10 repeats)** for all datasets with N ≥ 80, reporting the **mean** R², MAE, and RMSE across the CV repeats on the holdout set (See US-3).
- **FR-006**: System MUST perform permutation importance testing **and** generate confidence intervals for the R² metric using the **percentile method on 1000 bootstrap resamples of the holdout‑set predictions** (See US-3).
- **FR-007**: System MUST **average** duplicate yield‑strength measurements for identical compositions, compute the standard deviation, and log the aggregation method (`"average"`) in `aggregation.log` (See US-4).
- **FR-008**: System MUST catch descriptor domain‑error exceptions, assign a fallback value of **0.0**, and log the affected alloy IDs in `descriptor_errors.log` (See US-4).

### Key Entities

- **AlloyRecord**: Represents a single alloy entry; attributes include `elemental_composition` (dict), `yield_strength` (float, MPa), `crystal_structure` (string), `system_id` (string).
- **CompositionalDescriptor**: Represents derived features; attributes include `delta_radius` (float), `vec` (float), `mixing_entropy` (float), `mixing_enthalpy` (float), `electronegativity_diff` (float), `ilr_transformed_features` (list).
- **ModelPerformance**: Represents evaluation results; attributes include `model_type` (string), `r_squared` (float), `mae` (float), `rmse` (float), `confidence_interval` (tuple).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The coefficient of determination (R²) for the best‑performing model must **exceed** the baseline (mean‑predictor) R² **and** its 95 % bootstrap confidence interval must **not include** the baseline value, demonstrating statistically significant predictive improvement (See US-3).  
- **SC-002**: The mean absolute error (MAE) of the model predictions is **reported** and compared to the experimental uncertainty (~45 MPa) as a reference; no hard pass/fail threshold is imposed (See US-3).  
- **SC-005**: After aggregation, each unique alloy composition appears **exactly once** in the processed dataset; the `aggregation.log` records the aggregation method used for every duplicate (See US-4).  
- **SC-006**: The number of descriptor domain‑error events logged in `descriptor_errors.log` equals the number of alloys for which a fallback value of 0.0 was assigned; this count is reported in the final results (See US-4).

## Assumptions

- The public MPEA database (https://doi.org/10.1038/s41597-020-00768-9) contains sufficient entries (≥ 80) of BCC-phase alloys with reported yield strength values to support a statistical regression analysis.
- Elemental properties (atomic radius, electronegativity, valence) can be reliably retrieved from a standard periodic table reference (e.g., NIST or a local static dictionary) without requiring external API calls that might fail or rate‑limit during CI.
- The binary interaction parameters (Ω_ij) used for mixing enthalpy are sourced from **NIST‑JANAF Thermochemical Tables (2022 edition)**, distinct from the experimental yield strength measurements to avoid circular validation.
- The relationship between composition and yield strength in BCC alloys can be approximated by the selected compositional descriptors (δ, VEC, etc.) and ILR coordinates, provided a feature selection step is **not** mandatory (the model relies on the full set of engineered features).
- The GitHub Actions free‑tier runner (multi‑core CPU, standard memory allocation) is sufficient to process the filtered dataset and train the specified scikit‑learn models within the allotted job limit, provided the dataset remains within the size of the original public source.
- The yield strength values reported in the source datasets are measured under comparable conditions (room temperature, standard strain rates) such that they can be pooled without complex normalization for testing conditions.
