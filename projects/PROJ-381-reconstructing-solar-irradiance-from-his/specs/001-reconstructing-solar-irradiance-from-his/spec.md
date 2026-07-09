# Feature Specification: Reconstructing Solar Irradiance from Historical Sunspot Records

**Feature Branch**: `001-reconstruct-solar-irradiance`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "How does the relationship between historical sunspot numbers and total solar irradiance (TSI) vary across different solar cycles, and to what extent can sunspot-based reconstructions capture the amplitude of past irradiance fluctuations?"

## User Scenarios & Testing

### User Story 1 - Cycle-Specific TSI Reconstruction Model (Priority: P1)

**Description**: The system must ingest historical Group Sunspot Numbers (GSN) and modern satellite TSI data to train a non-linear regression model that maps sunspot counts to Total Solar Irradiance (TSI), explicitly accounting for cycle-to-cycle variability via cycle ID features, while validating generalization using a leave-one-cycle-out strategy.

**Why this priority**: This is the core research engine. Without a model that distinguishes between solar cycles and validates generalization across cycles (not just fit), the project cannot address the primary research question regarding variability. It provides the fundamental dataset and baseline metrics required for all subsequent validation.

**Independent Test**: The model can be fully tested by running the training pipeline on the satellite-era data using a leave-one-cycle-out validation scheme and verifying that it produces a valid reconstruction file with calculated RMSE and R² metrics against the held-out cycle, without requiring pre-satellite data.

**Acceptance Scenarios**:
1. **Given** GSN data (1610–present) and SORCE/TIM TSI data (2003–present) are loaded, **When** the pipeline executes a leave-one-cycle-out cross-validation (training on all cycles except one, e.g., Cycle 23, and validating on the held-out cycle), **Then** the system outputs a model artifact and a cross-validation report containing RMSE and R² values for the held-out cycle.
2. **Given** a trained model artifact, **When** the pipeline evaluates the model on the held-out cycle data, **Then** the system generates a validation report comparing the predicted TSI against observed satellite measurements, calculating the error reduction relative to the 2007 baseline.

---

### User Story 2 - Pre-Satellite TSI Reconstruction Generation (Priority: P2)

**Description**: The system must apply the calibrated cycle-specific model (or a Cycle-Agnostic fallback for unseen cycles) to the pre-satellite GSN record (early seventeenth century–2002) to generate an updated TSI reconstruction time series, including uncertainty bands derived from the model's confidence intervals.

**Why this priority**: This delivers the primary scientific output: extending the TSI record back to 1610. It relies on the model from P1 but adds the critical historical dimension required for climate attribution studies, ensuring the model handles cycles with no modern analog.

**Independent Test**: The feature is tested by running the application of the trained model (and fallback) to the pre-satellite GSN subset and verifying the output contains a complete time series with corresponding lower and upper uncertainty bounds, distinct from the satellite-era data.

**Acceptance Scenarios**:
1. **Given** the trained model from User Story 1 and the GSN data for 1610–2002, **When** the reconstruction script is executed, **Then** the system outputs a CSV/NetCDF file containing the reconstructed TSI values with associated uncertainty bands for the entire pre-satellite period, using the Cycle-Agnostic fallback for any cycle IDs not seen in training.
2. **Given** the reconstructed TSI time series, **When** the system performs a statistical comparison of variance across major minima (Maunder, Dalton, Modern), **Then** the output includes bootstrap resampling results (1000 iterations) quantifying the variance differences.

---

### User Story 3 - Baseline Comparison and Methodological Validation (Priority: P3)

**Description**: The system must rigorously compare the new reconstruction against the 2007 baseline and CMIP6 v3.2 dataset, calculating the percentage reduction in reconstruction error and ensuring methodological constraints (associational framing, multiplicity correction) are documented.

**Why this priority**: This validates the claim of improvement (≥15% error reduction) and ensures the scientific integrity of the findings. It is a validation step that confirms the utility of the P1 and P2 outputs.

**Independent Test**: The feature is tested by executing the comparison module which ingests the new reconstruction, the 2007 baseline, and CMIP6 data, outputting a final report with the specific error reduction metric and a statement on the nature of the findings (associational vs. causal).

**Acceptance Scenarios**:
1. **Given** the new reconstruction and the 2007 baseline reconstruction, **When** the comparison module calculates RMSE over the overlapping satellite era, **Then** the system reports the percentage reduction in error, confirming if it meets or exceeds the [deferred] target.
2. **Given** the final analysis results, **When** the system generates the summary report, **Then** the report explicitly frames all findings as associational (not causal) and documents the multiple-comparison correction method used for any hypothesis testing.

---

### Edge Cases

- **What happens when** the GSN data contains extended gaps (e.g., during the Maunder Minimum) where linear interpolation is insufficient?
  - *Handling*: The system must flag these regions and apply a specific "low-activity" proxy (GSN=0 baseline derived from modern minimum mean TSI) rather than defaulting to linear interpolation which would artificially inflate TSI.
- **How does the system handle** solar cycles where the GSN count is near zero but TSI measurements (if available) show non-zero variance due to facular activity?
  - *Handling*: The model must include a non-zero baseline offset or a separate facular proxy term to prevent predicting TSI = 0 when sunspots are absent.
