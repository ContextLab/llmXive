# Data Model: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview

All artifacts are versioned, checksummed (hashes under `data/`), and validated against schemas in `contracts/`. Raw inputs are immutable; every transformation writes a new file with documented derivation.

## 2. Raw Data (`data/raw/`)

Canonical parquet downloaded from the selected verified URL (see research.md Dataset Strategy). SHA‑256 checksum recorded in `data/raw/metadata.json`. Required columns (validated at load):

| Field | Type | Description |
|---|---|---|
| `material_id` | string | Unique identifier |
| `structure` | string (CIF) | Pymatgen‑compatible CIF representation |
| `elastic_tensor` | list[float] | Several independent Voigt components (C₁₁, C₁₂, C₂₂, C₆₆, C₁₃, C₃₃) |
| `formula` | string | Chemical formula |
| `space_group` | integer | Space‑group number |
| `is_2d` | boolean | Flag indicating 2D dimensionality |

## 3. Processed Data (`data/processed/`)

### 3.1 `graphs_v1.parquet` (schema `contracts/dataset_schema.schema.yaml`)
Per row: `material_id`, `num_nodes`, `num_edges`, `node_features` (5 columns), `edge_index`, `edge_features` (2 columns), `target_young`, `target_shear`, `target_poisson`, `family` (space‑group + stoichiometry), plus the full multi‑component tensor and an eligibility flag.

### 3.2 `split_indices.json` (schema `contracts/split_indices_schema.yaml`)
Contains `train_ids`, `val_ids`, `test_ids`, corresponding `train_families`, `val_families`, `test_families`, `split_seed`, and `timestamp`. Written atomically.

### 3.3 `model_v1.pt`
Torch checkpoint: `state_dict`, `hyperparameters`, `seed`, `target_normalization`, and the disclaimer text imported from `code/utils/disclaimer_template.py`.

## 4. Results (`data/results/`)

| File | Purpose | Schema |
|---|---|---|
| `constitution_title_audit.json` | Terminology audit (FR‑006/FR‑009) | `contracts/constitution_audit_schema.schema.yaml` |
| `training_logs.json` | Epoch losses, peak memory, Cross‑validation (CV) statistics, MEGNet benchmark flag, disclaimer | `contracts/training_logs_schema.yaml` |
| `split_validation.json` | Family‑disjointness and size validation | `contracts/split_validation.schema.yaml` |
| `generalization_metrics.json` | Surrogate & baseline metrics, relative reductions (including Poisson MAE), intra‑/inter‑family MAPE, inference timing, gates for SC‑[generic identifier]/SC‑003/SC‑006 | `contracts/results_schema.schema.yaml` |
| `predictions.json` | Test‑set true vs predicted values, per‑record errors | `contracts/predictions_schema.yaml` |
| `feature_importance_report.md` | Ranked descriptors, permutation + SHAP + ablation results, statistical tests | Markdown (no schema) |

## 5. Data Flow

1. **Loader** → `data/raw/*.parquet` (checksum)  
2. **Graph Builder** → `graphs_v1.parquet`  
3. **Split Generator** → `split_indices.json` (family definition = space‑group + stoichiometry)  
4. **Splitter Validation** → `split_validation.json`  
5. **Training + CV** → `model_v1.pt`, `training_logs.json`  
6. **Evaluation + Baseline** → `predictions.json`, `generalization_metrics.json`  
7. **Feature Importance** → `feature_importance_report.md`  
8. **Title Audit** → `constitution_title_audit.json` (runs first as a gate)

Orchestrated by `code/main_pipeline.py`; each stage must exit 0 before the next runs.
