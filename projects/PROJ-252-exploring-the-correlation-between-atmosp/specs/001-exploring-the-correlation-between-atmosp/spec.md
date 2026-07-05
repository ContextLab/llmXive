# Feature Specification: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Feature Branch**: `001-explore-pressure-quake-correlation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Do systematic atmospheric pressure anomalies precede earthquakes of magnitude ≥ 4.0, and can these anomalies be distinguished from normal meteorological variability?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

The research system MUST successfully download global sea-level pressure reanalysis data (NOAA NCEP/NCAR) and the USGS earthquake catalog (2013-2023, M≥4.0), then align them spatially and temporally to create a clean, analysis-ready dataset.

**Why this priority**: Without a valid, aligned dataset containing both atmospheric and seismic variables, no statistical analysis can be performed. This is the foundational step for the entire research project.

**Independent Test**: The script MUST exit with code 0. The output CSV row count MUST match the expected count of earthquakes in the 2018 Alaska subset (N=12) within a 1% tolerance. The output MUST contain a validation report confirming all required fields are present.

**Acceptance Scenarios**:

1. **Given** the NOAA and USGS data sources are accessible, **When** the download script runs, **Then** the system retrieves the full 2013-2023 earthquake catalog and the corresponding daily pressure grid files without error.
2. **Given** the raw data files are downloaded, **When** the pre-processing step runs, **Then** the system outputs a master dataset where every earthquake event (M≥4.0, depth≤70km) is paired with pressure anomalies extracted from the nearest 1° grid point for the 0-48h window prior to the event.
3. **Given** the master dataset, **When** the seasonal trend removal is applied, **Then** every record contains a calculated daily pressure anomaly (deviation from a left-censored 30-day moving average) and a control window label.

---

### User Story 2 - Statistical Association Analysis (Priority: P2)

The research system MUST perform statistical tests (Kolmogorov–Smisnov and permutation testing) to determine if pressure anomalies in the pre-earthquake window differ significantly from control windows, framing results as associational evidence.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by quantifying the relationship between pressure and seismic events while adhering to methodological rigor regarding observational data.

**Independent Test**: The analysis can be tested by running the statistical module on the prepared dataset. The output JSON MUST contain a p-value < 0.05 if and only if the observed test statistic is strictly greater than the 95th percentile of the [deferred] permuted statistics. This must be verifiable by a script comparing the observed value to the sorted null array.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with event and control windows, **When** the Kolmogorov–Smirnov test runs, **Then** the system outputs a p-value indicating whether the distribution of pressure anomalies in event windows differs from control windows.
2. **Given** the event labels, **When** the permutation test runs (10,000 shuffles), **Then** the system generates a null distribution of the test statistic and calculates a p-value based on the proportion of permuted statistics exceeding the observed statistic.
3. **Given** the statistical results, **When** the report is generated, **Then** the findings are explicitly framed as "associational" rather than "causal," and any significance (p < 0.05) is accompanied by the calculated effect size (Cohen’s d).

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

The research system MUST validate the primary findings by repeating the analysis across different magnitude thresholds, geographic regions, and seasonal bins, and by performing a sensitivity analysis on the anomaly definition cutoff.

**Why this priority**: Scientific validity requires demonstrating that results are not artifacts of a specific dataset subset or arbitrary parameter choices. This ensures the robustness of the conclusions.

**Independent Test**: The robustness module can be tested by executing the stratified analysis loop. The system MUST output separate p-values and effect sizes for each subset. The sensitivity analysis MUST vary the cutoff by multiples of the background standard deviation (σ) and report the variation in significance rates.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the robustness check runs, **Then** the system outputs separate p-values and effect sizes for subsets defined by magnitude (4.0–5.0, >5.0) and region (Pacific Ring of Fire vs. others).
2. **Given** a defined anomaly threshold (e.g., pressure drop > X σ), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over {0.5σ, 1.0σ, 1.5σ} and reports the variation in significance rates or inconsistency rates.
3. **Given** the full analysis suite, **When** the final report is compiled, **Then** it includes a section detailing whether the primary association holds across different seasonal bins and geographic subsamples, accounting for climate indices.

---

### Edge Cases

