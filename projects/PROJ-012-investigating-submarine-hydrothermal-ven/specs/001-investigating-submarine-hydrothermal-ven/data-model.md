# Data Model: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

## Overview

This document defines the data structures, schemas, and relationships used throughout the pipeline. It ensures that raw inputs (FASTQ, sensor logs) are transformed into a unified, analysis-ready format while preserving provenance.

## Entities

### 1. Sample (Core Entity)

Represents a single collection event at a vent site.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `sample_id` | String | Unique identifier (e.g., `VENT_001_S01`) | Derived |
| `deployment_event` | String | ID of the sensor deployment | Metadata |
| `sensor_id` | String | ID of the pH/Temp sensor | Metadata |
| `coordinates` | String | "lat,lon" or "x,y,z" | Metadata |
| `timestamp` | DateTime | UTC timestamp of collection | Sensor Log |
| `pH_value` | Float | pH measurement | Sensor Log |
| `pH_std` | Float | Standard deviation of pH in ±15 min window | Calculated (FR-001.1) |
| `temp_value` | Float | Temperature measurement | Sensor Log |
| `status` | Enum | `valid`, `rejected_temporal`, `rejected_ph_outlier`, `flagged_review` | Pipeline Logic |

### 2. OTU/ASV Table

Matrix of microbial abundances per sample.

| Attribute | Type | Description |
|-----------|------|-------------|
| `sample_id` | String | Foreign key to `Sample` |
| `otu_id` | String | OTU/ASV identifier |
| `abundance` | Integer | Raw read count |
| `taxonomy` | String | Taxonomic classification (Kingdom;Phylum;...) |

### 3. Diversity Metrics

Derived metrics per sample.

| Attribute | Type | Description |
|-----------|------|-------------|
| `sample_id` | String | Foreign key to `Sample` |
| `shannon_index` | Float | Shannon diversity index |
| `simpson_index` | Float | Simpson diversity index |
| `rarefaction_depth` | Integer | Depth used for rarefaction |

### 4. Analysis Results

Outputs of statistical models.

| Attribute | Type | Description |
|-----------|------|-------------|
| `analysis_id` | String | Unique ID for the run |
| `model_type` | Enum | `LME`, `OLS`, `PERMANOVA`, `dbRDA`, `Mantel` |
| `metric` | String | e.g., "shannon", "bray_curtis" |
| `coefficient` | Float | Regression coefficient or F-stat |
| `p_value` | Float | P-value |
| `r_squared` | Float | R² (for PERMANOVA/dbRDA) |
| `flag` | String | e.g., "low_power", "heteroscedastic", "associational_only", "dispersion_confounded" |

## Data Flow

1.  **Ingestion**: Raw FASTQ, pH CSV, Temp CSV -> `Sample` + `OTU/ASV Table` (raw).
2.  **Preprocessing**:
    -   Filter `Sample` by pH range (1.0–10.0).
    -   Align timestamps (±15 min).
    -   Calculate `pH_std`.
    -   Rarefy `OTU/ASV Table`.
    -   Calculate `Diversity Metrics`.
3.  **Analysis**:
    -   Join `Sample` + `Diversity Metrics` -> `Analysis Results` (LME/GLMM).
    -   Join `Sample` + `OTU/ASV Table` -> Distance Matrix -> `Analysis Results` (PERMANOVA, dbRDA, Mantel).
4.  **Output**: Final CSV/JSON with all results and flags.

## Constraints & Validation

-   **pH Range**: Must be between 1.0 and 10.0. Values 1.0–2.0 and 8.5–10.0 trigger `flagged_review`.
-   **Temporal Mismatch**: If no pH/Temp reading within ±15 min, `status` = `rejected_temporal`.
-   **Sequencing Depth**: Must be >= `rarefaction_depth`. Samples below this are excluded or flagged.
-   **Collinearity**: If VIF > 5 for pH/Temp, `flag` = `collinear`.
-   **Dispersion**: If `betadisper` is significant, `flag` = `dispersion_confounded`.