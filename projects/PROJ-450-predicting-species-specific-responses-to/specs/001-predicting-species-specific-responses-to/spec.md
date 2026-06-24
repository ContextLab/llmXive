# Feature Specification: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data  

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: “System to quantify species‑specific realized climatic niche shifts over the past century using georeferenced museum occurrence records (GBIF) paired with WorldClim climate layers, and to relate those shifts to regional warming rates for conservation insight.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Extract and Compute Niche Centroids (Priority: P1)  

A researcher supplies a list of focal species (including taxonomic group) and requests the pipeline to (a) download all **georeferenced PRESERVED_SPECIMEN museum** occurrence records from GBIF, (b) filter records to retain those spanning **≥ 50 years** and with valid latitude/longitude, and (c) compute mean annual temperature and precipitation at each occurrence location for two **50‑year historical periods**: **1900‑1950** (early) and **1970‑2020** (modern). The system then returns a table of species‑specific climate‑space centroids for each period.  

**Why this priority**: This is the core data‑generation step; without reliable centroids, no downstream analysis is possible.  

**Independent Test**: Run the pipeline on a test set of three species (one plant, one bird, one insect) with known GBIF records; verify that a CSV containing two centroid rows per species is produced and that each centroid is the arithmetic mean of the extracted climate values for the correct period.  

**Acceptance Scenarios**:

1. **Given** a species list with ≥50 records spanning >50 years, **When** the pipeline is executed, **Then** a CSV row with the species name, period identifier (1900‑1950 or 1970‑2020), mean temperature (°C) and mean precipitation (mm) is created for each period **and** a log file documenting the retrieval and centroid computation steps is written.  
2. **Given** a species that fails the ≥50‑record filter, **When** the pipeline is executed, **Then** the species is omitted from the output, a warning log entry is generated, and the log file records the filtering decision.

---

### User Story 2 – Relate Niche Shifts to Regional Warming (Priority: P2)  

After centroids are available, the researcher runs an analysis that (a) calculates the **Euclidean distance in standardized climate space** between the two period centroids for each species (niche‑shift magnitude ΔN), (b) computes the regional mean temperature change (ΔT) between the same periods for the species’ occurrence envelope, and (c) fits a linear regression of **niche‑shift magnitude (ΔN)** against **regional warming rate (ΔT)**. The system returns regression coefficients, [deferred] confidence interval for the slope, R², p‑value, and a scatter‑plot colored by taxonomic group. The analysis is also performed separately for each predefined geographic region (latitudinal bands of 10°) and a summary table of regional regression coefficients (with [deferred] CI) is produced.

**Why this priority**: Provides the primary scientific inference linking climate change to overall species‑level niche movement and assesses spatial variation across regions.  

**Independent Test**: Using the centroid CSV from Story 1, execute the analysis module; verify that the regression output includes a slope estimate, its [deferred] confidence interval, R² ≥ 0, and that a PNG scatter‑plot file of at least 1200 × 800 px is saved **and** the log records the regression steps, including per‑region summaries.

**Acceptance Scenarios**:

1. **Given** centroid data for ≥10 species, **When** the regression module runs, **Then** it outputs a table with slope, [deferred] CI, intercept, R², and p‑value for the global regression, saves a plot titled “Niche‑Shift Magnitude vs. Regional‑Warming” (≥ 1200 × 800 px), produces a per‑region regression summary table (including [deferred] CI), and appends a log entry summarising all regression results.
2. **Given** centroid data where all regional warming rates are ≤0 °C, **When** the regression runs, **Then** the global slope is reported as ≤0, the [deferred] CI reflects the lack of positive correlation, the plot reflects this trend, and the outcome is logged.

---

### User Story 3 – Sensitivity Analysis of Sampling Effort (Priority: P3)  

The researcher requests a robustness check that repeatedly **subsamples [deferred] of each species’ occurrence records**, 10 replicates, and recomputes niche‑shift magnitudes. The system reports the mean and standard deviation of shift estimates across replicates, highlighting species with high variability (≥ 0.2 °C‑precipitation‑space units).

