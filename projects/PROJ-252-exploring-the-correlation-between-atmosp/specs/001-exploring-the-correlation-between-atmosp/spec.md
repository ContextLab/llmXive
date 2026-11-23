# Feature Specification: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Feature Branch**: `001-explore-pressure-quake-correlation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Do systematic atmospheric pressure anomalies precede earthquakes of magnitude ≥ 4.0, and can these anomalies be distinguished from normal meteorological variability?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) (US-1)

The research system MUST successfully download global sea-level pressure reanalysis data (NOAA NCEP/NCAR) and the USGS earthquake catalog (2013-2023, M≥4.0), then align them spatially and temporally to create a clean, analysis-ready dataset.

**Why this priority**: Without a valid, aligned dataset containing both atmospheric and seismic variables, no statistical analysis can be performed. This is the foundational step for the entire research project.

**Independent Test**: The script MUST exit with code 0. The output CSV row count MUST match the expected count of earthquakes in the 2018 Alaska subset (N=12) within a 1% tolerance. The output MUST contain a validation report confirming all required fields are present.

**Acceptance Scenarios**:

1. **Given** the NOAA and USGS data sources are accessible, **When** the download script runs, **Then** the system retrieves the full 2013-2023 earthquake catalog and the corresponding daily pressure grid files without error.
2. **Given** the raw data files are downloaded, **When** the pre-processing step runs, **Then** the system outputs a master dataset where every earthquake event (M≥4.0, depth≤70km) is paired with pressure anomalies extracted from the nearest 1° grid point for the 0-48h window prior to the event.
3. **Given** the master dataset, **When** the seasonal trend removal is applied, **Then** every record contains a calculated daily pressure anomaly (deviation from a left‑censored multi‑day moving average) and a control window label.

---

### User Story 2 - Statistical Association Analysis (Priority: P2) (US-2)

The research system MUST perform statistical tests (block‑permutation testing) to determine if pressure anomalies in the pre‑earthquake window differ significantly from control windows, framing results as associational evidence.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by quantifying the relationship between pressure and seismic events while adhering to methodological rigor regarding observational data.

**Independent Test**: The analysis can be tested by running the statistical module on the prepared dataset. The output JSON MUST contain a p‑value computed from the permutation test and a bootstrap‑derived 95 % confidence interval for Cohen’s d. The script MUST verify that the observed statistic exceeds the 95th percentile of the permuted null distribution before reporting significance.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with event and control windows, **When** the permutation test runs (10,000 iterations, 7‑day block‑permutation preserving temporal autocorrelation), **Then** the system outputs a p‑value and a bootstrap confidence interval for the effect size.
2. **Given** the event labels, **When** the bootstrap resampling runs (a sufficiently large number of resamples), **Then** the system reports the median Cohen’s d and its 95 % confidence interval.
3. **Given** the statistical results, **When** the report is generated, **Then** the findings are explicitly framed as "associational" rather than "causal," and any significance (p < 0.05) is accompanied by the calculated effect size (Cohen’s d) and its confidence interval.
4. **Given** the control‑window generation step, **When** the stratification routine runs, **Then** each control window row in the output CSV includes non‑null ENSO, PDO, local temperature, and humidity values, verified by a validation script that checks for missing entries. (Addresses FR‑011 verification.)

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3) (US-3)

The research system MUST validate the primary findings by repeating the analysis across different magnitude thresholds, geographic regions, and seasonal bins, and by performing a sensitivity analysis on the anomaly definition cutoff and on the baseline gap length.

**Why this priority**: Scientific validity requires demonstrating that results are not artifacts of a specific dataset subset or arbitrary parameter choices. This ensures the robustness of the conclusions.

