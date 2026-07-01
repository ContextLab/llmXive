# Data Model: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## 1. Entity-Relationship Overview

The data model consists of four primary entities: `Species`, `OccurrenceRecord`, `ClimateRasterStack`, and `TraitProfile`. These are linked to form `ModelResult` entities for the LOSO cycle.

### 1.1 Species
- **Attributes**: `taxon_key` (GBIF ID), `scientific_name`, `genus`, `species`.

### 1.2 OccurrenceRecord
- **Attributes**: `record_id`, `taxon_key`, `latitude`, `longitude`, `event_date`, `source`.
- **Derived**: `cleaned_record_id` (after thinning), `background_flag` (presence/absence), `thinning_distance_km`.

### 1.3 ClimateRasterStack
- **Attributes**: `raster_id`, `variable_name` (e.g., "bio1"), `resolution`, `crs`.
- **Derived**: `extracted_values` (list of 19 floats per occurrence).

### 1.4 TraitProfile
- **Attributes**: `taxon_key`, `sla`, `seed_mass`, `height`, `trait_source`, `is_verified` (bool), `exclusion_reason` (null or string).
- **Derived**: `flag_unverified` (true when `is_verified` = false).

### 1.5 ModelResult
- **Attributes**: `species_id`, `fold_id`, `model_type` (`climate-only` | `climate+traits`), `auc`, `tss`, `vif_scores` (dict), `collinearity_flag` (bool).

## 2. Data Flow

1. **Ingestion**: Raw GBIF/WorldClim/TRY → `data/raw/`.
2. **Cleaning**: Duplicate removal, spatial thinning with fallback, trait validation → `data/processed/`.
3. **Feature Extraction**: Join occurrences with climate rasters → `data/processed/features.parquet`.
4. **Modeling**: LOSO loop → `results/metrics_per_fold.json`.
5. **Aggregation**: Statistical tests → `results/final_report.json`.

## 3. Validation Rules
- **Spatial Thinning**: Must retain ≥ 80 % of raw records; fallback reduces distance by 1 km steps to a minimum of 1 km (FR‑001).
- **Trait Completeness**: Missing any of SLA, Seed Mass, Height → `exclusion_reason = "missing_trait"` and species excluded from trait‑augmented branch (FR‑006). Unverified protocol → `is_verified = false`; flagged but retained (FR‑010).
- **VIF**: If any VIF > 5, set `collinearity_flag = true`; report values (FR‑011).
- **Random Seed**: All stochastic processes use seed 42.