- **Ocean Masking**: Events located over oceans where pressure grid interpolation is unreliable MUST be excluded from the analysis or flagged with a specific 'ocean-masked' status.
- **Missing Data**: Earthquakes with missing pressure data for the immediate 0-48h window MUST be excluded from the analysis, not interpolated, to prevent data leakage.
- **Multiple Comparisons**: The system MUST apply a False Discovery Rate (FDR) correction (Benjamini-Hochberg) to the family-wise error rate when testing across multiple regions and thresholds.
- **Duplicate Events**: Duplicate or revised USGS entries MUST be deduplicated based on the unique event ID, retaining the most recent revision.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the NOAA NCEP/NCAR daily global surface pressure data (source resolution 2.5°) and the USGS earthquake catalog (2013-2023, M≥4.0, depth≤70km) from their respective public repositories. (See US-1)
- **FR-002**: System MUST interpolate the 2.5° pressure fields to a 1°×1° grid and extract the nearest grid point (or 3-point average) for every earthquake epicenter to calculate daily pressure anomalies. (See US-1)
- **FR-003**: System MUST compute daily pressure anomalies by subtracting a 30-day moving average calculated from a left-censored window (excluding the event window and the 30 days immediately preceding it) to remove seasonal trends for every event and control window. (See US-1)
- **FR-004**: System MUST perform a two-sample Kolmogorov–Smirnov test and a permutation test (10,000 iterations) to compare pressure anomaly distributions between event and control windows. (See US-2)
- **FR-005**: System MUST frame all statistical findings as "associational" and explicitly avoid causal language in the generated report, acknowledging the observational nature of the data. (See US-2)
- **FR-006**: System MUST apply a multiple-comparison correction (Benjamini-Hochberg False Discovery Rate) to the family-wise error rate when testing across multiple regions and magnitude thresholds. (See US-3)
- **FR-007**: System MUST execute a sensitivity analysis sweeping the anomaly decision cutoff over the set {0.5σ, 1.0σ, 1.5σ} (where σ is the standard deviation of the background pressure field) and report the resulting variation in significance rates and inconsistency rates. (See US-3)
- **FR-008**: System MUST validate that the dataset contains all required variables (pressure, magnitude, depth, latitude, longitude, timestamp) and, if any are missing, MUST exit with error code 1 and output a JSON validation report listing the missing variables. (See US-1)
- **FR-009**: System MUST exclude earthquake events located over ocean regions (where grid interpolation reliability is < 95%) from the final analysis dataset. (See US-1)
- **FR-010**: System MUST exclude earthquake events where pressure data is missing for any part of the 0-48h pre-event window. (See US-1)
- **FR-011**: System MUST stratify control windows by matching on climate indices (ENSO, PDO) to ensure the control group does not contain systematic inter-annual climate trends that differ from the event group. (See US-2, US-3)

### Key Entities

- **Earthquake Event**: Represents a seismic occurrence with attributes: magnitude, depth, latitude, longitude, timestamp.
- **Pressure Grid**: Represents the global sea-level pressure field at daily resolution with attributes: grid coordinates, pressure value, timestamp.
- **Analysis Window**: Represents a time window (event or control) with attributes: start time, end time, calculated anomaly metrics, associated earthquake ID (if event), climate index label.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The association strength (Cohen’s d) and significance (p-value) are measured against the null hypothesis of no difference between event and control windows. (See US-2)
- **SC-002**: The robustness of the findings is measured against the consistency of p-values across different geographic regions and magnitude thresholds. (See US-3)
- **SC-003**: The stability of the anomaly detection is measured against the variation in significance rates when the decision cutoff is swept over {0.5σ, 1.0σ, 1.5σ}. (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of completing the full analysis (download, process, test, report) within the standard time limit on CPU-only hardware. (See US-1, US-2)

## Assumptions

- The NOAA NCEP/NCAR reanalysis data and USGS earthquake catalog are publicly accessible and do not require authentication or special API keys that would fail in a CI environment.
- The dataset (pressure grids + earthquake catalog) fits within the available RAM and disk limits of the GitHub Actions free-tier runner., allowing for in-memory processing of the time-series data.
- The 'left-censored 30-day moving average' is sufficient to remove seasonal trends for the purpose of this study without introducing bias from the event window itself.
- The relationship between atmospheric pressure and seismic activity, if it exists, is linear enough to be captured by standard anomaly metrics (drop magnitude, rate of change) without requiring non-linear feature engineering.
- The 'control windows' generated by matching calendar dates in different years AND stratifying by climate indices (ENSO, PDO) effectively represent the background meteorological variability, assuming no unmeasured confounders.
- The USGS catalog provides consistent magnitude and depth data for the 2013-2023 period without significant revisions that would invalidate the temporal alignment with pressure data.
- The 2.5° resolution of the source NOAA data is sufficient to capture the relevant pressure gradients when interpolated to 1°.