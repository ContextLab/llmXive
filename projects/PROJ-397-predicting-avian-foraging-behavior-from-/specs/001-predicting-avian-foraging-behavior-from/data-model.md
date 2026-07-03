# Data Model: Predicting Avian Foraging Guilds

## Entities & Relationships

### 1. ObservationRecord
Represents a single eBird sighting.
- **Attributes**:
  - `obs_id`: Unique identifier (derived from EBD row index or UUID).
  - `species_id`: eBird species code (e.g., "AMRO", "HOMI").
  - `species_common`: Common name (e.g., "American Robin").
  - `observation_date`: Date of observation (YYYY-MM-DD).
  - `latitude`: Decimal degrees (WGS84).
  - `longitude`: Decimal degrees (WGS84).
  - `foraging_guild`: Categorical (ground, canopy, aerial). *Derived from external lookup.*
  - `land_cover_proportions`: Nested object or flattened columns (see below).

### 2. LandCoverProfile
Derived from NLCD 2019, represents the habitat composition at an observation location.
- **Attributes**:
  - `location_id`: Links to `ObservationRecord.obs_id`.
  - `forest_prop`: Float (0.0 - 1.0).
  - `grassland_prop`: Float (0.0 - 1.0).
  - `wetland_prop`: Float (0.0 - 1.0).
  - `urban_prop`: Float (0.0 - 1.0).
  - `other_prop`: Float (0.0 - 1.0). (Remainder).
  - `source_raster`: "NLCD_2019".
  - `buffer_radius_m`: 100.

### 3. SpeciesHabitatProfile (Aggregated)
**New Entity**: Represents the aggregated land cover profile for a single species, used for modeling.
- **Attributes**:
  - `species_id`: eBird species code.
  - `species_common`: Common name.
  - `foraging_guild`: Categorical (ground, canopy, aerial).
  - `mean_forest_prop`: Float (0.0 - 1.0).
  - `mean_grassland_prop`: Float (0.0 - 1.0).
  - `mean_wetland_prop`: Float (0.0 - 1.0).
  - `mean_urban_prop`: Float (0.0 - 1.0).
  - `mean_other_prop`: Float (0.0 - 1.0).
  - `n_observations`: Integer (count of observations used for aggregation).

### 4. ModelOutput
Results of the Random Forest classification.
- **Attributes**:
  - `model_id`: Hash of code + data.
  - `random_seed`: Integer.
  - `balanced_accuracy`: Float.
  - `f1_ground`: Float.
  - `f1_canopy`: Float.
  - `f1_aerial`: Float.
  - `feature_importance`: Dictionary mapping feature names to scores.
  - `permutation_p_value`: Float.

## Data Flow

1. **Raw EBD** -> `download_ebd.py` -> **Raw CSV**
2. **Raw NLCD** -> `download_nlcd.py` -> **Raw ZIP/GeoTIFF**
3. **Raw CSV** + **Raw GeoTIFF** + **Guild Lookup** -> `merge_and_buffer.py` -> **Processed CSV** (`merged_observations.csv`)
4. **Processed CSV** -> `aggregate.py` -> **Species Profiles** (`species_profiles.csv`)
5. **Species Profiles** -> `train.py` -> **Model Artifact** (`.pkl`) + **Metrics JSON**
6. **Model Artifact** + **Species Profiles** -> `evaluate.py` -> **Permutation Results**
7. **Model Artifact** + **Species Profiles** -> `viz/*.py` -> **PNG/GeoJSON**

## Storage Formats

- **Raw Data**: CSV (EBD), ZIP (NLCD).
- **Processed Data**: CSV (tabular), GeoJSON (spatial maps).
- **Metadata**: YAML (`data/metadata.yaml`).
- **Models**: Pickle (`.pkl`) or Joblib (`.joblib`).