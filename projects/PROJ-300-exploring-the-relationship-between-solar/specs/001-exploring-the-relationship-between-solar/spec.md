# Feature Specification: Exploring the Relationship Between Solar Wind Speed and Geomagnetic Tail Reconnection Rates

**Feature Branch**: `PROJ-300-01-solar-wind-reconnection`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Does solar wind speed measured at 1 AU correlate with the magnetic reconnection rate in Earth's geomagnetic tail, and what is the optimal propagation time lag for this coupling?"

## User Scenarios & Testing *(mandatory)*

### User Story US-1 – Quantify Lag‑Adjusted Coupling (Priority: P1)

*As a space‑weather analyst I want to compute the correlation between solar‑wind speed (Vsw) and a tail‑reconnection proxy (Ey) after applying the appropriate propagation lag, so that I can quantify how strongly the upstream driver influences the downstream response.*

**Why this priority**: Establishes the core scientific claim; without a measurable correlation the project's hypothesis cannot be evaluated.

**Independent Test**: Run the analysis pipeline on an appropriate multi‑day interval and verify that the output includes Pearson and Spearman correlation coefficients, their p‑values, and a Bonferroni‑adjusted significance flag.

**Acceptance Scenarios**:

1. **Given** a continuous 1‑minute Vsw series and THEMIS Ey series for the same interval, **when** the pipeline computes the lag‑adjusted series, **then** it returns numeric correlation coefficients and adjusted p‑values.  
2. **Given** the same inputs but with a deliberately introduced NaN gap, **when** the pipeline runs, **then** it cleans the data, resamples, and still produces the correlation output without error.

---

### User Story US-2 – Identify Optimal Propagation Lag (Priority: P2)

*As a researcher I want the system to search a plausible lag window (30–90 min) and report the lag that maximizes the absolute correlation, so that I can use this lag in predictive models.*

**Why this priority**: The lag is the physical link between solar‑wind arrival at L1 and magnetotail response; its correct value is essential for any forecasting application.

**Independent Test**: Execute the lag‑search on a known synthetic dataset where the true lag is 45 min; the pipeline must report 45 min (±1 min) as the optimal lag.

**Acceptance Scenarios**:

1. **Given** a dataset with a hidden lag of 60 min, **when** the lag‑optimization routine scans the 30–90 min window, **then** it selects 60 min as the lag that yields the highest absolute correlation.  

---

### User Story US-3 – Visualise Relationship and Sensitivity (Priority: P3)

*As a scientist I want clear scatter plots and time‑series overlays, plus a sensitivity analysis of any speed‑threshold choices, so that I can assess linearity, possible saturation, and robustness of the result.*

**Why this priority**: Visual diagnostics are required for interpretation and for communicating results to the broader community.

**Independent Test**: After a successful run, the pipeline must produce (a) a scatter plot of lag‑adjusted Vsw vs. Ey with a regression line, (b) a dual‑axis time‑series plot, and (c) a table of correlation values for high‑speed thresholds T ∈ {400, 500, 600} km s⁻¹.

**Acceptance Scenarios**:

1. **Given** the analysis outputs, **when** the user opens the generated PNG files, **then** the scatter plot shows a fitted line and the time‑series plot aligns Vsw and Ey over the full interval.  
2. **Given** the same outputs, **when** the user examines the sensitivity table, **then** the system correctly computes and reports the correlation magnitude for each threshold, allowing the user to assess the variation.

---

### Edge Cases

