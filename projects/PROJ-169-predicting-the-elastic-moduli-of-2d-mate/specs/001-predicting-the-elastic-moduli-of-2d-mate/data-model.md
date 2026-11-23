# Data Model: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview
All artifacts are versioned, checksummed, and validated against JSON/YAML schemas in `contracts/`. Raw inputs are immutable; each transformation writes a new file with documented provenance.

## 2. Raw Data (`data/raw/`)
- **File**: `raw_dataset.parquet` (downloaded via Matminer).  
- **Checksum**: SHA‑256 recorded in `data/raw/metadata.json`.  
- **Required columns** (validated in `src/data/loader.py`):

| Field | Type | Description |
|---|---|---|
| `material_id` | string | Unique identifier (e.g., `mp-12345`). |
| `structure` | string | CIF representation of the crystal structure. |
| `elastic_tensor` | list[float] | Six Voigt components `[C11, C12, C22, C66, C13, C33]`. |
| `formula` | string | Chemical formula (e.g., `MoS2`). |
| `space_group` | integer | Space‑group number. |
| `is_2d` | boolean | Flag indicating the material is two‑dimensional. |

## 3. Processed Data (`data/processed/`)

### 3.1 `graphs_v1.parquet` (schema `contracts/dataset_schema.yaml`)
Each row contains:
- `material_id`
- `num_nodes`, `num_edges`
- `node_features` (5‑dimensional array per node)
- `edge_index` (source‑target pairs)
- `edge_features` (2‑dimensional per edge)
- `target_young`, `target_shear`, `target_poisson`
- `family` (space‑group + stoichiometry)
- Full 6‑component elastic tensor
- `eligible` flag (True if the four in‑plane components are finite).

### 3.2 `split_indices.json` (schema `contracts/split_indices_schema.yaml`)
Contains deterministic train/val/test splits:
```json
{
  "train_ids": [...],
  "val_ids": [...],
  "test_ids": [...],
  "train_families": [...],
  "val_families": [...],
  "test_families": [...],
  "split_seed": 42,
  "timestamp": "2026-10-25T12:00:00Z"
}
```

### 3.3 `model_v1.pt`
Torch checkpoint with:
- `state_dict`
- `hyperparameters`
- `seed`
- `target_normalization`
- Embedded `DISCLAIMER_TEXT` from `code/utils/disclaimer_template.py`.

## 4. Results (`data/results/`)

| File | Purpose | Schema |
|---|---|---|
| `constitution_title_audit.json` | Terminology audit (FR‑006/FR‑009) | `contracts/constitution_audit_schema.yaml` |
| `training_logs.json` | Epoch losses, peak memory, 5‑fold CV stats, MEGNet benchmark flag, disclaimer | `contracts/training_logs_schema.yaml` |
| `split_validation.json` | Validation of family disjointness and split sizes | `contracts/split_validation_schema.yaml` |
| `generalization_metrics.json` | Surrogate & baseline metrics, relative reductions, statistical significance, intra/inter‑family MAPE, inference timing, SC gates | `contracts/results_schema.yaml` |
| `predictions.json` | True vs. predicted values for test set, per‑record errors | `contracts/predictions_schema.yaml` |
| `feature_importance_report.md` | Ranked structural descriptors, permutation deltas, SHAP values, statistical tests (no schema). |
| `model_v1.pt` | Saved model weights (binary torch file). |
| `split_indices.json` | Already listed under Processed Data. |
| `graph_validation.json` | Summary of per‑graph validation against `graph.schema.yaml`. |
| `split_indices.json` | Already listed under Processed Data. |
| `split_validation.json` | Already listed under Results. |

## 5. Data Flow Diagram
1. **Loader** → `data/raw/raw_dataset.parquet` (checksum)  
2. **Graph Builder** → `graphs_v1.parquet`  
3. **Split Generator** → `split_indices.json` (with element‑overlap check)  
4. **Splitter Validation** → `split_validation.json`  
5. **Graph Validation** → `graph_validation.json`  
6. **Training + CV** → `model_v1.pt`, `training_logs.json`  
7. **Evaluation + Baseline** → `predictions.json`, `generalization_metrics.json`  
8. **Feature Importance** → `feature_importance_report.md`  
9. **Title Audit** → `constitution_title_audit.json`  

Orchestrated by `src/main_pipeline.py`; each stage must exit 0 before the next begins.

---

