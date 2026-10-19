# Data Model: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Entity Definitions

### CompositionRecord
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `string` (UUID) | Unique identifier for the record. |
| `family` | `string` | Alloy family (dominant element ≥ 40 %). |
| `elements` | `object` (element → fraction) | Atomic fractions; sum ≈ 1, at least two elements. |
| `tg_value` | `number` (K) | Glass transition temperature (300–800 K). |
| `source` | `string` | DOI of the source dataset. |
| `status` | `string` (`valid`) | Validation outcome (all rows are valid after `ingest.py`). |

### DescriptorSet
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `string` (FK) | Links to `CompositionRecord`. |
| `radius_mismatch` | `number` | Δr descriptor (FR‑002). |
| `electronegativity_diff` | `number` | Δχ descriptor (FR‑002). |
| `vec` | `number` | Valence Electron Concentration (FR‑002). |
| `weighted_mean_radius` | `number` | Diagnostic only; never used as predictor. |
| `vif_radius` | `number` | VIF for radius mismatch (computed for diagnostics). |
| `vif_electro` | `number` | VIF for electronegativity difference (computed for diagnostics). |
| `vif_vec` | `number` | VIF for VEC (computed for diagnostics). |

### ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `artifact_id` | `string` (UUID) | Unique model identifier. |
| `model_type` | `string` | `"GradientBoostingRegressor"`. |
| `hyperparameters` | `object` | Hyper‑parameter dict used for training (grid‑search selection). |
| `performance_metrics` | `object` | `{ "r2_mean": number, "r2_std": number, "mae_mean": number }`. |
| `feature_importances` | `object` | Mapping `feature → importance` (bootstrapped mean). |
| `sensitivity_variance` | `number` | σ² of R² across `max_depth` sweep (FR‑006). |
| `associational_statement` | `string` | Must be exactly `"These findings are associational only"` (FR‑004). |
| `collinearity_flag` | `boolean` | `true` if any predictor has VIF > 5 (FR‑007 flag). |
| `correlations` | `object` | Predictor‑pair → `{ "pearson": number, "spearman": number, "p_raw": number, "p_adj": number }`. |
| `feature_importance_ci` | `object` | Feature → `{ "lower": number, "upper": number }` (95 % CI). |

## 2. Data Flow Diagram

1. **Dataset acquisition** (`code/download_dataset.py`) → `data/raw/metalic_glass_raw.csv` (downloaded only).  
2. **Ingestion & cleaning** (`code/ingest.py`) → `data/processed/cleaned_data.csv`.  
3. **Descriptor computation** (`code/descriptors.py`) → `data/processed/descriptors.csv`.  
4. **Model training** (`code/train.py`) → `artifacts/models/best_model.pkl`.  
5. **Statistical analysis** (`code/analyze.py`) → `artifacts/metrics/stats.json` (validated against `contracts/artifact.schema.yaml`).  
6. **Report generation** (`code/report.py`) → `paper/report.md` (figures derived from the stored artifacts).

## 3. Constraints & Guarantees

- **Missing data**: Any record lacking `tg_value` or a complete `elements` mapping is dropped during ingestion (FR‑001). No imputation is performed.  
- **Predictor set**: Only `radius_mismatch`, `electronegativity_diff`, and `vec` are ever passed to the model; `weighted_mean_radius` is strictly diagnostic (FR‑002).  
- **Collinearity**: VIF is computed for the three predictors; any VIF > 5 is recorded in `collinearity_flag` but **no predictor is removed** (FR‑007).  
- **Randomness**: All stochastic processes use fixed seeds (`np.random.seed(42)`, `random_state=42`).  
- **Reproducibility**: Every artifact is written to disk and validated against a JSON/YAML schema; the exact file paths are hard‑coded in the pipeline.  

---
