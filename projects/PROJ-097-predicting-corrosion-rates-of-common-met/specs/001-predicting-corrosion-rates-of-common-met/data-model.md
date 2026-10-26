# Data Model: Predicting Corrosion Rates of Common Metals  

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **CorrosionRecord** | One observation from a corrosion experiment. | `record_id` (str), `pH` (float), `salinity` (float), `temperature` (float), `composition` (str), `crystal_structure` (optional, str), `corrosion_rate_mm_per_year` (float), `source_id` (str) |
| **InteractionFeature** | Derived variable representing a product of two base predictors. | `name` (str), `definition` (e.g., `"pH * salinity"` or `"pH * composition_Fe"`), `values` (array[float]) |
| **ModelArtifact** | Serialized model together with training metadata. | `model_type` (enum: ["RandomForest", "GradientBoosting"]), `hyperparameters` (dict), `feature_list` (list[str]), `cv_r2` (float), `cv_rmse` (float), `sha256` (str), `created_at` (ISO‑8601) |
| **DatasetMetadata** | Provenance record for each ingested raw dataset. | `doi` (str), `url` (str), `sha256` (str), `downloaded_at` (ISO‑8601), `num_records` (int), `columns_present` (list[str]) |

## File Formats
- **Raw download**: Original CSV/TSV as supplied (unchanged).  
- **Cleaned data**: `cleaned_dataset.csv` – required columns present, no nulls in those columns, numeric predictors standardized (mean = 0, std = 1).  
- **Feature matrix**: `features.parquet` – includes standardized numeric predictors, one‑hot encoded composition columns, and engineered interaction features.  
- **Feature list**: `feature_names.txt` – plain‑text file, one feature name per line, matching the column order in `features.parquet`.  
- **Model artifact**: `model_artifact.yaml` – conforms to `contracts/model_artifact.schema.yaml`.  
- **Metadata**: `metadata/dataset.yaml` – conforms to `contracts/cleaned_dataset.schema.yaml`.  

## Relationships
- Each `CorrosionRecord` belongs to a `source_id` (experimental batch).  
- `InteractionFeature`s are derived from base columns of `CorrosionRecord` (numeric env variables and one‑hot composition columns).  
- `ModelArtifact` references the exact `feature_list` used for training; this list must be a subset of columns in `features.parquet`.  

## Notes on Composition Encoding
Material composition is treated as a categorical variable and one‑hot encoded during preprocessing (FR‑008). Interaction features are formed **between each numeric environmental variable (pH, salinity, temperature) and each one‑hot composition column**, as well as between pairs of environmental variables. No numeric `composition_ratio` field is assumed; all composition information is captured via the one‑hot encoding.

---

