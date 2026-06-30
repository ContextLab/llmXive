# Data Model: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## Overview

This document defines the data structures, schemas, and relationships for the project. It ensures that the implementation adheres to the "Data Hygiene" and "Single Source of Truth" principles.

## Key Entities

### 1. Species
Represents a taxon (Genus + Species) in the study.
-   **Attributes**: `species_id` (unique), `scientific_name`, `genus`, `species`, `trait_source` (e.g., "Handbook 2013"), `exclusion_reason` (if any).

### 2. OccurrenceRecord
A single observation from GBIF.
-   **Attributes**: `record_id`, `species_id`, `latitude`, `longitude`, `timestamp`, `source` (GBIF), `cleaned` (boolean).

### 3. ClimateRasterStack
A set of 19 bioclimatic layers for a specific species extent.
-   **Attributes**: `species_id`, `raster_path` (list of 19 paths), `resolution`, `crs`, `extent` (min_lon, max_lon, min_lat, max_lat), `background_density` (points per km²).

### 4. TraitProfile
Species-level functional traits.
-   **Attributes**: `species_id`, `sla` (Specific Leaf Area), `seed_mass`, `plant_height`, `sla_unit`, `seed_mass_unit`, `height_unit`, `source_verified` (boolean), `trait_imputed` (boolean, for test set).

### 5. ModelResult
Performance metrics for a specific model configuration on a specific species.
-   **Attributes**: `species_id`, `model_type` (climate-only, climate+traits-imputed), `auc`, `tss`, `cv_folds`, `hyperparams` (JSON), `test_species_id` (for LOSO), `trait_imputed` (boolean), `imputed_traits` (JSON, optional).

### 6. StatisticalSummary
Aggregate results of the LMM.
-   **Attributes**: `metric` (AUC or TSS), `mean_climate_only`, `mean_climate_traits`, `mean_diff`, `p_value_raw`, `p_value_corrected`, `cohens_d`, `n_species`, `vif_warning`, `vif_details`, `random_effect_variance`, `fixed_effect_estimate`.

### 7. SensitivityAnalysis
Results of the threshold sweep.
-   **Attributes**: `threshold`, `direction_consistent` (boolean), `count_consistent` (integer).

## Data Flow

1.  **Raw Data**: GBIF (API), WorldClim (GeoTIFF), TRY (CSV/JSON) -> `data/raw/`.
2.  **Processed Data**: Cleaned Occurrences, Extracted Climate Values, Merged Traits -> `data/processed/`.
3.  **Model Output**: Per-species AUC/TSS -> `results/model_results.json`.
4.  **Final Report**: Statistical summaries -> `results/stats_report.json`.
5.  **Sensitivity Output**: Threshold sweep results -> `results/sensitivity_analysis.json`.

## Constraints

-   **Spatial Thinning**: Max 10km, min 1km. If <50 points remain, reduce thinning or flag.
- **Background Points**: **Density-based** (1 point per 100 km² of convex hull area). Max [deferred].
-   **Missing Data**: Species with missing traits are excluded from the "Climate+Traits" branch but included in "Climate-only".
-   **VIF**: If VIF > 5, flag in `ModelResult` or `StatisticalSummary`.
-   **Power**: Minimum N=30 species required. If N < 30, halt with 'Power Insufficient' error.
-   **Circularity**: Test species traits MUST be **imputed** (predicted from climate) for the 'climate+traits' model to ensure valid generalization testing.
- **SC-001 Scope**: The [deferred] retention metric applies to the **included species set** (N >= 30), not the target 50. If species are excluded due to data gaps, SC-001 is evaluated on the remaining set.