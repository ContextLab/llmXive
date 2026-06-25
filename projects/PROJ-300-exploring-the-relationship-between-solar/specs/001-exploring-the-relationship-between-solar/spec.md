# Feature Specification: Exploring the Relationship Between Solar Wind Speed and Geomagnetic Tail Reconnection Rates

**Feature Branch**: `PROJ-300-01-solar-wind-reconnection`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: “Does solar wind speed measured at 1 AU correlate with the magnetic reconnection rate in Earth's geomagnetic tail, and what is the optimal propagation time lag for this coupling?”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify Lag‑Adjusted Coupling (Priority: P1)

*As a space‑weather analyst I want to compute the correlation between solar‑wind speed (Vsw) and a tail‑reconnection proxy (Ey) after applying the appropriate propagation lag, so that I can quantify how strongly the upstream driver influences the downstream response.*

**Why this priority**: Establishes the core scientific claim; without a measurable correlation the project’s hypothesis cannot be evaluated.

**Independent Test**: Run the analysis pipeline on an appropriate multi‑day interval and verify that the output includes Pearson and Spearman correlation coefficients, their p‑values, and a Bonferroni‑adjusted significance flag.

**Acceptance Scenarios**:

1. **Given** a continuous 1‑minute Vsw series and THEMIS Ey series for the same interval, **when** the pipeline computes the lag‑adjusted series, **then** it returns numeric correlation coefficients and adjusted p‑values.  
2. **Given** the same inputs but with a deliberately introduced NaN gap, **when** the pipeline runs, **then** it cleans the data, resamples, and still produces the correlation output without error.

---

### User Story 2 – Identify Optimal Propagation Lag (Priority: P2)

*As a researcher I want the system to search a plausible lag window (30–90 min) and report the lag that maximizes the absolute correlation, so that I can use this lag in predictive models.*

**Why this priority**: The lag is the physical link between solar‑wind arrival at L1 and magnetotail response; its correct value is essential for any forecasting application.

**Independent Test**: Execute the lag‑search on a known synthetic dataset where the true lag is 45 min; the pipeline must report 45 min (±1 min) as the optimal lag.

**Acceptance Scenarios**:

1. **Given** a dataset with a hidden lag of 60 min, **when** the lag‑optimization routine scans the 30–90 min window, **then** it selects 60 min as the lag that yields the highest absolute correlation.  

---

### User Story 3 – Visualise Relationship and Sensitivity (Priority: P3)

*As a scientist I want clear scatter plots and time‑series overlays, plus a sensitivity analysis of any speed‑threshold choices, so that I can assess linearity, possible saturation, and robustness of the result.*

**Why this priority**: Visual diagnostics are required for interpretation and for communicating results to the broader community.

**Independent Test**: After a successful run, the pipeline must produce (a) a scatter plot of lag‑adjusted Vsw vs. Ey with a regression line, (b) a dual‑axis time‑series plot, and (c) a table of correlation values for high‑speed thresholds T ∈ {400, 500, 600} km s⁻¹.

**Acceptance Scenarios**:

1. **Given** the analysis outputs, **when** the user opens the generated PNG files, **then** the scatter plot shows a fitted line and the time‑series plot aligns Vsw and Ey over the full interval.  
2. **Given** the same outputs, **when** the user examines the sensitivity table, **then** the correlation magnitude varies by less than 0.05 across the three thresholds.

---

### Edge Cases