**Why this priority**: Ensures that conclusions are not driven by uneven sampling effort, a common issue in museum data.  

**Independent Test**: For a species with 120 records, run the subsampling routine; verify that 10 replicate shift values are produced and that the reported SD matches the sample variance, with the process documented in the log.  

**Acceptance Scenarios**:

1. **Given** a species with ≥100 records, **When** the sensitivity module executes 10 × random subsamples of [deferred] of the records, **Then** it returns a mean shift magnitude and SD, flags the species if SD ≥ 0.2, and writes a log entry describing the subsampling outcomes.
2. **Given** a species with <80 records, **When** the module is invoked, **Then** it skips subsampling, records “Insufficient data” in the log, and proceeds without error.

---

### Edge Cases  

- What happens when a species has **no georeferenced records** in GBIF?  
- How does the system handle **climate‑layer gaps** (e.g., missing WorldClim values for a location)?  
- What if **temperature and precipitation units differ** between climate layers (e.g., °C vs. K)?  

## Requirements *(mandatory)*

### Functional Requirements  

- **FR-001**: System MUST retrieve **georeferenced PRESERVED_SPECIMEN museum** occurrence records from the GBIF API for each species supplied.  
- **FR-002**: System MUST filter retrieved records to retain only those with collection dates spanning at least 50 years and with valid latitude/longitude.  
- **FR-003**: System MUST extract mean annual temperature (°C) and annual precipitation (mm) from WorldClim raster layers for the two periods **1900‑1950** and **1970‑2020** at each occurrence coordinate.  
- **FR-004**: System MUST compute, for each species and period, the arithmetic mean of the extracted climate variables, producing a **climatic niche centroid**.  
- **FR-005**: System MUST calculate Euclidean distance in **standardized climate space** between the two period centroids to quantify **niche‑shift magnitude (ΔN)**. Standardization is performed by **z‑scoring temperature and precipitation separately across all occurrence points of a species pooled over both periods (mean = 0, SD = 1)**.  
- **FR-006**: System MUST compute the **regional warming rate (ΔT)** as the difference in mean temperature (°C) between the two periods across all occurrence points of a species (independent of the centroid calculation).  
- **FR-007**: System MUST perform a linear regression of **niche‑shift magnitude (ΔN)** against **regional warming rate (ΔT)** and output slope, [deferred] confidence interval for the slope, intercept, R², and two‑tailed p‑value.
- **FR-008**: System MUST generate a scatter‑plot of **niche‑shift magnitude vs. regional warming rate**, with points colored by taxonomic group, and save it as a **high‑resolution PNG of at least 1200 × 800 pixels**.  
- **FR-009**: System MUST conduct a sensitivity analysis by random subsampling **[deferred] of records**, 10 replicates, and report mean shift, standard deviation, and flag species with SD ≥ 0.2 climate‑space units.
- **FR-010**: System MUST produce a comprehensive log file for each pipeline execution, documenting data retrieval counts, filtering decisions, centroid calculations, regression steps (including per‑region regressions), sensitivity analysis runs, and any warnings or errors encountered, as mandated by User Stories 1‑3.  
- **FR-011**: System MUST assign each species to a geographic region (e.g., latitudinal band of 10°) and perform the regression of niche‑shift magnitude vs. regional warming separately for each region, outputting a summary table of regression coefficients (including [deferred] CI) per region (required by User Story 2).
- **FR-012**: System MUST compute **precipitation shift magnitude** (ΔP) as the absolute difference in mean precipitation between the two periods for each species, to be reported as a secondary metric.

### Key Entities  

