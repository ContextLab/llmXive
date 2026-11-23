# Data Model: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase‑Change Materials

## Overview
All data artifacts are versioned, checksum‑protected, and described by JSON/YAML schemas located in `contracts/`. The model below defines the expected columns for each stage.

### 1. Raw PCM Data (`data/raw/pcm.parquet`)
| Column | Type | Description |
|--------|------|-------------|
| `material_id` | string | Unique identifier (e.g., formula or database ID). |
| `composition` | string | Chemical formula (e.g., `BaTiO3`). |
| `latent_heat_J_per_g` | float | Measured latent heat of fusion (J/g). |
| `melting_point_K` | float | Melting temperature (Kelvin). |
| `heat_capacity_J_per_mol_K` | float | Heat capacity at constant pressure (J · mol⁻¹ · K⁻¹). |
| `source` | string | `"literature"` or `"computed"` flag. |
| `structure_id` (optional) | string | Identifier for an associated crystal structure (if available). |

### 2. Elemental Feature Table (`data/processed/elemental_features.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `material_id` | string | FK to raw data. |
| `avg_atomic_number` | float | Mean atomic number of constituent elements. |
| `avg_electronegativity` | float | Mean Pauling electronegativity. |
| `avg_atomic_radius` | float | Mean covalent radius (pm). |
| `std_atomic_number` | float | Standard deviation of atomic numbers (captures compositional diversity). |
| … (additional aggregated elemental stats) | | |
| `has_structure` | int (0/1) | Indicator whether a CIF was found in the OMDB structure repository. |

### 3. Graph Feature Table (`data/processed/graph_features.parquet`) *optional*
| Column | Type | Description |
|--------|------|-------------|
| `material_id` | string | FK to raw data. |
| `graph_adj_matrix` | binary (npz) | Sparse adjacency matrix of the crystal graph. |
| `node_features` | binary (npz) | Node attribute matrix (e.g., element one‑hot). |
| `graph_descriptor_X` | float | Pre‑computed graph‑level descriptor (e.g., packing density). |

*Rows lacking a structure are omitted from this file; a log (`data/logs/missing_structures.log`) records their IDs. The `has_structure` flag in the merged dataset captures this missingness for modeling.*

### 4. Merged Full Dataset (`data/processed/full_dataset.csv`)
| Column | Type | Description |
|--------|------|-------------|
| All columns from **Elemental Feature Table** | | |
| All columns from **Graph Feature Table** (if present) | | |
| `latent_heat_J_per_g` | float | Target (continuous). |
| `phase_change_label` | int (0/1) | Binary label based on threshold (FR‑008). |
| `split` | string | `"train"`, `"val"`, or `"test"` (stratified). |
| `has_structure` | int (0/1) | Propagated from elemental table. |

### 5. Model Result (`data/results/model_result.json`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
required: [model_name, parameters, metrics, feature_importances]
properties:
  model_name:
    type: string
  parameters:
    type: object
    description: "Hyper‑parameters passed to the estimator."
  metrics:
    type: object
    required: [r2, mae, rmse]
    properties:
      r2:
        type: number
      mae:
        type: number
      rmse:
        type: number
  feature_importances:
    type: array
    items:
      type: object
      required: [feature, importance]
      properties:
        feature:
          type: string
        importance:
          type: number
```

### 6. Symbolic Regression Output (`data/results/pysr_formulas.json`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
required: [formulas, best_r2, runtime_seconds]
properties:
  formulas:
    type: array
    items:
      type: string
  best_r2:
    type: number
  runtime_seconds:
    type: number
```

### 7. Sensitivity Sweep Report (`data/results/threshold_sweep.json`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
required: [label_thresholds, metrics_by_threshold]
properties:
  label_thresholds:
    type: array
    items:
      type: number
  metrics_by_threshold:
    type: object
    additionalProperties:
      type: object
      required: [r2, mae, false_positive_rate, false_negative_rate]
      properties:
        r2:
          type: number
        mae:
          type: number
        false_positive_rate:
          type: number
        false_negative_rate:
          type: number
```

### 8. External Validation Report (`data/results/external_validation.json`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
required: [top20_accuracy, overall_r2, notes]
properties:
  top20_accuracy:
    type: number
    description: "Proportion of the top‑20 literature PCMs correctly ranked by the symbolic rule."
  overall_r2:
    type: number
  notes:
    type: string
```

All schemas are stored under `contracts/` (see `contracts/target_decision.schema.yaml` for the binary‑label schema).
