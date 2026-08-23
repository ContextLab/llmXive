# Data Model: Predicting HEA Yield Strength

The pipeline operates on a set of well‑defined entities. Each entity is described below with its attributes, types, and relationships. The schemas in `contracts/` are derived directly from these definitions.

## Entities

### 1. `hea_composition`
*Represents a single alloy entry as stored in the raw dataset.*

| Attribute | Type | Description |
|-----------|------|-------------|
| `alloy_id` | string | Unique identifier for the alloy (e.g., “HEA_001”). |
| `composition` | object (mapping) | Keys are element symbols (e.g., `"Al"`), values are atomic fractions (float, sum = 1). |
| `yield_strength` | number (float) | Experimentally measured yield strength in MPa. |
| `source_checksum` | string | SHA‑256 checksum of the raw CSV row (for reproducibility). |

### 2. `descriptor_set`
*Deterministic descriptors computed from `hea_composition`.*

| Attribute | Type | Description |
|-----------|------|-------------|
| `alloy_id` | string | Foreign key to `hea_composition`. |
| `mixing_entropy` | number | Configurational entropy (ΔS<sub>mix</sub>) (J mol⁻¹ K⁻¹). |
| `atomic_size_mismatch` | number | δ = √∑cᵢ(1 − rᵢ/ r̄)² (dimensionless). |
| `electronegativity_variance` | number | Δχ = √∑cᵢ(χᵢ − χ̄)² (dimensionless). |
| `valence_electron_concentration` | number | VEC = ∑cᵢ·VECᵢ (electrons per atom). |
| `melting_temp_variance` | number | σ_Tm = √∑cᵢ(Tmᵢ − Tm̄)² (K²). |
| `checksum` | string | SHA‑256 of the descriptor row. |

### 3. `model_artifact`
*Serialized Random Forest model and training metadata.*

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_path` | string | Path to the pickled model (`output/model.pkl`). |
| `hyperparameters` | object | Dictionary of RF hyperparameters (e.g., `n_estimators`, `max_depth`). |
| `cv_folds` | integer | Number of cross‑validation folds used (5). |
| `random_seed` | integer | Seed governing data split and model randomness. |
| `training_checksum` | string | SHA‑256 of the training descriptor file. |

### 4. `manifest`
*Reproducibility manifest required by FR‑007.*

| Attribute | Type | Description |
|-----------|------|-------------|
| `pipeline_version` | string | Semantic version of the pipeline code (e.g., “1.0.0”). |
| `run_timestamp` | string (ISO‑8601) | UTC timestamp of pipeline execution. |
| `random_seeds` | object | Keys: `data_split`, `model`, `bootstrap`; values: integers. |
| `software_versions` | object | Mapping of package name → version (as pinned in `requirements.txt`). |
| `data_checksums` | object | Mapping of dataset file name → SHA‑256. |
| `artifact_checksums` | object | Mapping of output artifact name → SHA‑256. |
| `git_commit` | string | Full commit SHA of the repository at run time. |

### 5. `evaluation_metrics`
*Performance metrics on the held‑out test set.*

| Attribute | Type | Description |
|-----------|------|-------------|
| `r2` | number | Coefficient of determination (R²). |
| `pearson_r` | number | Pearson correlation coefficient. |
| `pearson_p` | number | Two‑tailed p‑value for Pearson r. |
| `r2_ci` | array[number] | 95 % bootstrap CI for R² (two values). |
| `r_ci` | array[number] | 95 % bootstrap CI for Pearson r (two values). |
| `runtime_seconds` | integer | Total pipeline runtime. |
| `checksum` | string | SHA‑256 of the JSON file. |

### 6. `permutation_importance`
*Permutation importance scores and significance.*

| Attribute | Type | Description |
|-----------|------|-------------|
| `feature_name` | string | Descriptor name (e.g., “mixing_entropy”). |
| `importance_mean` | number | Mean decrease in score across permutations. |
| `importance_std` | number | Standard deviation across permutations. |
| `p_value_raw` | number | Non‑parametric permutation test p‑value (pre‑correction). |
| `p_value_corrected` | number | Bonferroni‑adjusted p‑value. |
| `significant` | boolean | True if corrected p < 0.05. |
| `checksum` | string | SHA‑256 of the row. |

## ER Relationships
- `descriptor_set.alloy_id` → `hea_composition.alloy_id` (one‑to‑one).  
- `model_artifact` references the descriptor file used for training.  
- `evaluation_metrics` is linked to the specific `model_artifact` via the same `run_timestamp`.  
- `permutation_importance` rows are associated with a single `model_artifact`.

All entities are immutable after creation; any transformation writes a new file with its own checksum, satisfying Constitution Principle III.

## Contract Coverage
The following contract schemas correspond to the entities above and are exercised by the pipeline:

- `dataset.schema.yaml` → raw `hea_composition` rows  
- `descriptor.schema.yaml` → `descriptor_set` records  
- `hea_composition.schema.yaml` → processed composition with descriptors  
- `hea_schema.schema.yaml` → enriched descriptor schema used for downstream analysis  
- `importance.schema.yaml` → `permutation_importance` output  
- `metrics.schema.yaml` → `evaluation_metrics` output  
- `manifest` fields are validated against a dedicated manifest schema (implicit in implementation).  