- **Species**: Represents a taxonomic entity; key attributes – scientific name, taxonomic group, GBIF taxonKey.  
- **OccurrenceRecord**: Represents a single museum specimen/observation; attributes – latitude, longitude, collectionDate, coordinateUncertainty.  
- **ClimateCentroid**: Represents mean temperature and precipitation for a species in a given period; attributes – periodLabel, meanTemp (°C), meanPrec (mm).  
- **NicheShiftResult**: Contains Euclidean distance, regional warming rate, precipitation shift magnitude, regression statistics, and sensitivity metrics for a species.  

## Success Criteria *(mandatory)*

### Measurable Outcomes  

- **SC-001**: ≥ 90 % of supplied species with ≥50 valid records produce a complete ClimateCentroid record for both periods (source: pipeline log).  
- **SC-002**: Regression analysis returns a slope estimate with a **[deferred] confidence interval** that is computable for ≥ 80 % of species sets (source: regression output).
- **SC-003**: Sensitivity analysis reports a standard deviation ≤ 0.2 climate‑space units for ≥ 70 % of species, indicating robust shift estimates (source: sensitivity summary).  
- **SC-004**: All generated PNG visualizations are ≥ 1200 × 800 pixels and viewable without error in standard image viewers (source: file system check).  
- **SC-005**: Log file contains ≤ 5 % warning entries relative to total processed records, demonstrating stable data quality (source: log parsing).  
- **SC-006**: For each geographic region, the regression of niche‑shift magnitude vs. regional warming returns a slope estimate with a **[deferred] confidence interval**; ≥ 80 % of regions produce computable results (source: per‑region regression summary).

## Assumptions  

- Researchers have **API access** to GBIF and permission to download occurrence records for the selected taxa.  
- WorldClim v2 raster layers (mean annual temperature & precipitation) for the periods **1900‑1950** (historical reconstruction) and **1970‑2020** (modern) are **pre‑downloaded** and stored locally in a format readable by the `raster` R package.  
- Climate variables are recorded in **standard units** (temperature in °C, precipitation in mm); no unit conversion is required.  
- Species selected for analysis each have **≥50 occurrence records** spanning at least 50 years; species failing this criterion are excluded automatically.  
- Euclidean distance is calculated in **standardized climate space** (z‑scaled temperature and precipitation) as defined in FR‑005.  
- The R environment includes the `rgbif`, `raster`, `sf`, and `ggplot2` packages at versions compatible with the code base.  
- The GBIF query is limited to **museum PRESERVED_SPECIMEN** records to stay faithful to the original idea.  

---



# Panel concerns to address (R1 output)

- [concern testability-68aaae8c] severity=requirement reviewer=testability location=spec.md:FR-009
  FR-009 contains a placeholder '[deferred] of records' for the subsampling proportion, leaving the functional behavior undefined and thus not verifiable by a test.
- [concern C-001] severity=requirement reviewer=scope location=FR-007
  The regression defined in FR-007 uses precipitation shift magnitude (ΔP) as the response variable, whereas the original idea’s research question focuses on overall realized niche shifts (e.g., Euclidean distance between climate‑space centroids). This changes the scientific focus from total niche movement to a single climate dimension, constituting a drift from the intended research question.
- [concern C-002] severity=requirement reviewer=scope location=FR-001 / Assumptions
  The idea explicitly emphasizes *museum collection* data as the primary source, yet FR-001 states the system retrieves records from the GBIF API without restricting to museum specimens. GBIF aggregates many data types (citizen science, observation platforms). The specification should either limit queries to museum records or justify inclusion of non‑museum data to stay faithful to the idea.
- [concern C-003] severity=requirement reviewer=scope location=User Story 1 – Period definitions
  The research question aims to assess niche shifts over the *past century*. The spec, however, only compares two recent 30‑year windows (1970‑2000 and 1991‑2020), which does not span a full century and may miss longer‑term trends. Either expand the temporal coverage or clarify that the chosen windows are a proxy for the century‑scale analysis.

# Remaining `[NEEDS CLARIFICATION]` markers

(no `[NEEDS CLARIFICATION]` markers remain)

# Recent reviewer / personality comments

(no recent comments)
