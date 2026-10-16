# Data Model: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview
All artifacts are versioned, checksummed, and validated against JSON schemas in `contracts/`. Raw inputs remain immutable; each transformation yields a new file.

## 2. Raw Data (`data/raw/`)
| Field | Type | Description |
|---|---|---|
| `material_id` | string | Unique identifier (e.g., `mp-12345`). |
| `structure` | string (CIF) or dict | Pymatgen‑compatible structure representation. |
| `elastic_tensor` | list[float] | Six independent Voigt components (C1*, C12, C13, C33, C44, C66), where C1* denotes the normal component associated with the first principal direction. |
| `formula` | string | Chemical formula. |
| `space_group` | integer | Space‑group number. |
| `is_2d` | boolean | Flag set by `pymatgen` dimensionality check. |

The loader validates presence and types; missing required columns cause an immediate abort.

## 3. Processed Data (`data/processed/`)

### 3.1 `graphs_v1.parquet`
Schema: `contracts/dataset_schema.schema.yaml`.  
Each row contains:
- `material_id`
- `num_nodes`, `num_edges`
- `node_features` (list of numeric vectors)
- `edge_index` (list of `[src, dst]` pairs)
- `edge_features`
- Targets: `target_young`, `target_shear`, `target_poisson`
- `family` (for downstream split/analysis)

### 3.2 `split_indices.json`
```json
{
  "train_ids": ["..."],
  "val_ids": ["..."],
  "test_ids": ["..."],
  "train_families": ["..."],
  "val_families": ["..."],
  "test_families": ["..."],
  "split_seed": 42,
  "timestamp": "2026-10-16T12:00:00Z"
}
```
Written atomically (temp file → `os.replace`). Validated by `contracts/split_indices.schema.yaml` (implicit, simple JSON).

### 3.3 `model_v1.pt`
Torch checkpoint containing:
- `state_dict`
- `hyperparameters`
- `seed`
- `target_normalization` (mean & std)
- `DISCLAIMER_TEXT` (imported from `disclaimer_template.py`)

## 4. Results (`data/results/`)

| File | Purpose | Schema |
|---|---|---|
| `training_logs.json` | Epoch‑wise loss, peak memory, device, disclaimer flag | `contracts/training_logs.schema.yaml` (implicit, unit tests) |
| `split_validation.json` | Verification of family‑disjoint split | `contracts/split_validation.schema.yaml` |
| `generalization_metrics.json` | Per‑property MAPE, RMSE, bootstrap CI, baseline comparison, PASS/FAIL | `contracts/results_schema.schema.yaml` |
| `predictions.json` | Test‑set true vs. predicted values + per‑record errors | `contracts/predictions.schema.yaml` |
| `inference_benchmark.json` | Average & max inference time, PASS/FAIL | `contracts/inference_benchmark.schema.yaml` (implicit) |
| `feature_importance_report.md` | Ranked descriptors, Integrated Gradients attributions, SHAP magnitudes, VIF screening notes | No schema (markdown). |
| `constitution_title_audit.json` | Audit status for forbidden terminology | `contracts/constitution_audit_schema.schema.yaml` |
| `power_analysis.json` | Estimated statistical power for detecting [deferred] MAPE reduction | No schema (JSON for internal gate). |
| `composition_gnn_metrics.json` | Baseline GNN (composition‑only) performance metrics | No schema (used for internal comparison). |

## 5. Data Flow Diagram
1. **Loader** → `data/raw/` (checksum)  
2. **Graph Builder** → `data/processed/graphs_v1.parquet`  
3. **Split Generator** → `data/processed/split_indices.json`  
4. **Splitter (validation)** → `data/results/split_validation.json`  
5. **Training** → `data/processed/model_v1.pt`, `data/results/training_logs.json`  
6. **Evaluation** → `data/results/predictions.json`, `data/results/generalization_metrics.json`  
7. **Baseline GNN** → `data/results/composition_gnn_metrics.json`  
8. **Inference Benchmark** → `data/results/inference_benchmark.json`  
9. **Feature Importance** → `data/results/feature_importance_report.md` (Integrated Gradients + SHAP + VIF)  
10. **Power Analysis** → `data/results/power_analysis.json`  
11. **Constitution Audit** → `data/results/constitution_title_audit.json`  

All steps are orchestrated by `code/main_pipeline.py` in the order above.

## 6. Multicollinearity & Feature‑Importance Workflow
- **VIF Screening**: Before any importance computation, variance inflation factors are calculated for all structural descriptors; any descriptor with VIF > 5 is excluded.  
- **Integrated Gradients**: Provides node‑ and edge‑level attribution scores (100 Monte‑Carlo samples).  
- **SHAP (KernelExplainer)**: Provides global descriptor importance on a 200‑sample subset.  
- **Descriptor Selection**: Only descriptors that (i) survive VIF screening and (ii) rank in the top‑3 by both IG magnitude and mean absolute SHAP magnitude are reported (fulfilling SC‑005).  
