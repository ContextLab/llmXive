# Data Model: Reef-Species Unified Dataset

**Version**: 1.0.0
**Generated**: 2024-01-15
**Source**: Pipeline Output from `code/ingest.py` and `code/features.py`
**File Path**: `data/processed/reef_species_unified.csv`

## Overview

This document describes the schema of the `reef_species_unified` dataset, which serves as the primary input for the coral bleaching susceptibility prediction model. The dataset is constructed by merging heterogeneous data sources:
- **NOAA**: Sea Surface Temperature (SST) and Degree Heating Weeks (DHW).
- **UNEP**: Reef geometries and locations.
- **Coral Trait Database**: Species-specific thermal tolerance traits.
- **ReefBase**: Historical bleaching events.

The data is aligned to a 5-km grid resolution and includes engineered features such as lagged environmental variables and interaction terms.

## Schema Definition

The dataset is a tabular CSV file where each row represents a unique **Reef-Species** observation at a specific time point.

### Core Identifiers

| Column Name | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `reef_id` | string | Unique identifier for the reef location (e.g., "RRR_001"). | UNEP |
| `species_id` | string | Unique identifier for the coral species (e.g., "ACR_POR"). | Coral Trait DB |
| `timestamp` | datetime | ISO 8601 formatted timestamp of the observation. | NOAA / ReefBase |
| `latitude` | float | Latitude of the reef centroid (WGS84). | UNEP |
| `longitude` | float | Longitude of the reef centroid (WGS84). | UNEP |

### Environmental Features

| Column Name | Type | Description | Source | Derived? |
|:--- |:--- |:--- |:--- |:--- |
| `sst_mean` | float | Mean Sea Surface Temperature (°C) for the observation period. | NOAA | No |
| `sst_std` | float | Standard deviation of SST within the period. | NOAA | No |
| `dhw` | float | Degree Heating Weeks (accumulated heat stress). | NOAA | No |
| `sst_lag_30d` | float | 30-day rolling mean of SST. | Features | Yes |
| `dhw_sst_interaction` | float | Interaction term: `DHW * thermal_tolerance`. | Features | Yes |

### Biological Traits

| Column Name | Type | Description | Source | Notes |
|:--- |:--- |:--- |:--- |:--- |
| `thermal_tolerance` | float | Species-specific thermal tolerance threshold (°C). | Coral Trait DB | Imputed if missing |
| `growth_rate` | float | Coral growth rate category (normalized). | Coral Trait DB | Optional |
| `trait_data_flag` | boolean | `True` if trait data was missing and imputed/flagged; `False` if original. | Ingest | |

### Target Variable

| Column Name | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `bleaching_event` | integer (0/1) | Binary label: `1` if a bleaching event was observed, `0` otherwise. | ReefBase |

### Data Quality & Processing Flags

| Column Name | Type | Description |
|:--- |:--- |:--- |
| `gap_status` | string | Status of temporal gaps: `valid`, `imputed`, or `excluded`. |
| `vif_filtered` | boolean | `True` if this feature set was retained after VIF filtering (VIF ≤ 5). |
| `region` | string | Geographic region classification (e.g., "West_Pacific", "East_Pacific") used for spatial splitting. |

## Data Processing Pipeline

1. **Ingestion**: Raw rasters and CSVs downloaded from `config.NOAA_URL`, `config.CORAL_TRAIT_URL`, etc.
2. **Merging**: Spatial join of UNEP reefs with NOAA rasters; temporal join with ReefBase events.
3. **Trait Alignment**: Species traits matched to reef observations; missing traits flagged.
4. **Feature Engineering**:
 - Lagged features computed using `compute_lagged_features` (30-day window).
 - Interaction term `dhw_sst_interaction` computed.
 - Definitional circularity check performed on DHW (residuals used if derived).
5. **Filtering**: High VIF features (VIF > 5) removed; resulting schema reflects filtered columns.
6. **Imputation**: Missing values filled via nearest temporal neighbor; rows with excessive gaps excluded.

## Constraints & Assumptions

- **Resolution**: All environmental data is resampled to 5-km grid cells.
- **Null Handling**: No nulls allowed in `sst_mean`, `dhw`, `thermal_tolerance`, or `bleaching_event`. Missing trait data is imputed and flagged.
- **Time Range**: Data covers the period from 2010 to 2024 (subject to availability).
- **Spatial Split**: The `region` column is derived for the purpose of the spatial train/test split (West vs. East Pacific).

## Usage Example

```python
import pandas as pd

df = pd.read_csv("data/processed/reef_species_unified.csv")

# Check for missing target values
assert df['bleaching_event'].isnull().sum() == 0

# Filter for high-confidence trait data
df_confident = df[df['trait_data_flag'] == False]

# View top features
print(df_confident[['reef_id', 'species_id', 'sst_mean', 'dhw', 'bleaching_event']].head())
```

## Maintenance

This schema is updated automatically when the `code/ingest.py` and `code/features.py` pipelines are re-run with new data sources or feature engineering logic. Any changes to the column set must be reflected in `contracts/dataset.schema.yaml`.