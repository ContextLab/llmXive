# Feature Specification: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

**Feature Branch**: `001-ecotourism-regeneration`  
**Created**: 2026-06-03  
**Status**: Draft  
**Input**: User description: "Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system must successfully ingest, clean, and align Landsat satellite imagery time series with ecotourism site metadata for the defined study period. This is the foundational step; without valid, aligned data, no analysis can proceed.

**Why this priority**: This is the data pipeline core. If the system cannot retrieve or process the raw satellite and economic data, the entire research question remains unanswerable. It is the prerequisite for all subsequent modeling.

**Independent Test**: Can be fully tested by verifying that the system outputs a consolidated CSV/Parquet file containing a representative set of paired sites with valid NDVI time series and corresponding tourism metadata, and that the data volume fits within the 7GB RAM limit without crashing, even when processing raw data in chunks.

**Acceptance Scenarios**:

1. **Given** a list of 30 site coordinates (15 ecotourism, 15 control) and API credentials, **When** the data ingestion script runs with chunked processing enabled, **Then** it successfully downloads Level-2 surface reflectance data for Landsat 5/8/9 and masks clouds using USGS land cover classifications, producing a clean time-series dataset without exceeding 7GB RAM.
2. **Given** a raw satellite image with partial cloud cover, **When** the preprocessing module applies the cloud mask, **Then** the resulting NDVI calculation excludes masked pixels, and the data integrity check confirms <5% data loss per site.
3. **Given** the requirement to match biomes, **When** the pairing logic executes, **Then** every ecotourism site is paired with a control site within the same biome classification and similar initial deforestation severity (±10% NDVI drop).

### User Story 2 - Deforestation Detection and Recovery Trajectory Modeling (Priority: P2)

The system must automatically detect deforestation events (absolute NDVI drop ≥0.30 sustained over 2 years) and calculate the recovery trajectory for the subsequent 5-10 years using a non-linear asymptotic model. This directly addresses the core variable of interest: regeneration rate.

**Why this priority**: This transforms raw time-series data into the specific outcome variable (regeneration rate) required to answer the research question. It is the primary analytical transformation step.

**Independent Test**: Can be fully tested by running the detection algorithm on a synthetic dataset with known deforestation events and recovery curves, verifying that the system correctly identifies the break-point and fits the asymptotic model within a defined tolerance (e.g., R² ≥ 0.95).

**Acceptance Scenarios**:

1. **Given** a site's NDVI time series showing a sharp decline, **When** the break-point detection algorithm runs, **Then** it identifies the start of the deforestation event only if the NDVI drop is ≥0.30 (absolute) and sustained for at least 2 years.
2. **Given** a detected deforestation event, **When** the recovery analysis runs, **Then** it fits a non-linear asymptotic model (e.g., logistic or Gompertz) to the recovery phase for the next 5-10 years, or alternatively calculates a linear slope for the initial 5-year window if data is insufficient for asymptotic fitting.
3. **Given** a site with no clear deforestation event (NDVI drop <0.30), **When** the detection runs, **Then** the site is flagged and excluded from the regeneration analysis cohort.

### User Story 3 - Statistical Inference and Sensitivity Analysis (Priority: P3)

The system must fit a linear mixed-effects model to test the association between ecotourism status and regeneration rate, and conduct a sensitivity analysis sweeping the ecotourism definition threshold (revenue/visitor count) to ensure robustness. This provides the final answer and validates the methodological soundness.

**Why this priority**: This delivers the research conclusion. The sensitivity analysis is critical for methodological defensibility, ensuring results aren't artifacts of arbitrary threshold choices or proxy variable selection.

**Independent Test**: Can be fully tested by running the model on the processed dataset and verifying that the output includes the coefficient for ecotourism status, p-values, and a sensitivity report showing how the effect size changes across the defined threshold sweep and proxy variable selection.

**Acceptance Scenarios**:

1. **Given** the paired dataset with regeneration rates and covariates, **When** the linear mixed-effects model runs with 'pair' as a random effect, **Then** it outputs the fixed effect estimate for "ecotourism status" with a 95% confidence interval, controlling for climate and initial severity.
2. **Given** the sensitivity analysis requirement, **When** the system sweeps the "ecotourism site" definition (revenue thresholds at $10k, $50k, $100k) and the proxy variable (revenue vs. visitor count), **Then** it generates a table showing the variation in the headline association rate (effect size) across these thresholds and variables.
3. **Given** the need for multiplicity correction, **When** multiple hypotheses are tested (e.g., different model specifications), **Then** the system applies a family-wise error correction (e.g., Bonferroni or Holm) and reports the adjusted p-values.

### Edge Cases

