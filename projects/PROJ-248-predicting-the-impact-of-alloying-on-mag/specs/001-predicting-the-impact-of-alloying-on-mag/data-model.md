# Data Model: Predicting the Impact of Alloying on Magnetic Properties via Public Data

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **AlloyRecord** | Raw entry from a source dataset (OQMD or Materials Project) | `composition` (string, e.g., `"Fe2Ni"`), `spacegroup` (int), `lattice_parameters` (dict: `a,b,c,alpha,beta,gamma`), `magnetic_moment` (float, µ_B/atom, optional), `curie_temperature` (float, K, optional), `source` (`"OQMD"` or `"MaterialsProject"`), `last_updated` (ISO‑8601 timestamp), `metadata` (dict of DFT settings: `functional`, `kpoints`, `pseudopotential`) |
| **FeatureVector** | Numerical representation derived from an `AlloyRecord` | `frac_{element}` (float for each element present in dataset), `avg_atomic_radius`, `avg_first_ionization_energy`, `avg_d_electron_count`, `avg_electronegativity`, `avg_bulk_modulus`, `spacegroup`, `a`, `b`, `c`, `alpha`, `beta`, `gamma`, `packing_fraction`, **optional** `functional_code`, `kpoint_density`, `pseudopotential_id` |
| **ModelArtifact** | Serialized regression model plus metadata | `target` (`"saturation_magnetization"` or `"curie_temperature"`), `model_type` (`"RandomForest"` / `"GradientBoosting"`), `hyperparameters` (dict), `training_split_indices` (list of ints), `random_seed` (int), `artifact_hash` (sha256) |
| **PredictionResponse** | JSON output of the CLI prediction service (see `contracts/prediction.schema.yaml`) | `saturation_magnetization` (number), `curie_temperature` (number), `confidence_interval` (object with two numeric arrays; each array `[lower, upper]`) |

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
| `magnetic_moment` | float | No (required for saturation‑magnetization modelling) | µ_B per atom. |
| `curie_temperature` | float | No (required for Curie‑temperature modelling) | Kelvin. |
| `source` | string | Yes | `"OQMD"` or `"MaterialsProject"`. |
| `last_updated` | string (ISO‑8601) | Yes | Timestamp of the calculation. |
| `metadata` | string (JSON) | No | Serialized DFT settings (`functional`, `kpoints`, `pseudopotential`). |

### 2. `FeatureVector` (internal NumPy array)

- Shape: `(n_features,)` where `n_features = N_elements + 7 + 3` (elemental fractions + 6 crystal descriptors + 3 optional DFT‑metadata features).  
- Order: `[frac_{El1}, …, frac_{ElN}, avg_atomic_radius, avg_first_ionization_energy, avg_d_electron_count, avg_electronegativity, avg_bulk_modulus, spacegroup, a, b, c, alpha, beta, gamma, packing_fraction, functional_code, kpoint_density, pseudopotential_id]`.

### 3. `PredictionResponse` (JSON)

```yaml
type: object
properties:
  saturation_magnetization:
    type: number
    description: "Predicted saturation magnetization in µ_B per atom"
  curie_temperature:
    type: number
    description: "Predicted Curie temperature in Kelvin"
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
      curie_temperature:
        type: array
        items:
          type: number
        minItems: 2
        maxItems: 2
        description: "[lower, upper] 95 % CI for Curie temperature"
    required:
      - saturation_magnetization
      - curie_temperature
    additionalProperties: false
required:
  - saturation_magnetization
  - curie_temperature
  - confidence_interval
additionalProperties: false
```

## Data Flow Diagram (textual)

1. **Raw download** → `AlloyRecord` CSV (`data/raw_oqmd.csv`, `data/raw_mp.csv`).  
2. **Cleaning & deduplication** → `AlloyRecord` CSV (`data/cleaned_oqmd.csv`, `data/cleaned_mp.csv`).  
3. **Feature engineering** (per record) → `FeatureVector` (saved as `data/feature_matrix_{target}.npy`).  
4. **Model training** → `ModelArtifact` (`artifacts/model_{target}.pkl`).  
5. **Prediction service** reads a JSON alloy description, builds a `FeatureVector`, loads the appropriate `ModelArtifact`, returns `PredictionResponse`.

---

