# Feature Specification: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

**Feature Branch**: `001-climate-smart-eval`  
**Created**: 2026-08-14  
**Status**: Draft  
**Input**: User description: "Assess the impact of climate‑smart agricultural (CSA) practices on food security and yield stability in smallholder systems, explicitly controlling for financial access as a confounder using LSMS-ISA and satellite data."

## Background

Smallholder farmers face increasing climate volatility, yet the specific contribution of Climate-Smart Agricultural (CSA) practices to yield stability remains confounded by socioeconomic factors like access to finance. Existing literature establishes finance as a primary driver of performance but fails to isolate the marginal agronomic effect of specific practices. This project addresses this gap by utilizing the World Bank's Living Standards Measurement Study - Integrated Surveys on Agriculture (LSMS-ISA) for Malawi or Tanzania, combined with Sentinel-2 satellite imagery, to perform a multivariate analysis. The study frames findings as **associational** (observational design) rather than causal, explicitly testing the correlation between a validated CSA Adoption Index and satellite-derived yield stability while controlling for financial access variables.

**Research Hypothesis**  
*The intensity of CSA practice adoption is positively correlated with satellite-derived yield stability (lower coefficient of variation in NDVI) and improved food security (lower HFIAS scores), independent of access to finance.*  
*Because multiple hypotheses are tested (yield stability, food security, and potential interaction effects), a Bonferroni correction is applied, targeting a family-wise error rate of $\alpha = 0.05$ (individual test threshold $\alpha \approx 0.0167$).*

## Methodology Overview

### Study Design
- **Design**: Observational cross-sectional analysis (no random assignment).
- **Data Source**: World Bank LSMS-ISA (Malawi or Tanzania) for ground-truth survey data; Sentinel-2/Landsat 8/9 for remote sensing.
- **Sample Size**: Target $N > 1000$ households (subject to spatial overlap with satellite coverage). If spatial overlap reduces $N$ below a sufficient threshold, results will be aggregated at the village level to maintain statistical power.
- **Variables**:
  - *Predictor*: CSA Adoption Index (binary indicators for practices + extension visit frequency).
  - *Outcomes*: Yield Stability (calculated as Stability Score = 1/CV of NDVI time-series), Food Security (HFIAS).
  - *Confounder*: Access to Finance (binary/continuous).
  - *Controls*: Land size, education, rainfall anomaly.

### Data Acquisition & Processing
- **Spatial Join**: Link household coordinates (fuzzed for privacy) to satellite pixels.
- **Variable Construction**:
  - *Yield Stability*: Calculated as the Stability Score (inverse of the Coefficient of Variation, $1/CV$) of NDVI over the growing season to align positive coefficients with improved stability.
  - *CSA Index*: Sum of validated practice indicators.
- **Statistical Analysis**:
  - **Model 1 (Yield Stability)**: `Stability_Score ~ CSA_Index + Access_to_Finance + Controls`.
  - **Model 2 (Food Security)**: `HFIAS ~ CSA_Index + Access_to_Finance + Controls`.
  - Robust standard errors (Huber-White) to account for heteroskedasticity.
  - Variance Inflation Factor (VIF) diagnostic to check for multicollinearity between predictors.
  - Sensitivity analysis on cloud cover thresholds by sweeping values across a representative range.

### Compute Feasibility
- **Environment**: GitHub Actions free-tier runner (limited CPU resources, limited RAM, A substantial disk capacity is required., no GPU).
- **Methodology**: Classical statistics (scikit-learn/statsmodels) on sampled data. No deep learning or large-model training.
- **Time Limit**: Total execution within a feasible time frame.

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Ingest and Harmonize Multimodal Data (Priority: P1)
**Description**: As a data analyst, I want to download the LSMS-ISA dataset and corresponding Sentinel-2 imagery, perform a spatial join, and construct the analysis-ready dataset so that the regression can be executed.

**Why this priority**: Without a harmonized dataset linking ground reports to satellite signals, no analysis is possible.