- **What happens when** the satellite TSI data (SORCE/TIM) has instrument drift or calibration gaps?
  - *Handling*: The preprocessing step must include a documented calibration correction or gap-filling strategy using the overlapping instrument data, with sensitivity analysis on the correction method.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest Group Sunspot Number (GSN) data from SILSO and modern TSI satellite data (SORCE/TIM) for the period 2003–present to establish the training correlation. (See US-1)
- **FR-002**: System MUST preprocess sunspot data by filling missing values via linear interpolation for gaps < 1 year, and applying a low-activity proxy (fixed value of 1360.5 W/m², derived from the mean TSI of the 2008–2019 minimum) for gaps ≥ 1 year. The system MUST compute cycle-averaged sunspot numbers using standard smoothed sunspot number peak detection (SILSO method) to detect cycle boundaries, ensuring boundaries align with known SILSO cycle maxima within ±6 months. (See US-1)
- **FR-003**: System MUST fit non-linear regression models (Random Forest and Gaussian Process) mapping sunspot numbers to TSI, utilizing Cycle ID (from SILSO definitions) as a categorical feature. The system MUST also train a Cycle-Agnostic fallback model (GSN-only) to handle pre-satellite cycles with no analog in the training set. (See US-1)
- **FR-004**: System MUST apply the calibrated model to the pre-satellite GSN record (early 17th century–2002) to generate an updated TSI reconstruction with uncertainty bands derived from the model's prediction intervals. For any cycle ID not present in the training set, the system MUST use the Cycle-Agnostic fallback model. (See US-2)
- **FR-005**: System MUST perform a statistical comparison of the reconstructed TSI variance across major solar minima (Maunder, Dalton, Modern) using bootstrap resampling with a sufficient number of iterations to ensure robust convergence. (See US-2)
- **FR-006**: System MUST explicitly frame all findings as associational rather than causal, given the observational nature of the data and lack of random assignment. (See US-3)
- **FR-007**: System MUST implement a multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) for any hypothesis tests conducted across multiple solar cycles or time windows. (See US-3)
- **FR-008**: System MUST execute the entire analysis pipeline on a CPU-only environment with ≤7 GB RAM, ensuring no GPU-specific libraries (CUDA, bitsandbytes) are invoked. (See US-1)
- **FR-009**: System MUST define the "inconsistency tolerance threshold" as the maximum allowed absolute difference between cycle-specific calibration coefficients, and must support a sensitivity analysis sweeping this threshold over absolute differences ∈ {0.01, 0.05, 0.1}. (See US-1, US-3)

### Key Entities

- **SolarCycle**: A logical entity representing a specific solar activity cycle, defined by start/end years and an average sunspot number, used to group data for cycle-specific calibration.
- **TSIRecord**: A time-series entity containing date, TSI value (W/m²), and uncertainty bounds, derived from either satellite measurements or model reconstruction.
- **SunspotRecord**: A time-series entity containing date, Group Sunspot Number (GSN), and quality flags, sourced from SILSO.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Reconstruction error (RMSE) measured against the historical baseline reconstruction over the satellite validation period (2016–present), targeting a reduction of ≥ 15%. (See US-1, US-3)
- **SC-002**: Coefficient of determination (R²) measured against observed satellite TSI data for the validation split to quantify the model's explanatory power. (See US-1)
- **SC-003**: Variance of reconstructed TSI measured across the Maunder, Dalton, and Modern minima using bootstrap resampling with a sufficient number of iterations to quantify statistical differences. (See US-2)
- **SC-004**: Computational resource usage measured against the constraint of ≤7 GB RAM and ≤6 hours total runtime (defined as the sum of data ingestion, preprocessing, training, and inference steps, excluding data download) on a CPU-only runner. (See US-1, US-3)
- **SC-005**: Sensitivity of reconstruction results measured against a sweep of the inconsistency tolerance threshold (absolute diff ∈ {0.01, 0.05, 0.1}) defined in FR-009 to ensure robustness of the cycle-specific calibration. (See US-1, US-3)

## Assumptions

- **Dataset-variable fit**: The Group Sunspot Number (GSN) dataset from SILSO contains sufficient temporal resolution and historical continuity to serve as the sole predictor for TSI reconstruction, assuming the relationship is mediated by magnetic activity proxies not explicitly measured in GSN but captured by the non-linear model.
- **Inference framing**: All correlations between sunspot numbers and TSI are strictly associational; no causal claims regarding solar forcing mechanisms are made without an explicit identification strategy or randomization.
- **Measurement validity**: The SORCE/TIM satellite data and the SILSO GSN records are considered the ground truth for the satellite era and historical proxy, respectively, without requiring further external validation of the source instruments within this scope.
- **Compute feasibility**: The Random Forest and Gaussian Process models, when trained on the sampled satellite-era data (2003–present), will fit within 7 GB of RAM and complete training and inference in ≤6 hours (processing time only) on a standard 2-core CPU runner.
- **Threshold justification**: The decision to use a significant error reduction target is based on the expected improvement from incorporating cycle-specific calibration, as cited in the motivation; sensitivity analysis will sweep the cutoff to verify this target is not an artifact of a specific threshold choice.
- **Predictor collinearity**: Cycle ID (derived from external SILSO definitions) and sunspot numbers are treated as jointly predictive features; the model does not claim independent predictive effects for Cycle ID beyond its role in modulating the sunspot-TSI relationship.
- **Cycle ID derivation**: Cycle boundaries are derived from external SILSO historical records, not from the GSN time series being analyzed in the current run, to prevent data leakage.