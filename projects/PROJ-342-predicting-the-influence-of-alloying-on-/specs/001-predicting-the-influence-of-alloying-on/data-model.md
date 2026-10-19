# Data Model: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Entity Definitions

### CompositionRecord
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `string` (UUID) | Unique identifier. |
| `family` | `string` | Alloy family (e.g., “Zr‑based”). |
| `elements` | `object` (element → fraction) | Atomic fractions; at least two entries. |
| `tg_value` | `number` (K) | Glass transition temperature. |
| `source` | `string` (DOI) | Originating dataset DOI. |
| `status` | `string` (`valid` / `dropped_missing_tg` / `dropped_incomplete_composition`) | Validation outcome. |

### DescriptorSet
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `string` (FK) | Links to `CompositionRecord`. |
| `radius_mismatch` | `number` | Δr descriptor. |
| `electronegativity_diff` | `number` | Δχ descriptor. |
| `vec` | `number` | Valence Electron Concentration. |
| `weighted_mean_radius` | `number` | Diagnostic only (FR‑002). |
| `vif_radius` | `number` | VIF for radius mismatch (post‑remediation). |
| `vif_electro` | `number` | VIF for electronegativity diff. |
| `vif_vec` | `number` | VIF for VEC. |

### ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `artifact_id` | `string` (UUID) | Unique model identifier. |
| `model_type` | `string` | `"GradientBoostingRegressor"`. |
| `hyperparameters` | `object` | Hyper‑parameter dict used for training. |
| `performance_metrics` | `object` | `{ "r2_mean": number, "r2_std": number, "mae_mean": number }`. |
| `feature_importances` | `object` | Feature → importance score. |
| `sensitivity_variance` | `number` | σ² of R² across `max_depth` sweep (FR‑006). |
| `fdr_corrected_pvalues` | `object` | Predictor‑pair → Bonferroni‑adjusted p‑value (FR‑008). |
| `associational_statement` | `string` | Must equal `"These findings are associational only"`. |
| `collinearity_flag` | `boolean` | True if any VIF > 5 after remediation. |

## 2. Data Flow

1. **Raw ingestion** (`data/raw/`) → `ingest.py` → `data/processed/cleaned_data.csv` (validated against `dataset.schema.yaml`).  
2. **Descriptor computation** → `descriptors.py` → `data/processed/descriptors.csv`.  
3. **Model training** → `train.py` → `artifacts/models/best_model.pkl`.  
4. **Statistical analysis** → `analyze.py` → `artifacts/metrics/stats.json` (validated against `artifact.schema.yaml`).  
5. **Report generation** → `report.py` → `paper/report.md`.

## 3. Constraints

- Records missing `tg_value` or with incomplete `elements` are dropped (FR‑001).  
- No imputation; listwise deletion only.  
- Descriptors are computed in native units; no scaling needed for GBM.  
- `weighted_mean_radius` never used as a predictor (FR‑002).  
- VIF remediation performed before model fitting (FR‑007).
