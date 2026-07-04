# Data Model: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

## 1. Overview

This document defines the data structures, schemas, and relationships used in the project. All data flows from the NASA Exoplanet Archive (raw) through `petitRADTRANS` (retrieval) to the statistical analysis module (processed).

## 2. Data Entities

### 2.1 Raw Spectrum
A transmission spectrum file downloaded from the NASA Exoplanet Archive.
*   **Format**: ASCII table or FITS (converted to CSV for processing).
*   **Contents**: Wavelength ($\mu m$), Flux (relative to star), Flux Uncertainty.

### 2.2 Planet Metadata
A record containing planetary and stellar parameters.
*   **Source**: NASA Exoplanet Archive API.
*   **Key Fields**: `planet_name`, `host_name`, `equilibrium_temp`, `host_metallicity`, `planet_mass`, `planet_category`.

### 2.3 Retrieval Result
The output of the `petitRADTRANS` run for a single spectrum.
*   **Key Fields**: `water_abundance_log10`, `uncertainty`, `is_upper_limit`, `detection_limit`, `retrieval_status`.

### 2.4 Analysis Dataset
The final merged table used for statistical modeling.
*   **Key Fields**: `planet_name`, `water_abundance`, `uncertainty`, `is_censored`, `equilibrium_temp`, `planet_mass`, `host_metallicity`, `category`, `detection_limit`.

## 3. Schema Definitions

### 3.1 Metadata Schema
Defines the structure of the `data/processed/metadata.csv` file.

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `planet_name` | String | Unique identifier (e.g., "HD 209458 b") | Non-null, Unique |
| `host_name` | String | Host star name | Non-null |
| `equilibrium_temp` | Float | Equilibrium temperature in Kelvin | > 0 |
| `host_metallicity` | Float | [Fe/H] value | Nullable (for regression exclusion) |
| `planet_mass` | Float | Mass in Jupiter masses | > 0 |
| `planet_category` | Enum | "Hot Jupiter" or "Super Earth" | Valid enum |
| `data_source` | String | "NASA Exoplanet Archive" | Constant |

### 3.2 Retrieval Output Schema
Defines the structure of `data/processed/retrieval_results.csv`.

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `planet_name` | String | Foreign key to metadata | Non-null |
| `water_abundance_log10` | Float | Log10 water mixing ratio | Nullable (if upper limit) |
| `uncertainty` | Float | 1-sigma uncertainty | > 0 |
| `is_upper_limit` | Boolean | True if result is an upper limit | True/False |
| `detection_limit` | Float | The 3-sigma noise floor value (censoring point) | Non-null (used as threshold) |
| `retrieval_status` | Enum | "Success", "Upper Limit", "Failed" | Valid enum |

### 3.3 Analysis Dataset Schema
The final joined table for statistical analysis.

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `planet_name` | String | Unique ID | Non-null |
| `water_abundance` | Float | Value or limit | Nullable |
| `is_censored` | Boolean | True if upper limit | True/False |
| `equilibrium_temp` | Float | Predictor 1 | Non-null |
| `planet_mass` | Float | Predictor 2 | Nullable |
| `host_metallicity` | Float | Predictor 3 | Nullable |
| `category` | Enum | Grouping variable | Valid enum |
| `detection_limit` | Float | The 3-sigma noise floor value (per-observation) | Non-null (for Tobit) |

## 4. Data Flow Diagram

1.  **Download**: `code/download.py` -> `data/raw/spectra/` + `data/raw/metadata.csv`
2.  **Retrieval**: `code/retrieval.py` reads `data/raw/`, runs `petitRADTRANS`, writes `data/processed/retrieval_results.csv`.
3.  **Merge**: `code/analysis.py` merges metadata and retrieval results, filters for validity, writes `data/processed/analysis_dataset.csv`.
4.  **Analysis**: `code/analysis.py` reads `analysis_dataset.csv`, performs stats, writes `results/statistics.json` and `results/plots/`.

## 5. Validation Rules

*   **Temperature**: Must be > 0 K.
*   **Metallicity**: Must be within [-1.0, +1.0] (physical bounds, with tolerance).
*   **Water Abundance**: Must be < 0 (log10 mixing ratio is negative).
*   **Censoring**: If `is_upper_limit` is True, `water_abundance` must be None or equal to `detection_limit`.
*   **Detection Limit**: Must be derived from the 3-sigma noise floor of the raw spectrum, not the retrieval posterior.
*   **Collinearity**: If VIF > 5 for predictors, the system must flag the model for Ridge fallback.