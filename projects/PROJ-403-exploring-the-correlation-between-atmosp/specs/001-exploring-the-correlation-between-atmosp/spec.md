# Feature Specification: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

**Feature Branch**: `001-atmospheric-river-geopotential-correlation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability"

## User Scenarios & Testing

### User Story 1 - Global AR Frequency and Z500 Anomaly Correlation Analysis (Priority: P1)

The researcher needs to compute the temporal correlation between monthly Atmospheric River (AR) frequency counts and 500 hPa geopotential height (Z500) anomalies across defined latitudinal bands and seasons to identify large-scale circulation drivers.

**Why this priority**: This is the core research objective. Without establishing the primary correlation metric, no secondary analysis (spatial mapping, sensitivity) provides value. It directly addresses the "What is NOT known" gap in the literature.

**Independent Test**: Can be fully tested by executing the correlation pipeline on a subset of the ERA5 dataset (e.g., one year, one band) and verifying that a correlation coefficient matrix is produced with valid statistical significance markers.

**Acceptance Scenarios**:

1. **Given** the ERA5 dataset contains water vapor transport and Z500 data for 1979–2023, **When** the system calculates monthly AR frequency and Z500 anomalies for a specific latitudinal band (e.g., 30°–40°N), **Then** the system outputs a Pearson correlation coefficient and p-value for every grid cell within that band/season combination.
2. **Given** a valid correlation result, **When** the Benjamini-Hochberg False Discovery Rate (FDR) correction is applied across all tested grid cells, **Then** the system flags correlations as "significant" only if the adjusted p-value is < 0.05.
3. **Given** the dataset spans multiple seasons, **When** the analysis is run, **Then** the output distinguishes correlation strengths by season (e.g., DJF, MAM, JJA, SON) rather than averaging them globally.
4. **Given** a set of significant correlations, **When** the validation step executes, **Then** the system cross-references the spatial patterns with established teleconnection indices (PNA, NAO) to confirm physical plausibility.

---

### User Story 2 - Spatial Visualization of Significant Covariation (Priority: P2)

The researcher needs to generate spatial maps highlighting regions where AR frequency significantly covaries with Z500 anomalies to visualize the geographic extent of the circulation link.

**Why this priority**: Visualization is essential for interpreting the correlation results and communicating findings (e.g., identifying storm-track regions). It transforms abstract coefficients into actionable geographic insights.

**Independent Test**: Can be tested by running the analysis on a pre-computed dataset and verifying that the system generates a PNG or NetCDF file containing a global map with color-coded correlation values and masked non-significant regions.

**Acceptance Scenarios**:

1. **Given** a set of statistically significant correlation coefficients for each grid cell, **When** the visualization module executes, **Then** it generates a global map where only cells with adjusted p < 0.05 (post-FDR) are colored.
2. **Given** the map generation process, **When** the system encounters a region with no data (e.g., poles or ocean gaps), **Then** those regions are rendered as transparent or masked rather than zeroed out.
3. **Given** the output format, **When** the researcher downloads the map, **Then** the file includes a color bar legend indicating the correlation strength range (-1.0 to 1.0).

---

### User Story 3 - Threshold Sensitivity and Robustness Analysis (Priority: P3)

The researcher needs to verify that the correlation results are robust to small variations in the AR detection threshold by sweeping the inconsistency tolerance and reporting how the count of significant correlations varies.

**Why this priority**: This addresses the "Threshold justification & sensitivity" methodological requirement. Without this, the findings are vulnerable to criticism that the correlation is an artifact of a specific, arbitrary cutoff.

**Independent Test**: Can be tested by running the correlation analysis three times with slightly different AR detection thresholds (e.g., ±5.0, ±10.0 units of integrated water vapor transport) and verifying that the system produces a summary table showing the variation in significant correlation counts.

**Acceptance Scenarios**:

1. **Given** a baseline AR detection threshold, **When** the sensitivity analysis is triggered, **Then** the system re-runs the detection with thresholds adjusted by ±5.0 and ±10.0 units relative to the baseline.
2. **Given** the multiple runs, **When** the results are aggregated, **Then** the system outputs a table showing the percentage change in the number of significant correlation cells for each threshold variation relative to the baseline.
3. **Given** a specific threshold variation, **When** the analysis detects a >10% change in significant results, **Then** the system flags this specific band/season as "threshold-sensitive" in the final report.

---

### Edge Cases

- What happens if the ERA5 dataset has missing months due to reanalysis gaps? (System must exclude the specific month from the correlation calculation without crashing).
- How does the system handle the polar regions where latitudinal bands become geometrically compressed? (System must ensure equal-area weighting or exclude latitudes >80° to avoid distortion).
- What occurs if the FDR correction is so strict that no correlations remain significant? (System must report "No significant correlations found after correction" rather than failing or hiding the null result).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse ERA5 reanalysis data for water vapor transport and 500 hPa geopotential height for the period 1979–2023 (See US-1).
- **FR-002**: System MUST implement an AR detection algorithm (e.g., SWHAT) using a baseline threshold of 250 kg m⁻¹ s⁻¹ for Integrated Water Vapor Transport (See US-1).
- **FR-003**: System MUST calculate Z500 anomalies by subtracting the 1979–2023 monthly climatology from the raw Z500 data (See US-1).
- **FR-004**: System MUST compute Pearson correlation coefficients between the monthly AR frequency time-series and the Z500 anomaly time-series at *each individual grid cell* within the defined latitudinal band and season (See US-1).
- **FR-005**: System MUST apply the Benjamini-Hochberg False Discovery Rate (FDR) procedure to control the expected proportion of false discoveries across all grid cells and seasons, using an adjusted p-value threshold of < 0.05 (See US-1).
- **FR-006**: System MUST generate spatial correlation maps masking non-significant regions (adjusted p > 0.05 post-FDR) (See US-2).
- **FR-007**: System MUST perform a sensitivity analysis sweeping the AR detection threshold by ±5.0 and ±10.0 absolute units (kg m⁻¹ s⁻¹) and report the percentage change in the number of significant correlation cells relative to the baseline (See US-3).
- **FR-008**: System MUST handle missing data points in the ERA5 dataset by excluding the specific time step from the correlation calculation rather than imputing values (See US-1).
- **FR-009**: System MUST ensure all analysis steps execute within 6 hours on a standard 'ubuntu-latest' GitHub Actions runner with ≤7 GB RAM, processing the full 1979–2023 global grid, measured by wall-clock time from script start to final artifact write (See Assumptions).
- **FR-010**: System MUST validate detected significant correlations by cross-referencing spatial patterns with established teleconnection indices (PNA, NAO) to confirm physical plausibility (See US-1).

### Key Entities

- **AR_Event**: A temporal instance of an atmospheric river defined by specific IVT thresholds, with attributes for start time, end time, and geographic footprint.
- **Z500_Anomaly**: A grid-cell value representing the deviation of 500 hPa geopotential height from the long-term monthly mean.
- **Correlation_Result**: A structured record containing the correlation coefficient, p-value, adjusted p-value, latitudinal band, and season.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system must identify at least one correlation with an adjusted p-value < 0.05, OR produce a p-value distribution consistent with uniform noise if no physical drivers are present (See US-1).
- **SC-002**: The variation in the count of significant correlations across the threshold sweep (±5.0, ±10.0) is measured against the baseline threshold result to assess robustness (See US-3).
- **SC-003**: The execution time of the full analysis pipeline is measured against the CI limit on 'ubuntu-latest' (See Assumptions).
- **SC-004**: The memory usage peak during the correlation matrix computation is measured against a specified RAM constraint (See Assumptions).

## Assumptions

- The ERA5 reanalysis data on the Copernicus Climate Data Store contains complete, gap-free monthly aggregates for water vapor transport and Z500 from 1979 to 2023.
- The "250 kg m⁻¹ s⁻¹" threshold for AR detection is a defensible community standard for this global study; if the dataset lacks the resolution to support this, the threshold will be adjusted based on the sensitivity analysis.
- The analysis is observational; therefore, all reported correlations are strictly associational and do not imply causal direction without further experimental design.
- The GitHub Actions 'ubuntu-latest' runner (multiple CPU cores, ~7 GB RAM) is sufficient to process the sampled ERA5 dataset using vectorized operations (e.g., xarray, numpy) without requiring GPU acceleration or distributed computing.
- The Benjamini-Hochberg FDR procedure is the chosen method for multiple comparison control, acknowledging its suitability for spatially autocorrelated data over the conservativeness of Bonferroni.
- Latitudinal bands are defined as non-overlapping intervals of consistent width covering the globe from 90°S to 90°N, excluding the poles where grid cells degenerate.