**Independent Test**: The robustness module can be tested by executing the stratified analysis loop. The system MUST output separate p‑values and effect sizes for each subset. The sensitivity analysis MUST vary the cutoff by multiples of the background standard deviation (σ) and report the variation in significance rates. It MUST also repeat the anomaly calculation using left‑censored moving‑average gaps of 12, 20, and 30 days and report any change in effect size.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the robustness check runs, **Then** the system outputs separate p‑values and effect sizes for subsets defined by magnitude (4.0–5.0, >5.0) and region (Pacific Ring of Fire vs. others).
2. **Given** a defined anomaly threshold (e.g., pressure drop > X σ), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over {0.5σ, 1.0σ, 1.5σ} and reports the variation in significance rates; the maximum absolute difference in p‑values across thresholds must be ≤ 0.05.
3. **Given** the baseline gap sensitivity analysis, **When** the analysis runs with gaps of 12, 20, and 30 days, **Then** the system reports the corresponding Cohen’s d values and verifies that the effect size does not change by more than 0.05 across gap lengths.
4. **Given** the full analysis suite, **When** the final report is compiled, **Then** it includes a section detailing whether the primary association holds across different seasonal bins and geographic subsamples, accounting for climate indices.

---

### Edge Cases

- **Ocean Masking**: Events located over oceans where pressure grid interpolation reliability is < 95 % MUST be excluded from the analysis or flagged with a specific 'ocean-masked' status.
- **Missing Data**: Earthquakes with missing pressure data for the immediate 0-48h window MUST be excluded from the analysis, not interpolated, to prevent data leakage.
- **Multiple Comparisons**: The system MUST apply a hierarchical False Discovery Rate (Benjamini‑Hochberg) correction: the primary overall hypothesis is tested without correction; secondary regional/magnitude tests are corrected using a hierarchical FDR procedure to preserve power.
- **Duplicate Events**: Duplicate or revised USGS entries MUST be deduplicated based on the unique event ID, retaining the most recent revision.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the NOAA NCEP/NCAR daily global surface pressure data (verified URL: https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.surface.html) and the USGS earthquake catalog (2013-2023, M≥4.0, depth≤70km) from their respective public repositories, covering the entire globe. (US-1)
- **FR-002**: System MUST interpolate the coarse pressure fields to a fine‑resolution grid and extract the nearest grid point (or 3‑point average) for every earthquake epicenter to calculate daily pressure anomalies. (US-1)
- **FR-003**: System MUST compute daily pressure anomalies by subtracting a left‑censored moving average (baseline length selectable; default 30 days, gap before event selectable) to remove seasonal trends for every event and control window. (US-1)
- **FR-004**: System MUST perform a block‑permutation test with **10,000 iterations** using a **Weekly block‑permutation scheme** to respect temporal autocorrelation, and MUST also generate **A sufficient number of bootstrap resamples** to obtain a 95 % confidence interval for Cohen’s d. (US-2)
- **FR-005**: System MUST frame all statistical findings as "associational" and explicitly avoid causal language in the generated report, acknowledging the observational nature of the data. (US-2)
- **FR-006**: System MUST apply a hierarchical Benjamini‑Hochberg False Discovery Rate correction: the overall test is primary (no correction), while secondary regional/magnitude tests are corrected within their family using the BH procedure (α = 0.05). (US-3)
- **FR-007**: System MUST execute a sensitivity analysis sweeping the anomaly decision cutoff over a range of standard deviation multiples {0.5σ, 1.0σ, 1.5σ} and report the resulting variation in significance rates (maximum |Δp| ≤ 0.05). (US-3)
- **FR-008**: System MUST validate that the dataset contains all required variables (pressure, magnitude, depth, latitude, longitude, timestamp) and, if any are missing, MUST exit with error code 1 and output a JSON validation report listing the missing variables. (US-1)
- **FR-009**: System MUST exclude earthquake events located over ocean regions where interpolation reliability < 95 %. Reliability is computed as 1 – (distance_to_nearest_grid_point / 200 km); events with reliability < 0.95 are flagged and omitted. (US-1)
- **FR-010**: System MUST exclude earthquake events where pressure data is missing for any part of the pre‑event window. (US-1)
- **FR-011**: System MUST stratify control windows by matching on climate indices (ENSO, PDO) **and** on local temperature and humidity to ensure the control group does not contain systematic inter‑annual climate trends that differ from the event group, and MUST output a CSV where each control window includes the associated ENSO, PDO, temperature, and humidity values (non‑null). (US-2)
- **FR-012**: System MUST conduct a Monte‑Carlo power analysis targeting **≥ 0.80** power for detecting **Cohen’s d = 0.3** (α = 0.05) and, if the calculated power is insufficient, MUST expand the event catalog to include earthquakes of magnitude ≥ 3.5 with appropriate weighting to achieve the target. (US-1)
- **FR-013**: System MUST perform a sensitivity analysis on the left‑censored moving‑average gap length (testing 12, 20, and 30 days) and report the resulting Cohen’s d values; the effect size must not change by more than 0.05 across gap lengths. (US-3)
- **FR-014**: System MUST limit the total downloaded NOAA reanalysis data to **≤ 5 GB** by selecting a verified subset (e.g., 1990‑2023, global, daily) and stream the data without persisting the full archive, ensuring CI disk usage stays within GitHub Actions free‑tier limits. (US-1)

