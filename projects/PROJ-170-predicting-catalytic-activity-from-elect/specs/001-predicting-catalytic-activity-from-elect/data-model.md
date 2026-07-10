# Data Model: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## 1. Entity-Relationship Overview

The data model consists of three primary stages: **Raw Ingestion**, **Aligned/Processed**, and **Model Output**.

### 1.1 Raw Data Entities
- **OC20Entry**: Raw DFT structure data.
  - Keys: `id`, `atoms`, `energy`, `forces`, `energy_change`.
  - Derived: `composition` (from atoms), `surface_facet` (from structure).

### 1.2 Processed Data Entities
- **CatalystEntry**: Unified record for modeling.
  - **Attributes**:
    - `catalyst_id`: Unique identifier (hash of composition + facet).
    - `composition`: String (e.g., "Cu2O").
    - `surface_facet`: String (e.g., "(111)").
    - `d_band_center`: Float (eV) (derived or imputed).
    - `adsorption_energy`: Float (eV) (derived or imputed).
    - `energy_change`: Float (eV) (DFT reaction energy, target).
    - `imputation_flag`: Boolean (True if KNN imputed).
    - `exclusion_reason`: String (if excluded from training).

### 1.3 Model Output Entities
- **ModelMetrics**: Performance statistics.
  - `model_type`: String ("XGBoost" or "Linear").
  - `r_squared`: Float.
  - `mean_absolute_error`: Float.
  - `pearson_r`: Float.
  - `t_test_p_value`: Float.
  - `alignment_rate`: Float (SC-002).
- **FeatureImportance**: SHAP results.
  - `descriptor_name`: String.
  - `mean_absolute_shap_value`: Float.
  - `rank`: Integer.

## 2. Schema Definitions

### 2.1 Aligned Dataset Schema (`aligned_dataset.csv`)
| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `catalyst_id` | String | Unique ID | Primary Key |
| `composition` | String | Chemical formula | Not Null |
| `surface_facet` | String | Crystal facet | Not Null |
| `d_band_center` | Float | d-band center (eV) | Not Null (imputed if needed) |
| `adsorption_energy` | Float | Adsorption energy (eV) | Not Null (imputed if needed) |
| `energy_change` | Float | Reaction energy (eV) | Not Null (target) |
| `imputation_flag` | Boolean | True if KNN used | Default False |
| `exclusion_reason` | String | Reason for exclusion | Optional |

### 2.2 Output Metrics Schema (`metrics.json`)
```json
{
  "xgboost": {
    "r_squared": 0.0,
    "mae": 0.0,
    "pearson_r": 0.0
  },
  "linear_baseline": {
    "r_squared": 0.0,
    "mae": 0.0,
    "pearson_r": 0.0
  },
  "comparison": {
    "test_type": "t-test",
    "p_value": 0.0,
    "significant": false
  },
  "alignment_rate": 0.0,
  "top_5_descriptors": [
    {"name": "string", "shap_value": 0.0}
  ]
}
```

## 3. Data Transformation Logic

1. **Alignment**: Filter OC20 entries by `composition` and `surface_facet`.
2. **Derivation**: Attempt to derive `d_band_center` and `adsorption_energy` from OC20 native data or adsorption energies.
3. **Filtering**: Remove rows where `energy_change` is missing.
4. **Imputation**:
   - Generate Morgan fingerprints for surface slabs.
   - Compute Euclidean distance in fingerprint space.
   - Select k=5 nearest neighbors.
   - If k < 5, set `exclusion_reason` = "Insufficient neighbors" and exclude from training.
   - Else, fill with mean of neighbors.
5. **Scaling**: Apply `StandardScaler` to all numeric features (excluding `energy_change`).

## 4. Data Integrity & Hygiene

- **Checksums**: All raw files in `data/raw/` must have a `.sha256` file.
- **Immutability**: Raw files are never modified. All transformations write to `data/processed/`.
- **PII**: No personal data is involved.

## projects/PROJ-170-predicting-catalytic-activity-from-elect/specs/001-predicting-catalytic-activity-from-elect/quickstart.md