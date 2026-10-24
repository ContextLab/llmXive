# Data Model: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Overview
Three primary artifact classes: raw ingestion files (immutable), the processed analysis dataset, and model output artifacts. Every artifact is version‑hashed; no synthetic records exist.

## Entity Definitions

### SpeciesRecord (analysis dataset)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `species_id` | string | Canonical `Genus_species` identifier. | Unique, non‑empty |
| `telomere_length_kb` | number | Species‑mean telomere length, kilobases. | > 0 |
| `mean_lifespan_days` | number | Species‑mean adult lifespan, days. | > 0 |
| `migration_status` | string | `"Migratory"`, `"Resident"`, or `"Unknown"`. | Enum |
| `breeding_latitude` | number | Mean breeding latitude (decimal degrees). | -90 ≤ value ≤ 90 |
| `body_mass_g` | number | Body mass, grams. | > 0 |
| `study_ids` | array[string] | List of Dryad DOIs contributing to this species mean. | Each entry non‑empty |
| `n_obs` | integer | Number of individual observations after filtering. | ≥ 1 |
| `measurement_method` | string | `"TRF"`, `"qPCR"`, or `"Unknown"`. |
| `age_category` | string | Must be `"Juvenile"` after filtering. | Enum |
| `tissue_type` | string | `"Blood"`, `"Feather"`, or `"Unknown"`. | Enum |
| `provenance_source` | string | Concatenated provenance identifier (e.g., `"<Dryad DOI>+<AnAge/BirdLife ID>"`). | Non‑empty |

### ModelResult
| Field | Type | Description |
|------|------|-------------|
| `model_type` | string | `"PGLS_Base"` or `"PGLS_Interaction"` |
| `fixed_effect_telomere` | number | null | Coefficient for telomere length; null when low‑power flag is true. |
| `se_telomere` | number | null | Standard error. |
| `ci_lower_telomere` | number | null | 95 % CI lower bound. |
| `ci_upper_telomere` | number | null | 95 % CI upper bound. |
| `fixed_effect_body_mass` | number | null | Coefficient for body mass (base model). |
| `se_body_mass` | number | null | Standard error for body mass. |
| `ci_lower_body_mass` | number | null | 95 % CI lower bound for body mass. |
| `ci_upper_body_mass` | number | null | 95 % CI upper bound for body mass. |
| `fixed_effect_migration` | number | null | Coefficient for migration (interaction model only). |
| `se_migration` | number | null | Standard error. |
| `ci_lower_migration` | number | null | 95 % CI lower bound. |
| `ci_upper_migration` | number | null | 95 % CI upper bound. |
| `interaction_effect_migration` | number | null | Telomere × migration interaction coefficient. |
| `se_interaction_migration` | number | null | Standard error. |
| `ci_lower_interaction_migration` | number | null | 95 % CI lower bound. |
| `ci_upper_interaction_migration` | number | null | 95 % CI upper bound. |
| `interaction_effect_latitude` | number | null | Telomere × breeding latitude interaction coefficient. |
| `se_interaction_latitude` | number | null | Standard error. |
| `ci_lower_interaction_latitude` | number | null | 95 % CI lower bound. |
| `ci_upper_interaction_latitude` | number | null | 95 % CI upper bound. |
| `p_value_telomere` | number | null | Two‑sided p‑value; null when low‑power. |
| `p_value_interaction_migration` | number | null | p‑value for telomere × migration interaction; null for base model or low‑power. |
| `p_value_interaction_latitude` | number | null | p‑value for telomere × latitude interaction; null for base model or low‑power. |
| `significance_flag` | boolean | True when `p_value_telomere < α` (α = 0.05). |
| `aic_score` | number | null | Akaike Information Criterion; null when low‑power. |
| `delta_aic` | number | null | ΔAIC vs. base model (interaction model only). |
| `n_species` | integer | Number of species included in the fitted model. |
| `low_power_flag` | boolean | True when `n_species < 15`. |
| `low_power_message` | string | null | `"Low Power: Phylogenetic inference unreliable"` when applicable. |
| `power_estimate` | number | Simulated power to detect a standardized slope of 0.2 at α = 0.05 for the observed species count. |

### SensitivityLog (log‑only artifact)
| Field | Type | Description |
|-------|------|-------------|
| `iteration_id` | integer | Index of LOOCV or jackknife iteration. |
| `excluded_unit` | string | Species name (LOOCV) or study DOI (jackknife). |
| `method` | string | `"LOOCV"` or `"Jackknife"` with justification. |
| `coefficient_telomere` | number | Refitted telomere coefficient for this iteration. |
| `p_value_telomere` | number | Corresponding p‑value. |

## Data Flow
1. `01_discover_data.py` → `config.yaml` (populated `dataset_ids`).  
2. `02_ingest_data.py` → `data/raw/` (raw CSVs) + SHA‑256 side‑cars.  
3. `03_clean_merge.py` → `data/processed/merged_analysis.csv` (conforms to `contracts/dataset.schema.yaml`).  
4. `04_fit_pgls_base.py` / `05_fit_pgls_interaction.py` → `results/model_summary.csv` (conforms to `contracts/model_output.schema.yaml`).  
5. `06_sensitivity_power.py` → `results/sensitivity_log.csv`, `results/power_report.yaml`.  
6. `07_visualize.py` → PNGs in `results/`.  

Every step writes a checksum file and updates the project state YAML, guaranteeing reproducibility (Constitution I).

---

