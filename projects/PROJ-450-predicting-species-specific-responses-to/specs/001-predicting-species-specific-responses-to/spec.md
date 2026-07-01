# Feature Specification: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data  

**Feature Branch**: `450-predicting-species-niche-shifts`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: "System to quantify species‑specific realized climatic niche shifts over the past century using georeferenced museum occurrence records (GBIF) paired with WorldClim climate layers, and to relate those shifts to regional warming rates for conservation insight."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Extract and Compute Niche Centroids (Priority: P1)  

A researcher supplies a list of focal species (including taxonomic group) and requests the pipeline to (a) download all **georeferenced PRESERVED_SPECIMEN museum** occurrence records from GBIF, (b) filter records to retain those spanning **≥ 50 years** and with valid latitude/longitude, and (c) compute mean annual temperature and precipitation at each occurrence location for two **50‑year historical periods**: **1970‑2000** (early) and **1991‑2020** (modern). The system then returns a table of species‑specific climate‑space centroids for each period.  

**Note on temporal coverage**: The gap between periods reflects WorldClim v2 data availability limitations; this is documented as a known constraint for century‑scale trend inference.

**Why this priority**: This is the core data‑generation step; without reliable centroids, no downstream analysis is possible.  

**Independent Test**: Run the pipeline on a test set of three species (one plant, one bird, one insect) with known GBIF records; verify that a CSV containing two centroid rows per species is produced and that each centroid is the arithmetic mean of the extracted climate values for the correct period.  

**Acceptance Scenarios**:

1. **Given** a species list with ≥50 records spanning >50 years, **When** the pipeline is executed, **Then** a CSV row with the species name, period identifier (1970‑2000 or 1991‑2020), mean temperature (°C) and mean precipitation (mm) is created for each period **and** a log file documenting the retrieval and centroid computation steps is written.  
2. **Given** a species that fails the ≥50‑record filter, **When** the pipeline is executed, **Then** the species is omitted from the output, a warning log entry is generated, and the log file records the filtering decision.

---

### User Story 2 – Relate Niche Shifts to Regional Warming (Priority: P2)  

After centroids are available, the researcher runs an analysis that (a) calculates the **Euclidean distance in standardized climate space** between the two period centroids for each species (niche‑shift magnitude ΔN), (b) computes the regional mean temperature change (ΔT) between the same periods from an independent regional climate grid for the species' occurrence envelope, and (c) fits a linear regression of **niche‑shift magnitude (ΔN)** against **regional warming rate (ΔT)**. The system returns regression coefficients, 95% confidence interval for the slope, R², p‑value, and a scatter‑plot colored by taxonomic group. The analysis is also performed separately for each predefined geographic region (latitudinal bands of 10°) and a summary table of regional regression coefficients (with 95% CI) is produced.

**Why this priority**: Provides the primary scientific inference linking climate change to overall species‑level niche movement and assesses spatial variation across regions.  

**Independent Test**: Using the centroid CSV from Story 1, execute the analysis module; verify that the regression output includes a slope estimate, its 95% confidence interval, R² ≥ 0.01, and that a PNG scatter‑plot file of at least 1200 × 800 px is saved **and** the log records the regression steps, including per‑region summaries.

**Acceptance Scenarios**:

1. **Given** centroid data for ≥30 species, **When** the regression module runs, **Then** it outputs a table with slope, 95% CI, intercept, R², and p‑value for the global regression, saves a plot titled "Niche‑Shift Magnitude vs. Regional‑Warming" (≥ 1200 × 800 px), produces a per‑region regression summary table (including 95% CI), and appends a log entry summarising all regression results.
2. **Given** centroid data where all regional warming rates are ≤0 °C, **When** the regression runs, **Then** the global slope is reported as ≤0, the 95% CI reflects the lack of positive correlation, the plot reflects this trend, and the outcome is logged.

---

### User Story 3 – Sensitivity Analysis of Sampling Effort (Priority: P3)  

The researcher requests a robustness check that repeatedly **subsamples [deferred] of each species' occurrence records**, 10 replicates, and recomputes niche‑shift magnitudes. The system reports the mean and standard deviation of shift estimates across replicates, highlighting species with high variability (≥ 0.2 °C‑precipitation‑space units).

**Why this priority**: Ensures that conclusions are not driven by uneven sampling effort, a common issue in museum data.  

**Independent Test**: For a species with 120 records, run the subsampling routine; verify that 10 replicate shift values are produced and that the reported SD matches the sample variance, with the process documented in the log.  

**Acceptance Scenarios**:

1. **Given** a species with ≥100 records, **When** the sensitivity module executes 10 × random subsamples of [deferred] of the records, **Then** it returns a mean shift magnitude and SD, flags the species if SD ≥ 0.2, and writes a log entry describing the subsampling outcomes.
2. **Given** a species with <80 records, **When** the module is invoked, **Then** it skips subsampling, records "Insufficient data" in the log, and proceeds without error.

---

### Edge Cases  

- What happens when a species has **no georeferenced records** in GBIF?  
- How does the system handle **climate‑layer gaps** (e.g., missing WorldClim values for a location)?  
- What if **temperature and precipitation units differ** between climate layers (e.g., °C vs. K)?  

## Requirements *(mandatory)*

### Functional Requirements  

