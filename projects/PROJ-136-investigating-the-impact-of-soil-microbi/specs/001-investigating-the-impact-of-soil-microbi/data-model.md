# Data Model: 001-soil-microbiome-diversity-disease-resistance

## Entity Definitions

### Sample

Represents a single soil microbiome collection with associated metadata.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| sample_id | string | Unique identifier for the sample | Required, unique |
| gps_coordinates | string | GPS coordinates (latitude, longitude) | Required, format: "lat,lon" |
| plant_species | string | Plant species name | Required |
| soil_type | string | Soil classification | Required, used as covariate in statistical models |
| sequencing_depth | integer | Total reads per sample before rarefaction | Required, >0 |
| alpha_diversity_shannon | float | Shannon diversity index | Computed, optional |
| alpha_diversity_simpson | float | Simpson diversity index | Computed, optional |
| alpha_diversity_faith_pd | float | Faith's phylogenetic diversity | Computed, optional |
| rarefaction_depth | integer | Sequencing depth after rarefaction | Computed, default 10000 |

### Disease Incidence

Represents plant disease measurement for a sample.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| sample_id | string | Foreign key to Sample | Required, references Sample.sample_id |
| disease_type | string | Type of plant disease | Required |
| incidence_rate | float | Disease incidence (0-100%) | Required, 0 ≤ x ≤ 100 |
| measurement_date | date | Date of disease measurement | Required, ISO 8601 |

### Taxon

Represents a microbial taxonomic unit from OTU/ASV tables.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| taxon_id | string | Unique identifier for the taxon | Required, unique |
| taxonomic_lineage | string | Full taxonomic classification | Required |
| relative_abundance | float | Relative abundance in sample | Required, 0 ≤ x ≤ 1 |
| sample_id | string | Foreign key to Sample | Required, references Sample.sample_id |
| differential_abundance_q | float | ANCOM q-value for differential abundance | Computed, optional |

## Relationships

- **Sample 1:1 Disease Incidence**: Each sample has at most one disease incidence record
- **Sample 1:N Taxon**: Each sample contains multiple taxa (OTUs/ASVs)
- **Disease Incidence N:1 Sample**: Disease incidence records reference samples

## Data Flow

```
Raw Data (data/raw/)
    ↓ [download + checksum]
EMP/MG-RAST OTU/ASV Tables
    ↓ [filtering: ≥5% prevalence]
Filtered OTU/ASV Tables
    ↓ [rarefaction: 10k reads]
Rarefied OTU/ASV Tables
    ↓ [diversity computation]
Alpha-Diversity Metrics
    ↓ [merge with disease data]
Matched Dataset (Sample + Disease Incidence)
    ↓ [statistical analysis]
Model Outputs (coefficients, p-values)
    ↓ [network analysis]
Co-occurrence Networks
    ↓ [keystone identification]
Final Results
```

## Validation Rules

1. **sample_id uniqueness**: Each sample_id must be unique across Sample and Disease Incidence tables
2. **incidence_rate bounds**: 0 ≤ incidence_rate ≤ 100
3. **relative_abundance bounds**: 0 ≤ relative_abundance ≤ 1
4. **gps_coordinates format**: Must match "lat,lon" pattern with valid ranges (-90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180)
5. **sequencing_depth positive**: sequencing_depth > 0
6. **measurement_date format**: ISO 8601 (YYYY-MM-DD)