**Independent Test**: Verify that the `data/processed/analysis_dataset.csv` exists, contains non-null values for the CSA Index and Stability Score, and passes the `contracts/dataset.schema.yaml` validation.

**Acceptance Scenarios**:
1. **Given** the raw LSMS-ISA and Sentinel-2 data sources, **When** the `src/data/ingest.py` script runs, **Then** a merged dataset is produced where every household record has a linked satellite pixel and a calculated Stability Score. *(Supports SC-001)*
2. **Given** the raw data, **When** the ingestion script encounters a household with missing coordinates, **Then** the record is flagged in the `data/logs/ingestion_errors.log` and excluded from the final analysis dataset. *(Supports SC-002)*

---

### User Story 2 – Execute Statistical Analysis and Diagnostics (Priority: P2)
**Description**: As a researcher, I want to run the multivariate regression models with robust standard errors and perform collinearity diagnostics to ensure the model assumptions are met.

**Why this priority**: This step generates the core scientific evidence (coefficients, p-values) and validates the statistical integrity of the findings.

**Independent Test**: Execution of `src/analysis/run_regression.py` produces a summary file containing regression coefficients, p-values, and VIF scores for both Yield Stability and Food Security models, completing within 60 minutes on CPU.

**Acceptance Scenarios**:
1. **Given** the analysis dataset, **When** the regression script runs, **Then** the output includes tables of coefficients for `CSA_Index`, `Access_to_Finance`, and `Controls` for both models, with p-values calculated using robust standard errors. *(Supports SC-003)*
2. **Given** the fitted models, **When** the collinearity check runs, **Then** the system reports VIF scores for all predictors, and if any VIF > 5, a warning is logged and the model summary is annotated with "Potential Collinearity Detected". *(Supports SC-004)*

---

### User Story 3 – Generate Sensitivity Analysis and Final Report (Priority: P3)
**Description**: As a policy analyst, I want to see how the results change under different cloud cover threshold definitions (sensitivity analysis) and receive a final report with the primary findings and limitations.

**Why this priority**: This ensures the findings are robust to arbitrary cutoff choices and provides the necessary context for interpretation (observational framing).

**Independent Test**: Execution of `src/analysis/sensitivity_check.py` produces a plot and table showing coefficient stability across threshold sweeps, and the final report includes the observational framing disclaimer.

**Acceptance Scenarios**:
1. **Given** the primary regression results, **When** the sensitivity script runs, **Then** the output shows the variation in the `CSA_Index` coefficient magnitude when the cloud cover threshold is swept from a lower bound to an upper bound. *(Supports SC-005)*
2. **Given** the analysis results, **When** the report generator runs, **Then** the PDF report explicitly states that findings are "associational" and not causal, and includes the Bonferroni-adjusted significance threshold. *(Supports SC-006)*

### Edge Cases

- **Boundary Condition**: If the spatial join yields an insufficient number of matched households, the system automatically aggregates data to the village level (mean CSA Index, mean Stability Score) to ensure sufficient sample size for regression.
- **Error Scenario**: If Sentinel-2 data is unavailable for a specific region due to persistent cloud cover (>80% cloudiness for the growing season), the system logs a `MISSING_SATELLITE_DATA` error for that region and excludes it from the analysis, reporting the exclusion count in the final summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache the LSMS-ISA dataset and corresponding Sentinel surface reflectance data for the specified region and growing season. *(See US-1)*
- **FR-002**: System MUST perform a spatial join between household survey coordinates and satellite pixels, calculating the Stability Score (inverse of NDVI CV) for each household's growing season. *(See US-1)*
- **FR-003**: System MUST construct a CSA Adoption Index based on binary indicators of specific practices and extension visit frequency, validating the index against the survey data schema. *(See US-1)*
- **FR-004**: System MUST execute two separate multiple linear regression models: (1) `Stability_Score ~ CSA_Index + Access_to_Finance + Controls` and (2) `HFIAS ~ CSA_Index + Access_to_Finance + Controls`, both using robust standard errors. *(See US-2)*
- **FR-005**: System MUST calculate Variance Inflation Factor (VIF) scores for all predictors in both models to detect multicollinearity and flag any VIF > 5. *(See US-2)*
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the cloud cover threshold over a range of representative values including high-coverage conditions and report the variation in the primary `CSA_Index` coefficient for both models. *(See US-3)*
- **FR-007**: System MUST apply a Bonferroni correction for multiple hypothesis testing (targeting a reduced significance threshold) when determining statistical significance. *(See US-3)*
- **FR-008**: System MUST generate a final report that explicitly frames results as "associational" and includes a disclaimer regarding the lack of random assignment. *(See US-3)*

