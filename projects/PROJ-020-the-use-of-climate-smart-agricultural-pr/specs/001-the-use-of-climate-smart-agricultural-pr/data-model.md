# Data Model: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

## Overview

This document defines the data structures, schemas, and transformations for the project. It ensures that all data flows from raw sources to final analysis-ready formats are documented and reproducible.

## Entity Definitions

### 1. Raw Data Entities

#### `RawLSMS`
-   **Source**: LSMS (Living Standards Measurement Study).
-   **Format**: STATA/CSV.
-   **Fields**: `household_id`, `country`, `year`, `hdds_score`, `conservation_tillage`, `crop_diversification`, `irrigation_efficiency`, `digital_access`, `finance_access`, `latitude`, `longitude`, `cluster_id`.
-   **Constraints**: `country` in [KEN, IND, VNM].

#### `RawNASA`
-   **Source**: NASA POWER (Verified URLs).
-   **Format**: CSV/Parquet.
-   **Fields**: `latitude`, `longitude`, `year`, `month`, `tavg`, `prcp`.
-   **Constraints**: Coordinates must match survey coordinates within 50km.

### 2. Processed Data Entities

#### `AnalysisDataset`
-   **Source**: Merged `RawLSMS`, `RawNASA`.
-   **Format**: Parquet.
-   **Fields**:
    -   `household_id`: String (Unique ID).
    -   `country`: String (ISO 3 code).
    -   `year`: Integer.
    -   `hdds`: Float (Household Dietary Diversity Score).
    -   `csa_index`: Float (0.0 to 1.0, weighted composite of agricultural practices **including digital and finance access**).
    -   `temp_anomaly`: Float (°C).
    -   `precip_anomaly`: Float (mm).
    -   `digital_access`: Binary/Ordinal (Moderator).
    -   `finance_access`: Binary/Ordinal (Moderator).
    -   `interaction_digital`: Float (csa_index * digital_access).
    -   `interaction_finance`: Float (csa_index * finance_access).
    -   `provenance_id`: String (Mapping to raw survey response IDs or composite key `household_id + variable_name`).
-   **Constraints**: No missing values in `hdds`, `csa_index`, `temp_anomaly`.

### 3. Output Entities

#### `ModelOutput`
-   **Source**: `modeling.py`.
-   **Format**: JSON/CSV.
-   **Fields**:
    -   `parameter`: String (e.g., "csa_index").
    -   `estimate`: Float.
    -   `std_err`: Float.
    -   `p_value`: Float (Raw).
    -   `p_value_corrected`: Float (Bonferroni corrected).
    -   `vif`: Float.
    -   `significance`: Boolean (based on corrected p-value).

## Data Flow

1.  **Ingestion**: Download raw files from LSMS portal and NASA API.
2.  **Cleaning**: Handle missing values (imputation for climate gaps ≤ 3 months).
3.  **Merging**: Join on `household_id` and spatially (50km).
4.  **Index Construction**: Calculate `csa_index` (weighted composite of agricultural practices **including digital and finance access**).
5.  **Modeling**: Fit Fixed-Effects Regression (Country Dummies).
6.  **Export**: Save `ModelOutput` and visualizations.

## Data Hygiene

-   **Checksums**: All raw files checksummed (SHA256).
-   **PII**: None (anonymized household IDs).
-   **Versioning**: Each processed file named with timestamp and hash.
-   **Provenance**: `provenance_id` maps derived variables to raw survey response IDs (or `household_id + variable_name` if unique response ID is unavailable).