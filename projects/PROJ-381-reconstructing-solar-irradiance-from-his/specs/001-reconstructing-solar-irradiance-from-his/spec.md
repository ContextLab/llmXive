# Feature Specification: Reconstructing Solar Irradiance from Historical Sunspot Records

**Feature Branch**: `001-reconstruct-solar-irradiance`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "How does the relationship between historical sunspot numbers and total solar irradiance (TSI) vary across different solar cycles, and to what extent can sunspot-based reconstructions capture the amplitude of past irradiance fluctuations?"

## User Scenarios & Testing

### User Story 1 - Cycle-Specific TSI Reconstruction Model (Priority: P1) (ID: US-1)

**Description**: The system must ingest historical Group Sunspot Numbers (GSN) and modern satellite TSI data to train a non-linear regression model that maps sunspot counts to Total Solar Irradiance (TSI), explicitly accounting for cycle-to-cycle variability via cycle ID features, while validating generalization using a leave-one-cycle-out strategy.

**Why this priority**: This is the core research engine. Without a model that distinguishes between solar cycles and validates generalization across cycles (not just fit), the project cannot address the primary research question regarding variability. It provides the fundamental dataset and baseline metrics required for all subsequent validation.

**Independent Test**: The model can be fully tested by running the training pipeline on the satellite-era data using a leave-one-cycle-out cross-validation scheme and verifying that it produces a valid reconstruction file with calculated RMSE and R² metrics against the held-out cycle, without requiring pre-satellite data.

**Acceptance Scenarios**:
1. **Given** GSN data (1610–present) and SORCE/TIM TSI data (2003–present) are loaded, **When** the pipeline executes a leave-one-cycle-out cross-validation (training on all cycles except one, e.g., Cycle 23, and validating on the held-out cycle), **Then** the system outputs a model artifact and a cross-validation report containing RMSE and R² values for the held-out cycle.
2. **Given** a trained model artifact, **When** the pipeline evaluates the model on the held-out cycle data, **Then** the system generates a validation report comparing the predicted TSI against observed satellite measurements, calculating the error reduction relative to the 2007 baseline reconstruction.

---

### User Story 2 - Pre-Satellite TSI Reconstruction Generation (Priority: P2) (ID: US-2)

**Description**: The system must apply the calibrated cycle-specific model (or a Cycle-Agnostic fallback for unseen cycles) to the pre-satellite GSN record (early seventeenth century–2002) to generate an updated TSI reconstruction time series, including uncertainty bands derived from the model's confidence intervals.

**Why this priority**: This delivers the primary scientific output: extending the TSI record back to 1610. It relies on the model from P1 but adds the critical historical dimension required for climate attribution studies, ensuring the model handles cycles with no modern analog.

**Independent Test**: The feature is tested by running the application of the trained model (and fallback) to the pre-satellite GSN subset and verifying the output contains a complete time series with corresponding lower and upper uncertainty bounds, distinct from the satellite-era data.

**Acceptance Scenarios**:
1. **Given** the trained model from User Story 1 and the GSN data for 1610–2002, **When** the reconstruction script is executed, **Then** the system outputs a CSV/NetCDF file containing the reconstructed TSI values with associated uncertainty bands for the entire pre-satellite period, using the Cycle-Agnostic fallback for any cycle IDs not seen in training.
2. **Given** the reconstructed TSI time series, **When** the system performs a statistical comparison of variance across major minima (Maunder, Dalton, Modern), **Then** the output includes bootstrap resampling results (1000 iterations) quantifying the variance differences.

---

### User Story 3 - Baseline Comparison and Methodological Validation (Priority: P3) (ID: US-3)

**Description**: The system must rigorously compare the new reconstruction against the baseline reconstruction (Wang et al., 2007) and the CMIP6 v3.2 solar forcing dataset, calculating the percentage reduction in reconstruction error and ensuring methodological constraints (associational framing, multiplicity correction) are documented.

**Why this priority**: This validates the claim of improvement (≥15% error reduction) and ensures the scientific integrity of the findings. It is a validation step that confirms the utility of the P1 and P2 outputs.

**Independent Test**: The feature is tested by executing the comparison module which ingests the new reconstruction, the 2007 baseline, and CMIP6 data, outputting a final report with the specific error reduction metric and a statement on the nature of the findings (associational vs. causal).