- **What happens when** a site has missing data for >50% of the time series due to persistent cloud cover or sensor failure?
  - *Handling*: The system must exclude the site from the analysis and log a warning, rather than attempting to impute large gaps which could bias the slope.
- **How does system handle** a site where deforestation is detected, but the recovery period is <5 years (insufficient data for slope calculation)?
  - *Handling*: The site is flagged as "incomplete recovery" and excluded from the primary slope analysis, but included in a secondary descriptive count if applicable.
- **What happens when** the ecotourism revenue data is missing for a specific year in the time series?
  - *Handling*: The system uses linear interpolation for single-year gaps but excludes the site if gaps exceed a threshold of consecutive years. If revenue data is missing entirely for a site, the system substitutes the 'visitor count' metric as a proxy, as defined in FR-006.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and process Landsat surface reflectance data for a set of paired sites (ecotourism and control) covering 2000-2023 using a chunked streaming strategy to ensure peak memory usage remains within feasible limits. (See US-1)
- **FR-002**: System MUST identify deforestation events defined as an absolute NDVI drop ≥0.30 sustained for ≥2 years, and calculate the recovery trajectory using a non-linear asymptotic model (or linear approximation for the first 5 years). (See US-2)
- **FR-003**: System MUST fit a linear mixed-effects model with 'pair' as a random effect to test the association between ecotourism status and regeneration rate, controlling for precipitation (CHIRPS), temperature (MODIS), and initial deforestation severity. (See US-3)
- **FR-004**: System MUST perform a sensitivity analysis by sweeping the "ecotourism site" definition threshold over a concrete set of annual revenue values and report the variation in the primary effect estimate. (See US-3)
- **FR-005**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Holm) if more than one hypothesis test is conducted, and report adjusted p-values. (See US-3)
- **FR-006**: System MUST output a final report containing the regression coefficients, confidence intervals, sensitivity analysis table (including proxy variable comparison if revenue data is missing), and a binary "pass/fail" flag for data quality checks. (See US-1, US-3)
- **FR-007**: If 'annual revenue' data is unavailable for a site, the system MUST use 'annual visitor count' as a proxy variable and include a sensitivity comparison between revenue-based and visitor-count-based models. (See US-3)

### Key Entities

- **Site**: A geographic polygon representing a protected area, characterized by coordinates, biome type, and protection status.
- **TimeSeries**: A sequence of NDVI values for a specific site, indexed by date, with associated cloud mask metadata.
- **Event**: A detected deforestation or regeneration event, characterized by start date, end date, severity (absolute NDVI drop), and recovery trajectory parameters.
- **EcotourismProfile**: Economic metadata for a site, including annual visitor counts, revenue, and reinvestment rates.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The data pipeline successfully processes [deferred] of valid sites (up to 30 target sites, excluding only those with >50% data loss) within the 6-hour GitHub Actions time limit. (See FR-001)
- **SC-002**: The deforestation detection algorithm correctly identifies break-points in synthetic test data with ≥95% accuracy (precision/recall) compared to ground-truth labels. (See FR-002)
- **SC-003**: The linear mixed-effects model converges successfully for ≥90% of the valid site pairs, producing stable coefficient estimates (standard error < 10% of coefficient magnitude). (See FR-003)
- **SC-004**: The sensitivity analysis demonstrates that the primary effect estimate (ecotourism impact on regeneration) remains statistically significant (p < 0.05) or consistently non-significant across the defined threshold sweep {10000, 50000, 100000} USD and proxy variable selection. (See FR-004)
- **SC-005**: The total memory usage of the analysis pipeline remains ≤7GB during peak processing. (See FR-001)

## Assumptions

- **Assumption about data availability**: Publicly available conservation organization reports and tourism authority databases contain sufficient annual visitor count data for the selected ecotourism sites. Annual revenue data may be missing; in such cases, 'visitor count' is assumed to be a valid proxy for economic activity.
- **Assumption about climate data**: CHIRPS precipitation and MODIS temperature data are available at the required spatial and temporal resolution for all study sites without gaps that would invalidate the mixed-effects model.
- **Assumption about compute constraints**: The Landsat data volume for a set of sites is processed in chunks, ensuring that the raw data is never fully loaded into RAM simultaneously, keeping peak usage within available memory constraints.
- **Assumption about methodology**: The study design is observational; therefore, all findings regarding ecotourism and regeneration will be framed as associational, not causal, consistent with the lack of random assignment.
- **Assumption about threshold justification**: The threshold for "deforestation" (absolute NDVI drop ≥0.30) is based on established remote sensing literature for detecting significant land cover change. The sensitivity analysis will sweep annual revenue thresholds to confirm robustness.
- **Assumption about model validity**: The linear mixed-effects model with 'pair' as a random effect is appropriate for the data structure, and the random effects adequately account for spatial autocorrelation within the paired sites.