# Data Model: Climate-Smart Agricultural Practices for Food Security

**Date**: 2025-07-04 | **Spec**: `specs/agriculture-20250704-001/spec.md`

## Entity-Relationship Overview

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Pilot Region   │───────│   Household     │───────│   Survey        │
│  (primary key)  │       │  (foreign key)  │       │   Response      │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Farm Plot     │       │  Yield          │       │ CSA Practice    │
│  (location)     │       │ Measurement     │       │ (adoption)      │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │
        ▼
┌─────────────────┐
│ Remote Sensing  │
│  (imagery)      │
└─────────────────┘
```

## Core Tables

### pilot_region

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| pilot_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| region_name | VARCHAR(50) | Pilot region name | NOT NULL |
| country | VARCHAR(50) | Country name | NOT NULL |
| latitude_center | FLOAT | Geographic center latitude | NULLABLE |
| longitude_center | FLOAT | Geographic center longitude | NULLABLE |

### household

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| household_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| pilot_id | VARCHAR(36) | Foreign key | NOT NULL, FK → pilot_region |
| latitude | FLOAT | Geographic coordinate | NULLABLE |
| longitude | FLOAT | Geographic coordinate | NULLABLE |
| household_size | INTEGER | Number of members | NOT NULL, ≥1 |
| income_level | VARCHAR(20) | Income bracket | CHECK IN ('low', 'medium', 'high') |
| farmer_experience_years | INTEGER | Years farming experience | NOT NULL, ≥0 |
| irrigation_access | VARCHAR(20) | Irrigation type | CHECK IN ('none', 'rainfed', 'irrigated') |
| market_distance_km | FLOAT | Distance to nearest market | NULLABLE, ≥0 |

### survey_response

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| response_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| household_id | VARCHAR(36) | Foreign key | NOT NULL, FK → household |
| survey_date | DATE | Date of survey | NOT NULL |
| food_security_index_id | VARCHAR(36) | Foreign key | NULLABLE, FK → food_security_index_components |
| survey_version | VARCHAR(20) | Survey instrument version | NOT NULL |

### food_security_index_components

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| component_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| household_id | VARCHAR(36) | Foreign key | NOT NULL, FK → household |
| measurement_date | DATE | Date of measurement | NOT NULL |
| dietary_diversity_score | INTEGER | Score 0-12 | NOT NULL, 0-12 |
| food_frequency_score | INTEGER | Score 0-28 | NOT NULL, 0-28 |
| hunger_score | INTEGER | Score 0-6 | NOT NULL, 0-6 |
| index_total | INTEGER | Sum of components | NOT NULL, 0-46 |

### farm_plot

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| plot_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| household_id | VARCHAR(36) | Foreign key | NOT NULL, FK → household |
| area_hectares | FLOAT | Plot size | NOT NULL, >0 |
| soil_type | VARCHAR(50) | Soil classification | NULLABLE |
| elevation_meters | INTEGER | Altitude | NULLABLE |

### csa_practice

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| practice_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| plot_id | VARCHAR(36) | Foreign key | NOT NULL, FK → farm_plot |
| practice_type | VARCHAR(50) | Practice category | NOT NULL |
| adoption_date | DATE | When adopted | NULLABLE |

### yield_measurement

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| measurement_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| plot_id | VARCHAR(36) | Foreign key | NOT NULL, FK → farm_plot |
| measurement_date | DATE | Date of measurement | NOT NULL |
| growing_season | VARCHAR(20) | Season identifier | NOT NULL |
| yield_kg_per_hectare | FLOAT | Yield measurement | NOT NULL, >0 |
| crop_type | VARCHAR(50) | Crop variety | NOT NULL |
| measurement_method | VARCHAR(30) | Self-report, actual measurement, or remote sensing | NOT NULL, CHECK IN ('self_report', 'actual_measurement', 'remote_sensing') |

> **Yield Measurement Methodology**: Yield data comes from a combination of self-report (validated against a [deferred] subsample of actual measurements) and remote sensing (NDVI-based yield estimation). The measurement_method column tracks the source for each yield observation to enable sensitivity analysis. Remote sensing validation subsample size: [deferred pending Phase 2 implementation].

### climate_observation

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| observation_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| pilot_id | VARCHAR(36) | Foreign key | NOT NULL, FK → pilot_region |
| observation_date | DATE | Date of observation | NOT NULL |
| temperature_celsius | FLOAT | Mean daily temp | NULLABLE |
| precipitation_mm | FLOAT | Daily rainfall | NULLABLE, ≥0 |
| drought_index | FLOAT | Drought severity | NULLABLE, 0-10 scale |

### remote_sensing

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| imagery_id | VARCHAR(36) | Unique identifier | PRIMARY KEY |
| plot_id | VARCHAR(36) | Foreign key | NULLABLE, FK → farm_plot |
| capture_date | DATE | Image capture date | NOT NULL |
| ndvi_value | FLOAT | Vegetation index | NULLABLE, -1 ≤ value ≤ 1 |
| land_cover_class | VARCHAR(30) | Classification | NULLABLE |

## File Formats

### Raw Data (data/raw/)

- **CSV**: Survey responses, household data
- **Parquet**: Climate data (optimized for columnar access)
- **GeoTIFF**: Remote sensing imagery

### Processed Data (data/processed/)

- **Parquet**: All joined/transformed data for analysis
- **JSON**: Model outputs and predictions

## Data Quality Requirements

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Completeness (required fields) | ≥95% | Contract schema validation |
| Geographic coordinate accuracy | <100m error | GPS verification sampling |
| Temporal consistency | No gaps >7 days | Time series continuity check |
| Cross-record referential integrity | [deferred] | Foreign key constraint tests |
| Soil data coverage | ≥60% | Coverage rate KPI tracking |
| Yield measurement validation | [deferred] subsample with actual measurement | Contract validation against measurement_method |