**Acceptance Scenarios**:
1. **Given** the new reconstruction and the 2007 baseline reconstruction, **When** the comparison module calculates RMSE over the overlapping satellite era, **Then** the system reports the percentage reduction in error, confirming if it meets or exceeds the ≥15% target.
2. **Given** the final analysis results, **When** the system generates the summary report, **Then** the report explicitly frames all findings as associational (not causal) and documents the multiple‑comparison correction method used for any hypothesis testing.

---

### Edge Cases

- **What happens when** the GSN data contains extended gaps (e.g., during the Maunder Minimum) where linear interpolation is insufficient?
  - *Handling*: The system must flag these regions; no interpolation is performed for gaps ≥ 1 year. Users are alerted to the missing data.
- **How does the system handle** solar cycles where the GSN count is near zero but TSI measurements (if available) show non‑zero variance due to facular activity?
  - *Handling*: The model includes a low‑sunspot offset term derived from satellite‑era periods with near‑zero GSN, ensuring predictions remain > 0 W/m².
- **What happens when** the satellite TSI data (SORCE/TIM) has instrument drift or calibration gaps?
  - *Handling*: The preprocessing step must apply documented calibration corrections using overlapping instrument records and perform a sensitivity analysis on the correction method.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest Group Sunspot Number (GSN) data from the SILSO repository (verified URL:) and modern TSI satellite data (SORCE/TIM preferred, NOAA Composite fallback) for the modern satellite era to establish the training correlation. (See US-1)  
  *Rationale*: The SILSO GSN series is the canonical sunspot proxy used in solar‑irradiance research.

- **FR-002**: System MUST preprocess sunspot data by filling missing values via linear interpolation for gaps **< 1 year**. Gaps **≥ 1 year** are left missing and flagged for downstream handling. The system MUST compute cycle‑averaged sunspot numbers using standard smoothed sunspot number peak detection (SILSO method) to detect cycle boundaries, ensuring boundaries align with known SILSO cycle maxima within ±6 months. (See US-1)

- **FR-003**: System MUST fit non‑linear regression models (Random Forest and Gaussian Process) mapping sunspot numbers to TSI, utilizing Cycle ID (from SILSO definitions) as a categorical feature. **Training data may be the verified SORCE/TIM satellite‑era TSI dataset (preferred) or, if unavailable, the NOAA Composite TSI dataset**, both of which conform to `contracts/dataset.schema.yaml`. The system MUST also train a Cycle‑Agnostic fallback model (GSN‑only) that uses the same TSI training target but omits the Cycle ID feature, to handle pre‑satellite cycles with no analog in the training set. (See US-1)

- **FR-004**: System MUST apply the calibrated model to the pre‑satellite GSN record (early 17th century–2002) to generate an updated TSI reconstruction with uncertainty bands derived from the model's prediction intervals. For any cycle ID not present in the training set, the system MUST use the Cycle‑Agnostic fallback model. (See US-2)

- **FR-005**: System MUST perform a statistical comparison of the reconstructed TSI variance across major solar minima (Maunder, Dalton, Modern) using bootstrap resampling with **1000 iterations** to ensure robust convergence. (See US-2)

- **FR-006**: System MUST explicitly frame all findings as associational rather than causal, given the observational nature of the data and lack of random assignment. (See US-3)

- **FR-007**: System MUST implement a multiple‑comparison correction (e.g., Bonferroni or False Discovery Rate) for any hypothesis tests conducted across multiple solar cycles or time windows. (See US-3)

- **FR-009**: *Removed* – the original idea did not request an inconsistency‑tolerance analysis; therefore this requirement has been eliminated to keep scope aligned.

- **FR-010**: System MUST ingest the CMIP6 v3.2 solar forcing dataset (TSI variable) and validate its schema against `contracts/dataset.schema.yaml`. The CMIP6 data is used **exclusively for independent validation/comparison**, not for model training. (See US-3)

- **FR-011**: System MUST compare the reconstructed TSI series against the ingested CMIP6 solar forcing series as an independent baseline, reporting RMSE and bias metrics. (See US-3)

- **FR-012**: System MUST incorporate a low‑sunspot offset term derived from satellite‑era observations (average TSI during periods where GSN ≈ 0) to avoid predicting zero irradiance when sunspots are absent. The offset is calibrated on the training dataset and applied uniformly across all cycles. (See US-2)

- **FR-013**: If the 2007 baseline TSI reconstruction (Wang et al., 2007) is available, System MUST ingest it in a format conforming to `contracts/dataset.schema.yaml` (fields: `date`, `tsi_value`, `instrument`, `uncertainty`). The baseline dataset is required for secondary comparison metrics; if unavailable, this requirement is not applicable. (See US-3)

