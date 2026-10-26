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
| `phosphorus_concentration` | float | Soil phosphorus (mg kg⁻¹ or ppm). |
| `nitrogen_concentration` | float | Soil nitrogen (mg kg⁻¹ or ppm). |
| `measurement_date` | date | Date of soil sampling. |
| `depth` | float | Sampling depth (cm). |
| `geographic_location` | string | Must match `RootPhenotypeRecord.geographic_location` for merging. |
| `soil_moisture` | float | Optional covariate (may be null). |
| `temperature` | float | Optional covariate (may be null). |
| `elevation` | float | Optional covariate (may be null). |

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
| `data_source_type` | string | `"observational"` after FR‑012 filtering. |
| `sample_size_per_species` | integer | Number of rows for the species after filtering (used for SC‑005). |
| `soil_moisture_missing` | integer | 1 if soil_moisture was imputed, 0 otherwise. |
| `temperature_missing` | integer | 1 if temperature was imputed, 0 otherwise. |
| `elevation_missing` | integer | 1 if elevation was imputed, 0 otherwise. |

## Data Flow Overview
1. **Ingestion** – Load PlantPheno (roots) and a verified MergedDataset (pre‑merged roots + soil) via HuggingFace.  
2. **Merging** – Join on `species` and `geographic_location` using ≤5 km spatial and ≤30 day temporal tolerances; if the merged dataset is used directly, this step is a simple copy.  
3. **Filtering** – Keep observational rows, enforce n ≥ 30 per species, apply FR‑003 missing‑nutrient policy.  
4. **Transformation** – Log‑transform root metrics, z‑score nutrients, impute covariates (with missing‑indicator flags), k‑NN impute remaining nutrients.  
5. **Persistence** – Write the cleaned Parquet file for downstream modeling.  

## Schema Constraints (mirrored in `contracts/dataset.schema.yaml`)
- `species`: required, non‑null string.  
- Root metrics (`root_length`, `branching_density`, `surface_area`): required numbers (already log‑transformed).  
- `phosphorus`, `nitrogen`: numbers **or null** (`nullable: true`).  
- Optional covariates (`soil_moisture`, `temperature`, `elevation`): numbers **or null**; corresponding missing‑indicator flags are required integers (0/1).  
- No additional properties permitted.

---