- **What happens when** either dataset contains extended gaps (≥30 min) that exceed the resampling window?  
- **How does the system handle** extreme solar‑wind speeds (>1000 km s⁻¹) that could produce a lag <30 min, outside the predefined search range?  
- **What if** the THEMIS Ey measurement is missing for a given timestamp?  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest 1‑minute solar‑wind speed (Vsw) and IMF Bz from NASA OMNIWeb for a user‑specified date range. *(See US-1)*
- **FR-002**: System MUST ingest THEMIS magnetotail magnetic and electric‑field data, including the cross‑tail electric field Ey, for the same date range. *(See US-1)*
- **FR-003**: System MUST clean both time series by removing NaN values and resample them to a common 5‑minute cadence using pandas. *(See US-1)*
- **FR-004**: System MUST compute a propagation lag **L = D / Vsw** where **D = 60 R_E ≈ 3.8 × 10⁵ km**, shift the Vsw series forward by L (rounded to the nearest 5‑min bin), and produce a lag‑adjusted Vsw series. *(See US-2)*
- **FR-005**: System MUST calculate Pearson and Spearman correlation coefficients between lag‑adjusted Vsw and Ey, and apply a Bonferroni correction for the two tests. *(See US-1)*
- **FR-006**: System MUST perform bootstrap resampling with **1000 iterations** to obtain 95 % confidence intervals for each correlation coefficient, thereby accounting for autocorrelation. *(See US-1)*
- **FR-007**: System MUST sweep a high‑speed threshold **T ∈ {400, 500, 600} km s⁻¹**, recompute correlations for each subset, and report the sensitivity of the correlation magnitude to T. The threshold values are chosen because 500 km s⁻¹ is a community‑standard boundary separating slow and fast solar‑wind streams (see e.g., *Coronal Holes, 2009*). *(See US-3)*
- **FR-008**: System MUST generate (a) a scatter plot of lag‑adjusted Vsw vs. Ey with a linear regression line, and (b) a dual‑axis time‑series overlay of Vsw and Ey for the full interval, saving each as a PNG file. *(See US-3)*
- **FR-009**: System MUST log the selected optimal lag, all correlation statistics, and any data‑quality warnings to a reproducible JSON report. *(See US-2 & US-3)*

### Key Entities *(include if feature involves data)*

- **SolarWindRecord**: timestamp, Vsw (km s⁻¹), Bz (nT).  
- **MagnetotailRecord**: timestamp, Ey (mV m⁻¹), ancillary magnetic/electric field components.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The absolute Pearson correlation |r| for the optimal lag is **≥ 0.30** and remains statistically significant after Bonferroni correction (adjusted *p* < 0.05). *(See US-1)*
- **SC-002**: The lag that maximizes the absolute correlation lies within **30–90 minutes**, consistent with the assumed 60 R_E propagation distance. *(See US-2)*
- **SC-003**: Varying the high‑speed threshold T by ±100 km s⁻¹ changes the correlation magnitude by **< 0.05**, demonstrating robustness of the result. *(See US-3)*
- **SC-004**: The 95 % bootstrap confidence interval for the chosen correlation coefficient does **not include zero**, confirming that the observed relationship is not a product of random autocorrelation. *(See US-1)*
- **SC-005**: All generated visualisations load without error in a standard web browser and correctly label axes, units, and the optimal lag value. *(See US-3)*

## Assumptions

- OMNIWeb provides continuous, gap‑free 1‑minute Vsw and Bz data for the selected interval.  
- **[NEEDS CLARIFICATION: Does the THEMIS dataset contain a pre‑computed Ey measurement, or must Ey be derived from magnetic and electric field components?]**  
- The distance from the L1 point to the reconnection region in the magnetotail is approximated as **60 R_E**; variations in field‑line length are ignored.  
- Autocorrelation in the time series is adequately addressed by the bootstrap procedure; no additional ARIMA modeling is required.  
- The analysis will be executed on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, ≤6 h wall‑time); therefore all computations are limited to CPU‑only Python libraries (pandas, numpy, scipy, matplotlib). No GPU or large‑model inference is involved.  
- **[NEEDS CLARIFICATION: What minimum number of days of simultaneous OMNI/​THEMIS coverage is required to achieve >80 % statistical power for detecting r = 0.30?]**  
- Multiple‑comparison correction is limited to the two correlation tests (Pearson & Spearman); any additional hypothesis tests introduced later will require an updated correction strategy.  
- The high‑speed threshold values (400, 500, 600 km s⁻¹) are based on standard practice for distinguishing fast solar‑wind streams (see *Coronal Holes, 2009*).  

---
