# Data Model: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Overview
Three primary artifact classes: raw ingestion files (immutable), the processed analysis dataset, and model outputs. All artifacts are version‑hashed under `data/` or `results/`. **No synthetic records exist in any artifact**; every row traces to a downloaded source file.

## Entity Definitions

### SpeciesRecord (analysis dataset)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `species_id` | string | Canonical `Genus_species` identifier | Unique, non‑empty |
| `telomere_length_kb` | number | Species‑mean telomere length, kilobases | > 0 |
| `lifespan_years` | number | Maximum recorded lifespan, years (wild‑recorded) | > 0 |
| `migration_status` | string | `"Migratory"`, `"Resident"`, `"Unknown"` | Enum |
| `body_mass_g` | number | Body mass, grams | > 0 |
| `study_ids` | array[string] | List of Dryad DOIs contributing to this species mean | Each entry non‑empty |
| `n_obs` | integer | Number of individual observations aggregated for this species (after juvenile and wild‑catch filters) | ≥ 1 |
| `measurement_method` | string | `"TRF"`, `"qPCR"`, or `"Unknown"` |
| `age_category` | string | Must be `"Juvenile"` after filtering | Enum: `"Juvenile"` |
| `tissue_type` | string | `"Blood"`, `"Feather"`, `"Unknown"` |
| `provenance_source` | string | Concatenated provenance identifier (e.g., `"<Dryad DOI>+<AnAge/BirdLife ID>"`) | Non‑empty |
| `study_id` | string | **Deprecated** – retained for backward compatibility; will be populated with the first DOI in `study_ids`. | MinLength 1 |

**Note**: `migration_status` may be `"Unknown"` when the source does not provide this covariate. Such records are **included** in the base PGLS model but are **explicitly excluded** from the interaction model (see research plan) to avoid treating missing data as a biological category.

### ModelResult
| Field | Type | Description |
|------|------|-------------|
| `model_type` | string | `"PGLS_Base"` or `"PGLS_Interaction"` |
| `fixed_effect_telomere` | number | null | Telomere coefficient; null when low‑power message issued. |
| `se_telomere` | number | null | Standard error of telomere coefficient. |
| `ci_lower_telomere` | number | null | 95 % CI lower bound for telomere coefficient. |
| `ci_upper_telomere` | number | null | 95 % CI upper bound for telomere coefficient. |
| `fixed_effect_migration` | number | null | Coefficient for migration (interaction model only). |
| `se_migration` | number | null | Standard error for migration coefficient. |
| `ci_lower_migration` | number | null | 95 % CI lower bound for migration coefficient. |
| `ci_upper_migration` | number | null | 95 % CI upper bound for migration coefficient. |
| `interaction_effect` | number | null | Interaction coefficient (telomere × migration); null for base model or low‑power. |
| `se_interaction` | number | null | Standard error for interaction coefficient. |
| `ci_lower_interaction` | number | null | 95 % CI lower bound for interaction coefficient. |
| `ci_upper_interaction` | number | null | 95 % CI upper bound for interaction coefficient. |
| `p_value_telomere` | number | null | 0–1; null when low‑power. |
| `p_value_interaction` | number | null | 0–1; null for base model or low‑power. |
| `significance_flag` | boolean | True when `p_value_telomere < α` (α = 0.05). |
| `phylogenetic_lambda` | number | null | Pagel’s λ; null when low‑power. |
| `lambda_ci_lower` | number | null | 95 % CI lower bound for λ. |
| `lambda_ci_upper` | number | null | 95 % CI upper bound for λ. |
| `aic_score` | number | null | Akaike Information Criterion; null when low‑power. |
| `delta_aic` | number | null | ΔAIC vs. base model (interaction model only). |
| `n_species` | integer | Number of species included in the model. |
| `low_power_flag` | boolean | True when n_species < 15 (message issued). |
| `low_power_message` | string | null | `"Low Power: Phylogenetic inference unreliable"` when low‑power; null otherwise. |
| `power_estimate` | number | Simulated power to detect a **standardized regression slope of 0.5 SD** at α = 0.05 for the observed species count; always computed and reported. |
| `delta_aic` | number | null | ΔAIC vs. base model (interaction model only). |

### SensitivityLog
| Field | Type | Description |
|-------|------|-------------|
| `iteration_id` | integer | LOOCV/jackknife iteration index |
| `excluded_unit` | string | Excluded species (LOOCV) or study_id (jackknife) |
| `method` | string | `"LOOCV"` or `"Jackknife"` with logged justification |
| `coefficient_telomere` | number | Refitted telomere coefficient |
| `p_value` | number | Corresponding p‑value |

## Data Flow
1. `01_discover_data.py` → real Dryad DOIs + AnAge/BirdLife availability → `config.yaml`.
2. `02_ingest_data.py` → `data/raw/` (+ SHA‑256 checksums).
3. `03_clean_merge.py` → `data/processed/merged_analysis.csv` (conforms to `dataset.schema.yaml`).
4. `04_fetch_phylogeny.py` → `data/phylogeny/bird_tree.nwk`.
5. `05_fit_pgls_base.py` / `06_fit_pgls_interaction.py` → `results/model_summary.csv` (conforms to `model_output.schema.yaml`).
6. `07_sensitivity.py` → `results/sensitivity_log.csv` (log‑only artifact; no separate schema), `results/power_report.yaml`.
7. `08_visualize.py` → PNGs in `results/`.

Every step writes a `*.sha256` sidecar and updates the state YAML. On data‑retrieval failure the pipeline halts before producing any analysis artifact — **no synthetic data are ever created**.