### Key Entities

- **Earthquake Event**: Represents a seismic occurrence with attributes: magnitude, depth, latitude, longitude, timestamp.
- **Pressure Grid**: Represents the global sea‑level pressure field at daily resolution with attributes: grid coordinates, pressure value, timestamp.
- **Analysis Window**: Represents a time window (event or control) with attributes: start time, end time, calculated anomaly metrics, associated earthquake ID (if event), climate index label.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system must successfully complete the full analysis pipeline (download, preprocessing, statistical testing, reporting) and generate a final JSON report containing the computed Cohen’s d, its 95 % bootstrap confidence interval, and the permutation‑test p‑value. Success is defined by **pipeline completion** and **report generation**; the sign of the effect (significant or null) does not affect success. (See US-2)
- **SC-002**: The consistency of findings across strata is measured by the coefficient of variation (CV) of p‑values across all geographic regions and magnitude thresholds; success requires **CV ≤ 0.10**. (See US-3)
- **SC-003**: Stability of anomaly detection across σ thresholds is measured by the maximum absolute difference in p‑values across the swept thresholds {0.5σ, 1.0σ, 1.5σ}; success requires **max |Δp| ≤ 0.05**. (See US-3)
- **SC-004**: (Removed – runtime ceiling was out of scope.) 

## Assumptions

- The NOAA NCEP/NCAR reanalysis data and USGS earthquake catalog are publicly accessible and do not require authentication or special API keys that would fail in a CI environment.
- The dataset (pressure grids + earthquake catalog) fits within the 5 GB limit imposed by the CI runner when using the verified subset and streaming approach.
- The left‑censored moving‑average baseline (default 30 days) with selectable gap length is sufficient to remove seasonal trends without leaking pre‑event signals; sensitivity analysis on gap length will confirm this.
- The relationship between atmospheric pressure and seismic activity, if it exists, can be captured by linear anomaly metrics; non‑linear feature engineering is not required for the primary hypothesis.
- The control windows generated by matching on calendar month, ENSO, PDO, local temperature, and humidity effectively represent background meteorological variability, assuming no unmeasured confounders remain.
- The USGS catalog provides consistent magnitude and depth data for the 2013‑2023 period without significant revisions that would invalidate temporal alignment with pressure data.
- All scripts use fixed random seeds to ensure reproducibility (see Constitution Principle I).

## Constitution

- **Principle I**: All analyses must be reproducible; scripts, data sources, and random seeds shall be version‑controlled.
- **Principle II**: No claim shall exceed the evidential support of the observational data; causal language is prohibited.
- **Principle III**: Statistical thresholds must adhere to community standards (α ≤ 0.05, FDR ≤ 0.05) unless explicitly justified.
- **Principle IV**: Methodological choices that affect inference (e.g., handling of autocorrelation, multiple‑testing correction) must be documented and justified.
- **Principle V**: Results must be reported with effect sizes and uncertainty estimates.
- **Principle VII (Null Result Rigor)**: Null results are valid scientific outcomes; project success is not contingent on detecting a significant effect.

## Verified Datasets

- **NOAA NCEP/NCAR Reanalysis Surface Pressure** – verified public URL: https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.surface.html  
  (Accessed via OPeNDAP; subset selected to stay ≤ 5 GB.)
