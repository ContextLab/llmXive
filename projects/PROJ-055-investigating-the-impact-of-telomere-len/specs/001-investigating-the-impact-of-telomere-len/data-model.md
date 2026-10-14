# Data Model: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Overview
The pipeline manipulates three primary artifacts:

1. **Raw ingestion files** (unchanged copies of Dryad/AnAge CSVs).  
2. **Processed analysis dataset** (`merged_analysis.csv`).  
3. **Model output** (`model_summary.csv` and `sensitivity_log.csv`).  

All artifacts are version‑hashed and stored under `data/` or `results/`.

## Entity Definitions

### SpeciesRecord (analysis dataset)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `species_id` | string | Canonical `Genus_species` identifier (derived from AnAge). | Unique, non‑empty |
| `telomere_length_kb` | number | Species‑mean telomere length, **kilobases**. | > 0 |
| `lifespan_years` | number | Maximum recorded lifespan, **years**. | > 0 |
| `migration_status` | string | `"Migratory"`, `"Resident"`, or `"Unknown"`. | Enum |
| `body_mass_g` | number | Body mass, **grams**. | > 0 |
| `study_id` | string | Dryad study identifier (e.g., DOI). | May be empty if synthetic |
| `measurement_method` | string | `"TRF"`, `"qPCR"`, or `"Unknown"`. | |
| `age_category` | string | `"Juvenile"` (required after filtering). | Must be `"Juvenile"` |
| `tissue_type` | string | `"Blood"`, `"Feather"`, or `"Unknown"`. | |
| `provenance_source` | string | Source of the record (Dryad, AnAge). | |

### ModelResult
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"PGLS_Base"` or `"PGLS_Interaction"`. |
| `fixed_effect_telomere` | number | Coefficient for `telomere_length_kb`. |
| `fixed_effect_migration` | number | Coefficient for `migration_status` (only interaction model). |
| `interaction_effect` | number | *Optional* – telomere × migration coefficient. |
| `p_value_telomere` | number | P‑value for telomere coefficient (0 – 1). |
| `p_value_interaction` | number | *Optional* – P‑value for interaction term. |
| `phylogenetic_lambda` | number | Estimated Pagel’s λ (0 – 1). |
| `aic_score` | number | Akaike Information Criterion of the fitted model. |
| `n_species` | integer | Number of species used. |
| `low_power_flag` | boolean | True if `n_species < 30` or λ estimation was unstable. |
| `power_estimate` | number | Simulated power (0 – 1). |

### SensitivityLog
| Field | Type | Description |
|-------|------|-------------|
| `iteration_id` | integer | Sequential index of the LOOCV/jackknife iteration. |
| `excluded_species` | string | Species left out for this iteration. |
| `coefficient_telomere` | number | Telomere coefficient computed without the excluded species. |
| `p_value` | number | Corresponding p‑value. |

## Data Flow Diagram
1. **Raw files** → `02_ingest_data.py` → `data/raw/`.  
2. **Cleaning** → `03_clean_merge.py` → `data/processed/merged_analysis.csv` (conforms to `dataset.schema.yaml`).  
3. **Phylogeny** → `04_fetch_phylogeny.py` → `data/phylogeny/bird_tree.nwk`.  
4. **Modeling** → `05_fit_pgls_*.py` → `results/model_summary.csv` (conforms to `model_output.schema.yaml`).  
5. **Sensitivity** → `07_sensitivity.py` → `results/sensitivity_log.csv`.  
6. **Visualization** → `08_visualize.py` → PNG files in `results/`.  

All steps write a SHA‑256 checksum file (`*.sha256`) and invoke `utils.py --update-state` to keep `state/projects/PROJ-055...yaml` current.
