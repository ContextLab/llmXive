# Feature Specification: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data  

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: “System to quantify species‑specific realized climatic niche shifts over the past century using georeferenced museum occurrence records (GBIF) paired with WorldClim climate layers, and to relate those shifts to regional warming rates for conservation insight.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Extract and Compute Niche Centroids (Priority: P1)  

A researcher supplies a list of focal species (including taxonomic group) and requests the pipeline to (a) download all georeferenced museum occurrence records from GBIF, (b) filter records to retain those spanning ≥50 years, and (c) compute mean annual temperature and precipitation at each occurrence location for two historical climate periods (1970‑2000 and 1991‑2020). The system then returns a table of species‑specific climate‑space centroids for each period.  

**Why this priority**: This is the core data‑generation step; without reliable centroids, no downstream analysis is possible.  

**Independent Test**: Run the pipeline on a test set of three species (one plant, one bird, one insect) with known GBIF records; verify that a CSV containing two centroid rows per species is produced and that each centroid is the arithmetic mean of the extracted climate values.  

**Acceptance Scenarios**:

1. **Given** a species list with ≥50 records spanning >50 years, **When** the pipeline is executed, **Then** a CSV row with the species name, period identifier, mean temperature (°C) and mean precipitation (mm) is created for each period.  
2. **Given** a species that fails the ≥50‑record filter, **When** the pipeline is executed, **Then** the species is omitted from the output and a warning log entry is generated.

---

### User Story 2 – Relate Niche Shifts to Regional Warming (Priority: P2)  

After centroids are available, the researcher runs an analysis that (a) calculates the Euclidean distance between the two period centroids for each species (niche shift magnitude), (b) computes the regional mean temperature change between the same periods for the species’ occurrence envelope, and (c) fits a linear regression of niche shift magnitude against regional warming rate. The system returns regression coefficients, R², p‑value, and a scatter‑plot colored by taxonomic group.  

**Why this priority**: Provides the primary scientific inference linking climate change to species responses.  

**Independent Test**: Using the centroid CSV from Story 1, execute the analysis module; verify that the regression output includes a slope estimate, R² ≥ 0, and that a PNG scatter‑plot file is saved.  

**Acceptance Scenarios**:

1. **Given** centroid data for ≥10 species, **When** the regression module runs, **Then** it outputs a table with slope, intercept, R², and p‑value, and saves a plot titled “Niche‑Shift vs. Regional‑Warming”.  
2. **Given** centroid data where all regional warming rates are ≤0 °C, **When** the regression runs, **Then** the slope is reported as ≤0 and the plot reflects the lack of positive correlation.

---

### User Story 3 – Sensitivity Analysis of Sampling Effort (Priority: P3)  

The researcher requests a robustness check that repeatedly subsamples each species’ occurrence records (e.g., [deferred] of records, 10 replicates) and recomputes niche shift magnitudes. The system reports the mean and standard deviation of shift estimates across replicates, highlighting species with high variability (≥ 0.2 °C‑precipitation‑space units).

**Why this priority**: Ensures that conclusions are not driven by uneven sampling effort, a common issue in museum data.  

**Independent Test**: For a species with 120 records, run the subsampling routine; verify that 10 replicate shift values are produced and that the reported SD matches the sample variance.  

**Acceptance Scenarios**:

1. **Given** a species with ≥100 records, **When** the sensitivity module executes 10 × [deferred] random subsamples, **Then** it returns a mean shift magnitude and SD, and flags the species if SD ≥ 0.2.
2. **Given** a species with <80 records, **When** the module is invoked, **Then** it skips subsampling, records “Insufficient data” in the log, and proceeds without error.

---

### Edge Cases  

- What happens when a species has **no georeferenced records** in GBIF?  
- How does the system handle **climate‑layer gaps** (e.g., missing WorldClim values for a location)?  
- What if **temperature and precipitation units differ** between climate layers (e.g., °C vs. K)?  

## Requirements *(mandatory)*

### Functional Requirements  

- **FR-001**: System MUST retrieve georeferenced occurrence records from the GBIF API for each species supplied.  
- **FR-002**: System MUST filter retrieved records to retain only those with collection dates spanning at least 50 years and with valid latitude/longitude.  
- **FR-003**: System MUST extract mean annual temperature (°C) and annual precipitation (mm) from WorldClim v2 raster layers for the two periods 1970‑2000 and 1991‑2020 at each occurrence coordinate.  
- **FR-004**: System MUST compute, for each species and period, the arithmetic mean of the extracted climate variables, producing a **climatic niche centroid**.  
- **FR-005**: System MUST calculate Euclidean distance in standardized climate space between the two period centroids to quantify **niche shift magnitude**.  
- **FR-006**: System MUST compute the regional warming rate as the difference in mean temperature (°C) between the two periods across all occurrence points of a species.  
- **FR-007**: System MUST perform a linear regression of niche shift magnitude (response) against regional warming rate (predictor) and output slope, intercept, R², and two‑tailed p‑value.  
- **FR-008**: System MUST generate a scatter‑plot of niche shift magnitude vs. regional warming rate, with points colored by taxonomic group, and save it as a high‑resolution PNG.  
- **FR-009**: System MUST conduct a sensitivity analysis by random subsampling (default [deferred] of records, 10 replicates) and report mean shift, standard deviation, and flag species with SD ≥ 0.2 climate‑space units.
- **FR-010**: System MUST produce a comprehensive log file documenting data retrieval counts, filtering decisions, and any warnings or errors encountered.  

### Key Entities  

- **Species**: Represents a taxonomic entity; key attributes – scientific name, taxonomic group, GBIF taxonKey.  
- **OccurrenceRecord**: Represents a single museum specimen/observation; attributes – latitude, longitude, collectionDate, coordinateUncertainty.  
- **ClimateCentroid**: Represents mean temperature and precipitation for a species in a given period; attributes – periodLabel, meanTemp (°C), meanPrec (mm).  
- **NicheShiftResult**: Contains Euclidean distance, regional warming rate, regression statistics, and sensitivity metrics for a species.  

## Success Criteria *(mandatory)*

### Measurable Outcomes  

- **SC-001**: ≥ 90 % of supplied species with ≥50 valid records produce a complete ClimateCentroid record for both periods (source: pipeline log).  
- **SC-002**: Regression analysis returns a slope estimate with a [deferred] confidence interval that is computable for ≥ 80 % of species sets (source: regression output).
- **SC-003**: Sensitivity analysis reports a standard deviation ≤ 0.2 climate‑space units for ≥ 70 % of species, indicating robust shift estimates (source: sensitivity summary).  
- **SC-004**: All generated PNG visualizations are ≥ 1200 × 800 pixels and viewable without error in standard image viewers (source: file system check).  
- **SC-005**: Log file contains ≤ 5 % warning entries relative to total processed records, demonstrating stable data quality (source: log parsing).  

## Assumptions  

- Researchers have **API access** to GBIF and permission to download occurrence records for the selected taxa.  
- WorldClim v2 raster layers (mean annual temperature & precipitation) are **pre‑downloaded** and stored locally in a format readable by the `raster` R package.  
- Climate variables are **already standardized** (temperature in °C, precipitation in mm); no unit conversion is required.  
- Species selected for analysis each have **≥50 occurrence records** spanning at least 50 years; species failing this criterion are excluded automatically.  
- Euclidean distance is calculated in **unstandardized climate space**; if future extensions require scaling, the current implementation assumes comparable numeric ranges.  
- The R environment includes the `rgbif`, `raster`, `sf`, and `ggplot2` packages at versions compatible with the code base.  

---