- **FR-001**: System MUST retrieve **georeferenced PRESERVED_SPECIMEN museum** occurrence records from the GBIF API for each species supplied, restricting queries to museum specimens only (See US-1).  
- **FR-002**: System MUST filter retrieved records to retain only those with collection dates spanning at least 50 years and with valid latitude/longitude (See US-1).  
- **FR-003**: System MUST extract mean annual temperature (°C) and annual precipitation (mm) from WorldClim v2 raster layers for the two periods **1970‑2000** and **1991‑2020** at each occurrence coordinate (See US-1).  
- **FR-004**: System MUST compute, for each species and period, the arithmetic mean of the extracted climate variables, producing a **climatic niche centroid** (See US-1).  
- **FR-005**: System MUST calculate Euclidean distance in **standardized climate space** between the two period centroids to quantify **niche‑shift magnitude (ΔN)**. Standardization is performed by **z‑scoring temperature and precipitation separately across ALL species occurrence points pooled (global mean = 0, SD = 1)** to ensure cross‑species comparability (See US-2).  
- **FR-006**: System MUST compute the **regional warming rate (ΔT)** as the difference in mean temperature (°C) between the two periods from an **independent regional climate grid** across the species' occurrence envelope (not from species-specific occurrence data) to avoid circularity (See US-2).  
- **FR-007**: System MUST perform a linear regression of **niche‑shift magnitude (ΔN)** against **regional warming rate (ΔT)** and output slope, 95% confidence interval for the slope, intercept, R², and two‑tailed p‑value (See US-2).
- **FR-008**: System MUST generate a scatter‑plot of **niche‑shift magnitude vs. regional warming rate**, with points colored by taxonomic group, and save it as a **high‑resolution PNG of at least 1200 × 800 pixels** (See US-2).  
- **FR-009**: System MUST conduct a sensitivity analysis by random subsampling **50% of records**, 10 replicates, and report mean shift, standard deviation, and flag species with SD ≥ 0.2 climate‑space units (See US-3).
- **FR-010**: System MUST produce a comprehensive log file for each pipeline execution, documenting data retrieval counts, filtering decisions, centroid calculations, regression steps (including per‑region regressions), sensitivity analysis runs, and any warnings or errors encountered, as mandated by User Stories 1‑3 (See US-1, US-2, US-3).  
- **FR-011**: System MUST assign each species to a geographic region (e.g., latitudinal band) and perform the regression of niche‑shift magnitude vs. regional warming separately for each region, outputting a summary table of regression coefficients (including 95% CI) per region (See US-2).
- **FR-012**: System MUST perform a power analysis to justify the regression sample size (minimum 30 species required for adequate statistical power) and report margin‑of‑error for the slope estimate to address statistical power concerns (See US-2).

### Key Entities  

- **Species**: Represents a taxonomic entity; key attributes – scientific name, taxonomic group, GBIF taxonKey.  
- **OccurrenceRecord**: Represents a single museum specimen/observation; attributes – latitude, longitude, collectionDate, coordinateUncertainty.  
- **ClimateCentroid**: Represents mean temperature and precipitation for a species in a given period; attributes – periodLabel, meanTemp (°C), meanPrec (mm).  
- **NicheShiftResult**: Contains Euclidean distance, regional warming rate, regression statistics, and sensitivity metrics for a species.  

## Success Criteria *(mandatory)*

### Measurable Outcomes  

- **SC-001**: ≥ 90% of supplied species with ≥50 valid records produce a complete ClimateCentroid record for both periods (source: pipeline log) (See US-1).  
- **SC-002**: Regression analysis returns a slope estimate with a **95% confidence interval** that is computable for ≥ 80% of species sets (source: regression output) (See US-2).
- **SC-003**: Sensitivity analysis reports a standard deviation ≤ 0.2 climate‑space units for ≥ 70% of species, indicating robust shift estimates (source: sensitivity summary) (See US-3).  
- **SC-004**: All generated PNG visualizations are ≥ 1200 × 800 pixels and viewable without error in standard image viewers (source: file system check) (See US-2).  
- **SC-005**: Log file contains ≤ 5% warning entries relative to total processed records, demonstrating stable data quality (source: log parsing) (See US-1, US-2, US-3).  
- **SC-006**: For each geographic region, the regression of niche‑shift magnitude vs. regional warming returns a slope estimate with a **95% confidence interval**; ≥ 80% of regions produce computable results (source: per‑region regression summary) (See US-2).
- **SC-007**: Power analysis report includes margin‑of‑error calculation for slope estimate with target ≤ 0.15 for n ≥ 30 species (source: FR-012 output) (See US-2).

## Assumptions  

- Researchers have **API access** to GBIF and permission to download occurrence records for the selected taxa.  
- WorldClim v2 raster layers (mean annual temperature & precipitation) for the periods **1970‑2000** (historical reconstruction) and **1991‑2020** (modern) are **pre‑downloaded** and stored locally in a format readable by the `raster` R package.  
- Climate variables are recorded in **standard units** (temperature in °C, precipitation in mm); no unit conversion is required.  
- Species selected for analysis each have **≥50 occurrence records** spanning at least 50 years; species failing this criterion are excluded automatically.  
- Euclidean distance is calculated in **standardized climate space** (z‑scaled temperature and precipitation) as defined in FR‑005, using **global** z‑scoring across all species.  
- The R environment includes the `rgbif`, `raster`, `sf`, and `ggplot2` packages at versions compatible with the code base.  
- The GBIF query is limited to **museum PRESERVED_SPECIMEN** records only, consistent with the original idea's focus on museum collection data.  
- The mid-20th century temporal gap between WorldClim v2 periods is a known data limitation; century‑scale trend inference relies on extrapolation from the two available periods.