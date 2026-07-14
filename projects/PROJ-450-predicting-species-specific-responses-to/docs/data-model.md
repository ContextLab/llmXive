# Data Model: Predicting Species-Specific Responses to Climate Change

## Directory Structure
```
project_root/
├── data/
│ ├── raw/
│ │ ├── worldclim_v2/ # Downloaded.tif rasters
│ │ │ ├── bio1_1970_2000.tif
│ │ │ ├── bio12_1970_2000.tif
│ │ │ ├── bio1_1991_2020.tif
│ │ │ └── bio12_1991_2020.tif
│ │ └── gbif_occurrences/ # Raw GBIF CSV exports
│ ├── processed/
│ │ ├── centroids.csv # Aggregated niche centroids
│ │ └── points_with_climate.csv # Occurrences with climate values
│ └── metadata.yaml # Query parameters, checksums, timestamps
├── results/
│ ├── regression_results.csv # PGLS/WLS output
│ ├── power_analysis_report.csv # Power analysis metrics
│ ├── sensitivity_summary.csv # Subsampling variability
│ └── figures/
│ └── niche_shift_plot.png # 1200x800px scatter plot
├── src/
│ ├── code/
│ │ ├── utils.R # Logging, validation, helpers
│ │ ├── fetch_gbif.R # GBIF query and filtering
│ │ ├── download_worldclim.R # Climate data download
│ │ ├── extract_climate.R # Raster value extraction
│ │ ├── compute_centroids.R # Centroid calculation
│ │ ├── compute_shifts.R # Global z-scoring, ΔN
│ │ ├── compute_regional_warming.R # ΔT calculation
│ │ ├── analyze_shifts.R # PGLS/WLS regression
│ │ ├── power_analysis.R # A priori power analysis
│ │ ├── sensitivity.R # Subsampling analysis
│ │ └── plotting.R # Figure generation
│ └── tests/
│ ├── unit/
│ │ ├── test_utils.R
│ │ ├── test_fetch_gbif.R
│ │ └── test_extract_climate.R
│ └── integration/
│ └── test_us1_centroids.R
├── docs/
│ ├── research.md # This file
│ └── data-model.md # This file
└── config.yaml # Project configuration
```

## Data Schemas

### `data/raw/gbif_occurrences/*.csv` (Raw GBIF Export)
| Column | Type | Description |
|--------|------|-------------|
| scientificName | string | Species name |
| decimalLatitude | float | Latitude (-90 to 90) |
| decimalLongitude | float | Longitude (-180 to 180) |
| eventDate | date | Collection date (YYYY-MM-DD) |
| coordinateUncertaintyInMeters | float | Uncertainty radius |
| occurrenceStatus | string | Must be "PRESERVED_SPECIMEN" |
| taxonKey | int | GBIF taxonomic key |

### `data/processed/centroids.csv`
| Column | Type | Description |
|--------|------|-------------|
| species | string | Species name |
| period | string | "1970-2000" or "1991-2020" |
| n_records | int | Number of records used |
| mean_temp | float | Mean annual temperature (°C) |
| mean_precip | float | Mean annual precipitation (mm) |

### `data/processed/points_with_climate.csv`
| Column | Type | Description |
|--------|------|-------------|
| species | string | Species name |
| period | string | "1970-2000" or "1991-2020" |
| latitude | float | Latitude |
| longitude | float | Longitude |
| temp | float | Extracted temperature |
| precip | float | Extracted precipitation |
| z_temp | float | Global z-scored temperature |
| z_precip | float | Global z-scored precipitation |

### `results/regression_results.csv`
| Column | Type | Description |
|--------|------|-------------|
| method | string | "PGLS" or "WLS" |
| slope | float | Regression slope (ΔN vs ΔT) |
| ci_lower | float | 95% CI lower bound |
| ci_upper | float | 95% CI upper bound |
| r_squared | float | R² value |
| p_value | float | P-value |
| n_species | int | Number of species in analysis |

### `results/sensitivity_summary.csv`
| Column | Type | Description |
|--------|------|-------------|
| species | string | Species name |
| n_records | int | Original record count |
| mean_shift | float | Mean ΔN across replicates |
| sd_shift | float | Standard deviation of ΔN |
| flag_high_var | bool | TRUE if SD ≥ 0.2 |

## Metadata Schema (`data/metadata.yaml`)
```yaml
queries:
 - timestamp: "2024-01-15T10:30:00Z"
 species_list: "data/species_list.csv"
 gbif_params:
 hasCoordinate: true
 occurrenceStatus: "PRESERVED_SPECIMEN"
 checksum: "md5:abc123..."
climate:
 source: "WorldClim v2.1"
 periods:
 - "1970-2000"
 - "1991-2020"
 variables:
 - "bio1"
 - "bio12"
 checksums:
 "bio1_1970_2000.tif": "md5:xyz789..."
```

## Data Dependencies
1. `fetch_gbif.R` → `data/raw/gbif_occurrences/`
2. `download_worldclim.R` → `data/raw/worldclim_v2/`
3. `extract_climate.R` → Reads (1) and (2) → `data/processed/points_with_climate.csv`
4. `compute_centroids.R` → Reads (3) → `data/processed/centroids.csv`
5. `compute_shifts.R` → Reads (3) → Calculates ΔN
6. `compute_regional_warming.R` → Reads (2) → Calculates ΔT
7. `analyze_shifts.R` → Reads (5) and (6) → `results/regression_results.csv`
8. `sensitivity.R` → Reads (1) → `results/sensitivity_summary.csv`