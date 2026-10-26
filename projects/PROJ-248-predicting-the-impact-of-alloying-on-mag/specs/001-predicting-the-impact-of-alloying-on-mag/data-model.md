# Data Model: Predicting Saturation Magnetization of Alloys via Public OQMD Data

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **AlloyRecord** | Raw entry from OQMD (the only verified source) | `composition` (string, e.g., `"Fe2Ni"`), `spacegroup` (int), `lattice_parameters` (dict: `a,b,c,alpha,beta,gamma`), `magnetic_moment` (float, µ_B/atom), `source` (`"OQMD"`), `last_updated` (ISO‑8601 timestamp) |
| **FeatureVector** | Numerical representation derived from an `AlloyRecord` | `frac_{element}` (float for each element present), `avg_atomic_radius`, `avg_first_ionization_energy`, `avg_d_electron_count`, `avg_electronegativity`, `avg_bulk_modulus`, `spacegroup`, `a`, `b`, `c`, `alpha`, `beta`, `gamma`, `packing_fraction` |
| **ModelArtifact** | Serialized regression model plus metadata | `target` (`"saturation_magnetization"`), `model_type` (`"RandomForest"` / `"GradientBoosting"`), `hyperparameters` (dict), `training_split_indices` (list of ints), `random_seed` (int), `artifact_hash` (sha256) |
| **PredictionResponse** | JSON output of the CLI prediction service (see `contracts/prediction.schema.yaml`) | `saturation_magnetization` (number), `curie_temperature` (number | null), `confidence_interval` (object with numeric arrays) |

## Schema Definitions

### 1. `AlloyRecord` (CSV representation)

| Column | Type | Required? | Description |
|--------|------|-----------|-------------|
| `composition` | string | Yes | Normalized formula (e.g., `"Fe2Ni"`). |
| `spacegroup` | integer | Yes | International space‑group number. |
| `a` | float | Yes | Lattice constant a (Å). |
| `b` | float | Yes | Lattice constant b (Å). |
| `c` | float | Yes | Lattice constant c (Å). |
| `alpha` | float | Yes | Angle α (degrees). |
| `beta` | float | Yes | Angle β (degrees). |
| `gamma` | float | Yes | Angle γ (degrees). |
| `magnetic_moment` | float | Yes | µ_B per atom (used for saturation‑magnetization modeling). |
| `source` | string | Yes | `"OQMD"`. |
| `last_updated` | string (ISO‑8601) | Yes | Timestamp of the calculation. |
| `metadata` | string (JSON) | No | Placeholder for future extensions. |

### 2. `FeatureVector` (internal NumPy array)

- Shape: `(n_features,)` where `n_features = N_elements + 13` (elemental fractions + 6 crystal descriptors + 7 elemental‑average properties).  
- Order: `[frac_{El1}, …, frac_{ElN}, avg_atomic_radius, avg_first_ionization_energy, avg_d_electron_count, avg_electronegativity, avg_bulk_modulus, spacegroup, a, b, c, alpha, beta, gamma, packing_fraction]`.

### 3. `PredictionResponse` (JSON)

```yaml
type: object
properties:
  saturation_magnetization:
    type: number
    description: "Predicted saturation magnetization in µ_B per atom"
  curie_temperature:
    type: [number, "null"]
    description: "Predicted Curie temperature in Kelvin (null until data available)"
  confidence_interval:
    type: object
    properties:
      saturation_magnetization:
        type: array
        items:
          type: number
        minItems: 2
        maxItems: 2
        description: "[lower, upper] 95 % CI for saturation magnetization"
    required:
      - saturation_magnetization
    additionalProperties: false
required:
  - saturation_magnetization
  - curie_temperature
  - confidence_interval
additionalProperties: false
```

> **Note**: The original specification required both `saturation_magnetization` **and** `curie_temperature`. Because no verified open‑source provides Curie‑temperature values, the `curie_temperature` field will be emitted as `null` with a logged warning. This maintains schema compatibility while transparently indicating the data gap.

## Data Flow Diagram (textual)

1. **Raw download** → `AlloyRecord` CSV (`data/raw_oqmd.csv`).  
2. **Cleaning & deduplication** → `AlloyRecord` CSV (`data/cleaned_oqmd.csv`).  
3. **Feature engineering** (per record) → `FeatureVector` (saved as `data/feature_matrix_saturation.npy`).  
4. **Model training** → `ModelArtifact` (`artifacts/model_saturation.pkl`).  
5. **Prediction service** reads a single‑alloy JSON, builds a `FeatureVector`, loads the model, returns a `PredictionResponse` (with `curie_temperature: null`).  

---



