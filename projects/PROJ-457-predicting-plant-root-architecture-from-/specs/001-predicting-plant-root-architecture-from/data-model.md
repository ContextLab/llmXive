# Data Model: Predicting Plant Root Architecture from Soil Nutrient Availability

## Entity Definitions

### RootPhenotypeRecord
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Scientific name of the plant species (non‑null). |
| `root_length` | float | Total root length (cm). |
| `branching_density` | float | Branches per unit length. |
| `surface_area` | float | Root surface area (cm²). |
| `geographic_location` | string | Latitude/Longitude or site code. |
| `experimental_id` | string | Unique experiment identifier. |
| `data_source_type` | string | `"observational"` or `"experimental"` (used for FR‑012). |

### SoilNutrientRecord
| Field | Type | Description |
|-------|------|-------------|
| `phosphorus_concentration` | float | Soil P (mg kg⁻¹ or ppm). |
| `nitrogen_concentration` | float | Soil N (mg kg⁻¹ or ppm). |
| `measurement_date` | date | Date of soil sampling. |
| `depth` | float | Sampling depth (cm). |
| `geographic_location` | string | Must match `RootPhenotypeRecord` location for merging. |

### MergedDataset (post‑processing)
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Plant species (non‑null). |
| `root_length` | float | **Log‑transformed** total length. |
| `branching_density` | float | **Log‑transformed** branching density. |
| `surface_area` | float | **Log‑transformed** surface area. |
| `phosphorus` | float | **Z‑scored** P; may be null if soil data unavailable. |
| `nitrogen` | float | **Z‑scored** N; may be null if soil data unavailable. |
| `data_source_type` | string | `"observational"` (after FR‑012 filtering). |
| `sample_size_per_species` | integer | Count of rows for the species (computed for SC‑005). |

## Data Flow Overview
1. **Ingestion** (`T006`): Load PlantPheno (and optionally merged datasets) via HuggingFace.  
2. **Merging** (`T007`‑`T008`): Attempt geographic join with ISRIC; if unavailable, use verified merged dataset or fall back to root‑only.  
3. **Filtering** (`T010`): Remove experimental rows and species with < 20 observations.  
4. **Transformation** (`T011`‑`T012`): Log‑transform roots, z‑score nutrients.  
5. **Missing‑Data Logic** (`T013`‑`T014`): Exclude rows lacking both nutrients; KNN impute remaining missing values.  
6. **Storage** (`T015`): Write Parquet to `data/processed/merged_dataset.parquet`.  

## Schema Constraints (mirrored in `contracts/dataset.schema.yaml`)
- `species`: required, non‑null string.  
- Root metrics: required numbers (post‑log).  
- Nutrient columns: numbers **or null** (allowed when soil data missing).  
- No additional properties permitted.

---
