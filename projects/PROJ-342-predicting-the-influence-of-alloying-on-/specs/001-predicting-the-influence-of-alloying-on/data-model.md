# Data Model: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Entity Definitions

### CompositionRecord
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `string` (UUID) | Unique identifier for the synthetic record. |
| `family` | `string` | Alloy family (dominant element ≥ 40 %). |
| `elements` | `object` (element → fraction) | Atomic fractions; sum ≈ 1, at least two elements. |
| `tg_value` | `number` (K) | Synthetic glass transition temperature (300–800 K). |
| `source` | `string` | Fixed value `"synthetic"`. |
| `status` | `string` (`valid`) | Validation outcome (all rows are valid). |

### DescriptorSet
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `string` (FK) | Links to `CompositionRecord`. |
| `radius_mismatch` | `number` | Δr descriptor (FR‑002). |
| `electronegativity_diff` | `number` | Δχ descriptor (FR‑002). |
| `vec` | `number` | Valence Electron Concentration (FR‑002). |
| `weighted_mean_radius` | `number` | Diagnostic only; never used as predictor. |
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
| `feature_importances` | `object` | Feature → importance score mapping. |
| `sensitivity_variance` | `number` | σ² of R² across `max_depth` sweep (FR‑006). |
| `fdr_corrected_pvalues` | `object` | Predictor‑pair → Bonferroni‑adjusted p‑value (FR‑008). |
| `associational_statement` | `string` | Must equal `"These findings are associational only"`. |
| `collinearity_flag` | `boolean` | True if any VIF > 5 after remediation (FR‑007). |

## 2. Data Flow

1. **Synthetic generation** (`code/generate_synthetic.py`) → `data/raw/synthetic_mg.csv` (validated against `contracts/dataset.schema.yaml`).  
2. **Ingestion & cleaning** (`code/ingest.py`) → `data/processed/cleaned_data.csv`.  
3. **Descriptor computation** (`code/descriptors.py`) → `data/processed/descriptors.csv`.  
4. **Model training** (`code/train.py`) → `artifacts/models/best_model.pkl`.  
5. **Statistical analysis** (`code/analyze.py`) → `artifacts/metrics/stats.json` (validated against `contracts/artifact.schema.yaml`).  
6. **Report generation** (`code/report.py`) → `paper/report.md` (includes figures and the required associational statement).

## 3. Constraints

- All records must contain `tg_value` and a complete `elements` mapping; otherwise they are dropped (FR‑001).  
- No imputation; only listwise deletion.  
- `weighted_mean_radius` is never used as a predictor (FR‑002).  
- VIF remediation occurs before model fitting (FR‑007).  
- All random processes use fixed seeds (`np.random.seed(42)`, `random_state=42`).  

---