### Key Entities

- **Household**: Represents a smallholder farming unit; attributes include `household_id`, `location`, `land_size`, `education_level`, `financial_access_flag`.
- **CSA_Adoption_Index**: A composite score derived from binary practice indicators and extension visit counts; represents the intensity of climate-smart practice adoption.
- **Stability_Score**: A derived variable representing the inverse of the Coefficient of Variation ($1/CV$) of NDVI time-series for a specific household's plot, where higher values indicate greater stability.
- **Financial_Access_Confounder**: A variable indicating the household's access to credit or savings, used to control for socioeconomic confounding.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001 (Derived from User Story 1)**: The spatial join successfully links ≥ 95% of valid household records to a corresponding satellite pixel with non-null NDVI data. *(Measured against total valid households in LSMS-ISA)*
- **SC-002 (Derived from User Story 1)**: The ingestion pipeline produces a `data/processed/analysis_dataset.csv` where the percentage of records passing the `contracts/dataset.schema.yaml` validation with no missing `CSA_Index` or `Stability_Score` values is measured and documented. *(Measured against schema contract)*
- **SC-003 (Derived from User Story 2)**: The regression model execution completes within 2 hours on a CPU-only runner, producing a summary file with coefficients and p-values for all specified predictors in both models. *(Measured against GitHub Actions time limit)*
- **SC-004 (Derived from User Story 2)**: The collinearity diagnostic reports VIF scores for all predictors; if any VIF > 5, the system logs a warning and the final report includes a "Collinearity Note" section. *(Measured against VIF threshold of 5)*
- **SC-005 (Derived from User Story 3)**: The sensitivity analysis demonstrates that the variation magnitude of the primary `CSA_Index` coefficient is measured and documented across the threshold sweep over a range of values including moderate and high thresholds. *(Measured against coefficient stability documentation)*
- **SC-006 (Derived from User Story 3)**: The final report explicitly states the family-wise error rate control method (Bonferroni) and the adjusted significance threshold ($\alpha$ adjusted for multiple comparisons). *(Measured against report content checklist)*

## Assumptions

- The World Bank LSMS-ISA dataset for Malawi or Tanzania contains the necessary variables for the CSA Adoption Index (practice indicators, extension visits) and financial access.
- Sentinel-2 or Landsat 8/9 imagery is available for the specific growing seasons corresponding to the survey dates with < 80% cloud cover.
- The household coordinates in the LSMS-ISA dataset are sufficiently precise (or fuzzed appropriately) to allow a spatial join with satellite pixels at the required resolution.
- The relationship between CSA practices and yield stability is linear enough to be modeled by multiple linear regression; non-linear effects are treated as residual noise for this scope.
- The analysis will be performed on a CPU-only environment (GitHub Actions free tier) with $\le$ moderate RAM, requiring the dataset to be sampled or aggregated if it exceeds memory limits.
- The "Access to Finance" variable in the survey data is a valid proxy for the socioeconomic confounder and is not definitionally collinear with the CSA Adoption Index.
- Any thresholds introduced (e.g., for data cleaning or consistency checks) are justified by community standards or sensitivity analysis as required by FR-006.