- **FR-014**: If a verified SORCE/TIM satellite TSI dataset is available, System MUST ingest it and validate against `contracts/dataset.schema.yaml`; this dataset will serve as the **sole** training target for all regression models. If not available, the NOAA Composite TSI dataset (verified) will be used as the training target instead. (See US-1)

### Key Entities

- **SolarCycle**: A logical entity representing a specific solar activity cycle, defined by start/end years and an average sunspot number, used to group data for cycle‑specific calibration.
- **TSIRecord**: A time‑series entity containing date, TSI value (W/m²), and uncertainty bounds, derived from either satellite measurements or model reconstruction.
- **SunspotRecord**: A time‑series entity containing date, Group Sunspot Number (GSN), and quality flags, sourced from SILSO.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Reconstruction error (RMSE) measured against the **independent** CMIP6 solar forcing dataset over the overlapping satellite validation period (e.g., 2003–2020), **targeting a reduction of ≥ 15 % relative to the CMIP6 baseline RMSE**. As a secondary, optional metric, the system may also report RMSE reduction relative to the 2007 baseline reconstruction when that dataset is available. (See US-1, US-3)

- **SC-002**: Coefficient of determination (R²) measured against observed satellite TSI data for the validation split to quantify the model's explanatory power **when a verified training TSI dataset is available**; if no verified TSI training dataset is present, SC-002 is marked “N/A” and the metric is omitted. (See US-1)

- **SC-003**: Variance of reconstructed TSI measured across the Maunder, Dalton, and Modern minima using bootstrap resampling with **1000 iterations** to quantify statistical differences. (See US-2)

- **SC-004**: Computational resource usage measured against the constraint of **≤ 7 GB RAM and ≤ 6 hours total runtime** (sum of ingestion, preprocessing, training, and inference) on a standard 2‑core CPU runner. (See US-1, US-3)

- **SC-005**: Sensitivity of reconstruction results measured against a sweep of the inconsistency tolerance threshold (absolute differences ∈ {0.01, 0.05, 0.1}); the metric reported is the **maximum absolute change in RMSE** observed across the sweep, demonstrating robustness of the cycle‑specific calibration. (See US-1, US-3)

### Additional Notes

All datasets and generated outputs must conform to the single source‑of‑truth schema `contracts/dataset.schema.yaml`. Output fields such as `rmse_train`, `rmse_validation`, `r2_train`, and `r2_validation` are defined as **nullable**; they may be left null when training is skipped due to unavailable TSI labels, satisfying both the primary and degraded execution paths.

## Assumptions

- **Dataset-variable fit**: The Group Sunspot Number (GSN) dataset from SILSO contains sufficient temporal resolution and historical continuity to serve as the sole predictor for TSI reconstruction, assuming the relationship is mediated by magnetic activity proxies implicitly captured by the non‑linear model.
- **Inference framing**: All correlations between sunspot numbers and TSI are strictly associational; no causal claims regarding solar forcing mechanisms are made without an explicit identification strategy or randomization.
- **Measurement validity**: The SORCE/TIM (or NOAA Composite) satellite data and the SILSO GSN records are considered the ground truth for the satellite era and historical proxy, respectively, without requiring further external validation within this scope.
- **Compute feasibility**: The Random Forest and Gaussian Process models, when trained on the sampled satellite‑era data (2003–present), will fit within 7 GB of RAM and complete training and inference in ≤ 6 hours (processing time only) on a standard 2‑core CPU runner.
- **Threshold justification**: The decision to target a ≥ 15 % RMSE reduction is based on expected gains from incorporating cycle‑specific calibration, as cited in contemporary solar‑irradiance literature; sensitivity analysis (SC‑005) will verify that this target is not an artifact of a specific tolerance choice.
- **Predictor collinearity**: Cycle ID (derived from external SILSO definitions) and sunspot numbers are treated as jointly predictive features; the model does not claim independent predictive effects for Cycle ID beyond its role in modulating the sunspot‑TSI relationship.
- **Cycle ID derivation**: Cycle boundaries are derived from external SILSO historical records, not from the GSN time series being analyzed in the current run, to prevent data leakage.
- **Schema consistency**: All ingested datasets and generated outputs conform to the single source‑of‑truth schema `contracts/dataset.schema.yaml`; this is the canonical schema for the project.
- **Output schema flexibility**: Metric fields in output schemas are nullable to accommodate degraded paths where training data are unavailable.
