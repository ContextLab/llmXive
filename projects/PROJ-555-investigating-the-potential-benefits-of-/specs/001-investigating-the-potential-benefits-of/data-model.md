# Data Model: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/` and processed via `code/`.

## Entity Definitions

### 1. Site
Represents a geographic location (ecotourism or control).
- **ID**: Unique string (e.g., `SITE_001`).
- **Type**: `ecotourism` | `control`.
- **Coordinates**: Latitude, Longitude (WGS84).
- **Biome**: Classification (e.g., `Tropical_Rainforest`).
- **Pair_ID**: Identifier linking the site to its matched control/ecotourism partner.
- **Initial_Severity**: NDVI drop at the start of the event (absolute value).
- **Designation_Date**: Date of ecotourism designation (YYYY-MM-DD). **Critical for Temporal Validation**.
- **Economic_Source**: Citation string for the economic data source (e.g., "Park Report 2022").

### 2. TimeSeries
A sequence of NDVI values for a specific site.
- **Site_ID**: Foreign key to `Site`.
- **Date**: ISO 8601 date.
- **NDVI**: Normalized Difference Vegetation Index (float, -1 to 1).
- **Cloud_Mask**: Boolean (True if pixel was masked as cloud).
- **Precipitation**: mm (from CHIRPS).
- **Temperature**: °C (from MODIS).

### 3. Event
Detected deforestation or regeneration event.
- **Site_ID**: Foreign key to `Site`.
- **Start_Date**: Date of deforestation onset.
- **End_Date**: Date of event end (or current date for ongoing).
- **Severity**: Absolute NDVI drop.
- **Recovery_Rate**: $k$ parameter from the HNLMM (or linear slope).
- **Model_Type**: `hnlmm` | `linear` | `hlm`.
- **R_Squared**: Goodness of fit.
- **Temporal_Flag**: `pre-designation` | `post-designation` | `unknown`.

### 4. EcotourismProfile
Economic metadata.
- **Site_ID**: Foreign key to `Site`.
- **Year**: Integer.
- **Revenue**: USD (annual).
- **Visitor_Count**: Integer (annual).
- **Source**: Citation string for the data source.

## Data Flow

1.  **Raw Ingestion**: `data/raw/landsat/*.tif` (Landsat Level-2).
2.  **Processed**: `data/processed/ndvi_timeseries.parquet` (Aggregated NDVI + Climate).
3.  **Derived**: `data/processed/events.csv` (Detected events + fitted parameters).
4.  **Final Output**: `data/processed/final_report.csv` (Model coefficients, sensitivity table).

## Constraints

- **NDVI Range**: Must be within [-1, 1]. Values outside this range are flagged as invalid.
- **Cloud Mask**: Sites with >50% cloud cover in a year are excluded from that year's analysis.
- **Revenue/Visitor**: If both are missing, the site is excluded from the economic analysis but may remain in the physical recovery analysis if other covariates are present.
- **Temporal Integrity**: Sites where `designation_date` is after `deforestation_start_date` must be flagged and handled per the Temporal Validation logic in `research.md`.
- **Metadata Completeness**: Every site in `site_list.csv` MUST have a corresponding entry in `data/ecotourism/metadata.json` with `source_name`, `retrieval_date`, and `preprocessing_steps`.
