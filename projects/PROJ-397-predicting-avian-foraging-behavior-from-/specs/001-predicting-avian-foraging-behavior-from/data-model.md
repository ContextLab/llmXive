# Data Model: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

## Entity Definitions

### 1. ObservationRecord
Represents a single eBird sighting.
- `species_id` (str): Unique species identifier (mapped from `common_name`).
- `observation_date` (str): ISO 8601 date.
- `latitude` (float): Decimal degrees (WGS84).
- `longitude` (float): Decimal degrees (WGS84).
- `source` (str): "eBird".

### 2. LandCoverProfile
Represents the land cover composition at a location.
- `location_id` (str): Unique identifier for the observation point.
- `forest_proportion` (float): Fraction [0.0, 1.0].
- `grassland_proportion` (float): Fraction [0.0, 1.0].
- `wetland_proportion` (float): Fraction [0.0, 1.0].
- `urban_proportion` (float): Fraction [0.0, 1.0].
- `other_proportion` (float): Fraction [0.0, 1.0].
- *Constraint*: Sum of proportions = 1.0.

### 3. ForagingGuild
Categorical label assigned to a species.
- `species_id` (str): Unique species identifier.
- `guild` (enum): "ground", "canopy", "aerial".
- `source` (str): "Birds of the World" (via dynamic lookup).

### 4. MergedObservation
The primary analysis dataset (raw).
- `species_id` (str)
- `foraging_guild` (enum)
- `forest_proportion` (float)
- `grassland_proportion` (float)
- `wetland_proportion` (float)
- `urban_proportion` (float)
- `other_proportion` (float)
- `observation_date` (str)
- `latitude` (float)
- `longitude` (float)

### 5. SpeciesProfile (Aggregated & Transformed)
Aggregated data for model training and permutation testing.
- `species_id` (str)
- `foraging_guild` (enum)
- `mean_forest` (float)
- `mean_grassland` (float)
- `mean_wetland` (float)
- `mean_urban` (float)
- `mean_other` (float)
- `observation_count` (int)
- `clr_forest` (float): CLR transformed forest proportion.
- `clr_grassland` (float): CLR transformed grassland proportion.
- `clr_wetland` (float): CLR transformed wetland proportion.
- `clr_urban` (float): CLR transformed urban proportion.
- `clr_other` (float): CLR transformed other proportion.

## Data Flow

1.  **Raw EBD** -> `download_ebd.py` -> **Raw CSV**.
2.  **Raw CSV** -> `load_and_count.py` -> `select_top_species.py` -> **Filtered EBD**.
3.  **Filtered EBD** + **NLCD Raster** -> `calculate_100m_buffers.py` -> **LandCoverProfile**.
4.  **Filtered EBD** + **Guild Mapping** -> `join_guild_labels.py` -> **MergedObservation**.
5.  **MergedObservation** -> `aggregate.py` -> `transform_clr.py` -> **SpeciesProfile**.
6.  **SpeciesProfile** -> `train.py` -> **Model**.
7.  **SpeciesProfile** -> `stratified_permutation.py` -> **Null Distribution**. *Note: Permutation test uses SpeciesProfile, not MergedObservation.*

## Schema Constraints

- **Missing Data**: Observations with invalid coordinates or missing land cover data are dropped.
- **Filtering**: Species with `observation_count` < 50 are excluded from `MergedObservation` and `SpeciesProfile`.
- **Proportions**: All land cover proportions must be non-negative and sum to 1.0 (within floating point tolerance).
- **CLR Transformation**: CLR values are derived from proportions; sum of CLR values is not constrained to 1.0.
