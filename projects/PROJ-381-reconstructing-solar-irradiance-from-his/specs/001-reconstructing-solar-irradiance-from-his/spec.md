# Feature Specification: Reconstructing Solar Irradiance from Historical Sunspot Records

**Feature Branch**: `001-reconstruct-solar-irradiance`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Reconstructing Solar Irradiance from Historical Sunspot Records"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cycle-Specific TSI Reconstruction Model (Priority: P1)

**Journey**: The researcher downloads the Group Sunspot Number (GSN) and satellite-era TSI data, runs the cycle-aware regression pipeline, and obtains a reconstructed TSI time series that accounts for varying sunspot-TSI relationships across different solar cycles.

**Why this priority**: This is the core scientific deliverable. Without a model that distinguishes between cycles, the reconstruction cannot capture the amplitude fluctuations mentioned in the research question, rendering the project unable to constrain climate model sensitivity.

**Independent Test**: Can be fully tested by executing the training script on the satellite-era split (2003–2015) and validating against the held-out set (2016–present), confirming that the model produces a valid TSI time series with cycle-specific calibration.

**Acceptance Scenarios**:

1. **Given** the GSN and SORCE/TIM datasets are preprocessed and split into training/validation sets, **When** the non-linear regression model (Random Forest or Gaussian Process) is trained with cycle ID and a facular proxy as features, **Then** the model outputs a reconstructed TSI time series for the validation period with an RMSE that is ≥ 15% lower than the 2007 baseline reconstruction (re-run on the same split), representing a relative improvement metric rather than an absolute validation of physical truth.
2. **Given** the trained model, **When** it is applied to the pre-satellite GSN data (1610–2002), **Then** the system generates a continuous TSI reconstruction with uncertainty bands derived from the cross-validation performance, and, where available, independent verification against cosmogenic isotope proxies (14C, 10Be) to assess accuracy.
3. **Given** the reconstructed TSI data, **When** the variance is compared across major solar minima (Maunder, Dalton, Modern), **Then** the system produces statistical summaries (e.g., mean, variance) that distinguish between these historical periods.

---

### User Story 2 - Baseline Comparison and Error Reduction Validation (Priority: P2)

**Journey**: The researcher compares the new reconstruction against the 2007 baseline and the CMIP6 v3.2 dataset to verify that the new method reduces reconstruction error by at least 15% during the satellite era.

**Why this priority**: This validates the specific hypothesis of the research question. It confirms whether the added complexity of cycle-specific calibration yields a tangible improvement over existing simplified models.

**Independent Test**: Can be tested by running the comparison script which ingests the new reconstruction, the 2007 baseline, and the ground-truth satellite TSI, then calculates the percentage reduction in RMSE.

**Acceptance Scenarios**:

1. **Given** the new cycle-specific reconstruction and the 2007 baseline reconstruction, **When** both are compared against the satellite-era ground truth (SORCE/TIM), **Then** the system reports an RMSE reduction of ≥ 15% for the new method, treating the 2007 baseline as a fixed, external reference that is not re-tuned on the specific 2003-2015 split.
2. **Given** the CMIP6 solar forcing dataset (v3.2), **When** the new reconstruction is aligned with this dataset for the overlapping period, **Then** the system generates a difference plot and a correlation coefficient indicating improved agreement with modern observations.

---

### User Story 3 - Statistical Significance of Variance Differences (Priority: P3)

**Journey**: The researcher performs block-bootstrap resampling to determine if the observed differences in TSI variance between major solar minima (e.g., Maunder Minimum vs. Modern Maximum) are statistically significant.

**Why this priority**: This addresses the "extent" part of the research question, providing rigorous statistical evidence for historical climate forcing variations rather than just point estimates.

**Independent Test**: Can be tested by executing the block-bootstrap resampling module on the reconstructed pre-satellite TSI data and verifying the generation of p-values or confidence intervals for variance differences.

**Acceptance Scenarios**:

1. **Given** the reconstructed TSI time series for the 1610–2002 period, **When** A sufficient number of block-bootstrap iterations are performed to resample variance estimates. for the Maunder, Dalton, and Modern minima (accounting for autocorrelation), **Then** the system outputs a table of p-values indicating whether the variance differences between these periods are statistically significant (p < 0.05).
2. **Given** the resampled distributions, **When** the system generates a visualization of the variance confidence intervals, **Then** the intervals for distinct solar minima do not overlap if the difference is deemed meaningful (specifically, non-overlapping 95% confidence intervals).

---

### Edge Cases

