# Data Model: Predicting Plant Root Architecture from Soil Nutrient Availability

## Entity Definitions

### RootPhenotypeRecord
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Scientific name of the plant species (non‑null). |
| `root_length` | float | Total root length (cm). |
| `branching_density` | float | Branches per unit length. |
| `surface_area` | float | Root surface area (cm²). |
| `geographic_location` | string | Latitude/Longitude or site identifier. |
| `experimental_id` | string | Unique experiment identifier. |
| `data_source_type` | string | `"observational"` or `"experimental"` (used for FR‑012). |

### SoilNutrientRecord
| Field | Type | Description |
|-------|------|-------------|
| `phosphorus_concentration` | float | Soil P (mg kg⁻¹ or ppm). |
| `nitrogen_concentration` | float | Soil N (mg kg⁻¹ or ppm). |
| `measurement_date` | date | Date of soil sampling. |
| `depth` | float | Sampling depth (cm). |
| `geographic_location` | string | Must match `RootPhenotypeRecord.geographic_location` for merging. |

### MergedDataset (post‑processing)
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Plant species (non‑null). |
| `root_length` | float | **Log‑transformed** total length. |
| `branching_density` | float | **Log‑transformed** branching density. |
| `surface_area` | float | **Log‑transformed** surface area. |
| `phosphorus` | float | **Z‑scored** phosphorus concentration; may be null if soil data unavailable. |
| `nitrogen` | float | **Z‑scored** nitrogen concentration; may be null if soil data unavailable. |
| `soil_moisture` | float | Optional covariate (may be null). |
| `temperature` | float | Optional covariate (may be null). |
| `elevation` | float | Optional covariate (may be null). |
| `data_source_type` | string | `"observational"` (after FR‑012 filtering). |
| `sample_size_per_species` | integer | Number of rows for the species after filtering (used for SC‑005). |

## Data Flow Overview
1. **Ingestion** (`T007`, `T008`) – Load a verified merged dataset via HuggingFace.  
2. **Filtering** (`T009`‑`T010`) – Keep observational rows, enforce n ≥ 30 per species.  
3. **Missing‑Data Logic** (`T011`) – Apply FR‑025 species‑level missing‑nutrient policy (impute or exclude).  
4. **Transformation** (`T012`‑`T014`) – Log‑transform roots, z‑score nutrients, two‑stage imputation.  
5. **Persistence** (`T015`) – Write Parquet file for downstream steps.  

## Schema Constraints (mirrored in `contracts/dataset.schema.yaml`)
- `species`: required, non‑null string.  
- Root metrics: required numbers (already log‑transformed).  
- `phosphorus`, `nitrogen`: numbers **or null** (`nullable: true`).  
- Optional covariates may be null.  
- No additional properties permitted.
