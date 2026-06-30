# Data Model: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Overview

This document defines the data structures for the telomere-lifespan analysis pipeline. It covers the raw ingestion format, the cleaned/merged analysis dataset, and the output model results. All data models adhere to the **Single Source of Truth** (Constitution Principle IV) and **Data Hygiene** (Principle III) requirements.

## Entity Definitions

### 1. SpeciesRecord (Analysis Dataset)
The core unit of analysis. Represents a single species entry in the merged, cleaned dataset.

| Field Name | Type | Description | Source | Constraints |
|------------|------|-------------|--------|-------------|
| `species_id` | string | Unique identifier (e.g., "Genus_species") | Derived (AnAge ID) | PK, Unique |
| `telomere_length_kb` | float | Telomere length in kilobases (Species Mean). | Dryad | > 0.0 |
| `lifespan_years` | float | Maximum lifespan in years. | AnAge | > 0.0 |
| `migration_status` | string | "Migratory", "Resident", or "Unknown". | AnAge | Enum |
| `body_mass_g` | float | Body mass in grams. | AnAge | > 0.0 |
| `study_id` | string | Source study identifier (from Dryad). | Dryad | |
| `measurement_method` | string | "TRF", "qPCR", or "Unknown". | Dryad | |
| `age_category` | string | "Juvenile", "Adult", "Unknown". | Dryad | **Filtered to "Juvenile"** |
| `tissue_type` | string | "Blood", "Feather", "Unknown". | Dryad | Covariate |
| `provenance_source` | string | "Dryad", "AnAge". | Derived | |

### 2. ModelResult
Output of the PGLS fitting process.

| Field Name | Type | Description |
|------------|------|-------------|
| `model_type` | string | "PGLS_Base" or "PGLS_Interaction" |
| `fixed_effect_telomere` | float | Coefficient for telomere length. |
| `fixed_effect_migration` | float | Coefficient for migration (if interaction model). |
| `interaction_effect` | float | Interaction coefficient (telomere * migration). **(Optional if N < 30)** |
| `p_value_telomere` | float | P-value for telomere effect. |
| `p_value_interaction` | float | P-value for interaction effect. **(Optional if N < 30)** |
| `phylogenetic_lambda` | float | Pagel's lambda (phylogenetic signal). |
| `aic_score` | float | Akaike Information Criterion. |
| `n_species` | int | Number of species in the model. |
| `low_power_flag` | boolean | True if N < 15 or lambda estimation was unstable. |
| `power_estimate` | float | Estimated power (Partial R-squared based). |

### 3. SensitivityLog
Output of the LOOCV/Jackknife analysis.

| Field Name | Type | Description |
|------------|------|-------------|
| `iteration_id` | int | Iteration number (species excluded). |
| `excluded_species` | string | Name of excluded species. |
| `coefficient_telomere` | float | Coefficient calculated without this species. |
| `p_value` | float | P-value calculated without this species. |

## Data Flow

1.  **Raw Ingestion**: `raw/dryad_*.csv`, `raw/anage_*.csv` (Unmodified, checksummed).
2.  **Cleaning**: `processed/telomere_standardized.csv` (kb conversion applied, age filtered to Juvenile).
3.  **Merging**: `processed/merged_analysis.csv` (Final `SpeciesRecord` table, aggregated to species mean).
4.  **Modeling**: `results/model_summary.csv` (Final `ModelResult`).
5.  **Sensitivity**: `results/sensitivity_log.csv` (Final `SensitivityLog`).

## Data Quality Rules

*   **Missing Values**: Rows with missing `telomere_length_kb` or `lifespan_years` are excluded from the primary analysis and logged.
*   **Unit Consistency**: All telomere lengths must be in `kb`. Relative units (Ct) are excluded unless a conversion factor is explicitly provided in the source metadata.
*   **Species Matching**: Only species present in *both* datasets (after standardization) are included.
*   **Age Filter**: **Only** records with `age_category` = "Juvenile" (or equivalent) are retained. Records with unknown age are excluded to prevent confounding by sampling age structure.
*   **Aggregation**: Telomere length is aggregated to the species mean before modeling.