- **What happens when** either dataset contains extended gaps (≥30 min) that exceed the resampling window?  
- **How does the system handle** extreme solar‑wind speeds (>1000 km s⁻¹) that could produce a lag <30 min, outside the predefined search range?  
- **What if** the THEMIS Ey measurement is missing for a given timestamp?  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest 1‑minute solar‑wind speed (Vsw) and IMF Bz from NASA OMNIWeb for a user‑specified date range. *(See US-1)*
- **FR-002**: System MUST ingest THEMIS magnetotail magnetic and electric‑field data, including the cross‑tail electric field Ey, for the same date range. *(See US-1)*
- **FR-003**: System MUST clean both time series by removing NaN values and resample them to a common 5‑minute cadence using pandas. *(See US-1)*
- **FR-004**: System MUST shift the Vsw series forward by a propagation lag **L** (in minutes) and produce a lag‑adjusted Vsw series. **L** is either a user‑specified value **or** the physics‑based lag computed by FR‑012. *(See US-2)*
- **FR-005**: System MUST calculate Pearson and Spearman correlation coefficients between lag‑adjusted Vsw and Ey, and apply a Bonferroni correction across all tested lags (2 correlation tests × number of lag candidates). The system MUST document in the output report that the Bonferroni correction is conservative for autocorrelated lag searches and may mask true signals; future work should consider permutation testing or False Discovery Rate control for improved power. *(See US-1)*
- **FR-006**: System MUST perform bootstrap resampling with **1000 iterations** to obtain 95 % confidence intervals for each correlation coefficient, thereby accounting for autocorrelation. *(See US-1)*
- **FR-007**: System MUST sweep a high‑speed threshold **T ∈ {400, 500, 600} km s⁻¹**, recompute correlations for each subset, and report the sensitivity of the correlation magnitude to T. The threshold values are chosen because 500 km s⁻¹ is a community‑standard boundary separating slow and fast solar‑wind streams (see *Coronal Holes, 2009*). *(See US-3)*
- **FR-008**: System MUST generate (a) a scatter plot of lag‑adjusted Vsw vs. Ey with a linear regression line, and (b) a dual‑axis time‑series overlay of Vsw and Ey for the full interval, saving each as a PNG file. *(See US-3)*
- **FR-009**: System MUST log the selected optimal lag, all correlation statistics, and any data‑quality warnings to a reproducible JSON report. *(See US-2 & US-3)*
- **FR-010**: System MUST search a lag window centered on the physics‑based lag **L_phys** (from FR‑012) with a ±15 min tolerance, constrained to the overall feasible range **30–90 minutes**, in 5‑minute increments, and identify the lag **L*** that maximizes the absolute Pearson (or Spearman) correlation; the routine must output **L*** and the corresponding correlation values. *(See US-2)*
- **FR-011**: System MUST document the multiple‑comparison correction applied (see FR‑005) and record the total number of lag candidates evaluated, ensuring statistical rigor. *(See US-2)*
- **FR-012**: System MUST compute a physics‑based propagation lag **L_phys** (in minutes) from the mean solar‑wind speed **Vsw_mean** over the selected interval using the nominal Earth‑magnetotail distance of **60 R_E** (where 1 R_E = 6371 km). The formula is:

  \[
  L_{\text{phys}} \;=\; \frac{\text{Distance}}{V_{\text{sw,mean}}} \;\bigg/\; 60
  \;=\; \frac{60 \times 6371\ \text{km}}{V_{\text{sw,mean}}\ (\text{km s}^{-1})}\;\bigg/\;60
  \;=\; \frac{6371}{V_{\text{sw,mean}}}\ \text{minutes}.
  \]

  Here, **Distance = 60 * 6371 km**. This conversion yields a lag expressed in minutes, consistent with all other time‑based parameters. *(See US-1, US-2; conforms to Constitution Principle VII; citation: Kivelson & Russell, *Introduction to Space Physics*, 1995, Chap. 3).*

### Key Entities *(include if feature involves data)*

- **SolarWindRecord**: timestamp, Vsw (km s⁻¹), Bz (nT).  
- **MagnetotailRecord**: timestamp, Ey (mV m⁻¹), ancillary magnetic/electric field components.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system correctly calculates and reports the Pearson and Spearman correlation coefficients, their p‑values, and the Bonferroni‑adjusted significance flag for the optimal lag. *(See US-1)*
- **SC-002**: The system correctly calculates and reports the difference between the optimal lag **L*** and the physics‑based lag **L_phys**. *(See US-2)*
- **SC-003**: The system correctly computes and reports the variation in correlation magnitude across the specified high‑speed thresholds T ∈ {400, 500, 600} km s⁻¹. *(See US-3)*
- **SC-004**: The system correctly computes and reports the 95% bootstrap confidence interval for the chosen correlation coefficient. *(See US-1)*
- **SC-005**: All generated visualisations load without error in a standard web browser and correctly label axes, units, and the optimal lag value. *(See US-3)*

## Assumptions

- OMNIWeb provides **mostly** continuous 1‑minute Vsw and Bz data for the selected interval; occasional gaps may occur and are handled by the cleaning and resampling steps described in FR‑003.  
- **The THEMIS dataset includes a pre‑computed cross‑tail electric field component Ey (in mV m⁻¹) measured by the Electric Field Instrument (EFI); therefore the pipeline can ingest Ey directly without deriving it from other field components.**  
- The distance from the L1 point to the reconnection region in the magnetotail is approximated as **60 R_E** (1 R_E = 6371 km). This distance is the **PRIMARY input** for the physics-based propagation lag calculation in FR‑012 and is not used for any other purpose in the analysis. While the magnetotail reconnection site (X-line) varies dynamically with solar wind pressure and IMF Bz, often ranging from tens to over a hundred R_E, a fixed distance of 60 R_E is used as a necessary simplification for the initial correlation analysis. Future work will address the dynamic nature of the X-line.  
- Autocorrelation in the time series is adequately addressed by the bootstrap procedure; no additional ARIMA modeling is required.  
- The analysis will be executed on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, ≤6 h wall‑time); therefore all computations are limited to CPU‑only Python libraries (pandas, numpy, scipy, matplotlib). No GPU or large‑model inference is involved.  
- **Power analysis for detecting a Pearson correlation of r = 0.30 with α = 0.05 (two‑tailed) and 80% power requires approximately 85 independent samples (Cohen 1992; Faul et al., 2007). At a resampled cadence, a sample set of 85 corresponds to a duration of [deferred] of data. However, due to the high autocorrelation in solar wind data, the effective number of independent samples is significantly lower. To mitigate autocorrelation and ensure sufficient independent points for a robust statistical analysis, we require a minimum of **2 full days** (48 hours) of simultaneous OMNI‑Vsw and THEMIS‑Ey coverage.**
- Multiple‑comparison correction is limited to the two correlation tests across all lag candidates; any additional hypothesis tests introduced later will require an updated correction strategy.  
- The high‑speed threshold values (400, 500, 600 km s⁻¹) are based on standard practice for distinguishing fast solar‑wind streams (see *Coronal Holes, 2009*).  