- What happens when the Group Sunspot Number data has missing values in critical transition periods between solar cycles? (Handled by linear interpolation as per methodology).
- How does the system handle the discontinuity or scaling differences between the historical GSN and the satellite-era TSI measurements? (Handled by the cycle-specific calibration feature).
- What if the Random Forest model overfits to the short satellite-era training window (2003–2015)? (Mitigated by 5-fold cross-validation and Gaussian Process regularization).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess the Group Sunspot Number (GSN) data from SILSO and satellite-era TSI data from SORCE/TIM, filling missing values via linear interpolation (See US-1).
- **FR-002**: System MUST implement a non-linear regression model (Random Forest or Gaussian Process) that accepts sunspot numbers, cycle ID, and a facular proxy (e.g., Ca II K or Mg II indices) as inputs to predict TSI. If a facular proxy is unavailable, the system MUST document a scientific justification for relying solely on GSN + Cycle ID (See US-1).
- **FR-003**: System MUST split the satellite-era data into a training set (2003–2015) and a validation set (2016–present) to prevent data leakage (See US-1).
- **FR-004**: System MUST perform 5-fold cross-validation on the training set to tune model hyperparameters and report CV metrics; the system MUST also evaluate the final model on the held-out validation set (2016–present) to determine if the R² score meets the target defined in SC-002 (See US-1).
- **FR-005**: System MUST apply the calibrated model to the pre-satellite GSN data (1610–2002) to generate a reconstructed TSI time series with uncertainty bands (See US-1).
- **FR-006**: System MUST compare the new reconstruction against the 2007 baseline to calculate the percentage reduction in RMSE, ensuring the baseline is treated as a fixed reference (See US-2).
- **FR-007**: System MUST perform block-bootstrap resampling on the reconstructed variance of major solar minima to test for statistical significance, accounting for time-series autocorrelation (See US-3).
- **FR-008**: System MUST frame all findings regarding historical solar forcing as associational rather than causal, given the observational nature of the data (See US-2).
- **FR-009**: System MUST compare the correlation coefficient of the new reconstruction with the CMIP6 v3.2 dataset against the correlation of the 2007 baseline, requiring the new model to be at least as high as the baseline (See US-2).

### Key Entities

- **Sunspot Record**: Time-series data of Group Sunspot Numbers (GSN) from 1610 to present, including cycle boundaries.
- **TSI Measurement**: Time-series data of Total Solar Irradiance from satellite instruments (SORCE/TIM) for the period 2003–present.
- **Reconstruction Model**: The trained non-linear regression model mapping sunspot numbers and facular proxies to TSI, parameterized by solar cycle ID.
- **Solar Cycle**: A discrete period of solar activity used as a categorical feature to calibrate the sunspot-TSI relationship.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The RMSE of the new reconstruction on the held-out satellite validation set (2016–present) is measured against the RMSE of the 2007 baseline reconstruction (re-run on the same split) to verify a ≥ 15% reduction, acknowledging this as a relative metric (See FR-006, US-2).
- **SC-002**: The R² score of the model on the held-out validation set (2016–present) is measured against the R² score of the 2007 baseline to ensure the new method is at least comparable or improved (See FR-004, US-1).
- **SC-003**: The statistical significance (p-value) of the variance difference between the Maunder Minimum and Modern Maximum is measured against a conventional alpha level using a sufficient number of block-bootstrap iterations to ensure robust convergence.. (See FR-007, US-3).
- **SC-004**: The correlation coefficient between the new reconstruction and the CMIP6 v3.2 dataset for the overlapping period is measured against the correlation of the 2007 baseline to verify the new model is at least as high (See FR-009, US-2).

## Assumptions

- The SILSO GSN dataset contains sufficient temporal resolution and coverage from the early modern period to present. to support cycle boundary detection via Hilbert-Huang transform.
- The satellite-era TSI data from SORCE and TIM is sufficiently consistent to serve as a ground truth for training, despite potential instrument calibration drifts (assumed handled by standard preprocessing).
- The relationship between sunspot numbers and TSI is sufficiently non-linear to warrant Random Forest or Gaussian Process models over simple linear regression.
- The GitHub Actions free-tier runner (multiple CPU cores, ample RAM) provides a sufficient runtime budget to train the chosen non-linear models on the sampled dataset without requiring GPU acceleration or 8-bit quantization.
- The 2007 baseline reconstruction and CMIP6 v3.2 datasets are available via the provided URLs and are compatible with the Python data processing stack.
- The "cycle-specific calibration" approach assumes that solar cycles are distinct enough to be treated as categorical features without overfitting the small satellite-era dataset.
- The facular proxy data (Ca II K or Mg II) is available for the satellite era to support the model requirements.