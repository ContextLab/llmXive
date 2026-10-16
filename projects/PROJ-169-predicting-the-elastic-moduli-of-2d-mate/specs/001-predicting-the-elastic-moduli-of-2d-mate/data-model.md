# Data Model: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview

Schemas, transformations, and storage for the surrogate pipeline. All artifacts versioned and checksummed; raw data immutable; every derivation writes a new file.

## 2. Raw Data (`data/raw/`)

Downloaded parquet from the verified canonical URL (see research.md). Required fields validated at load:

| Field | Type | Description |
| :--- | :--- | :--- |
| `material_id` | string | Unique identifier |
| `structure` | object/string | Pymatgen Structure dict or CIF text |
| `elastic_tensor` | list[float] | 6 independent Voigt components (Principle VI filter) |
| `formula` | string | Chemical formula |
| `space_group` | integer | Space group number |

Derived: `family` = space_group + stoichiometry class; `is_2d` flag from structure dimensionality.

## 3. Processed Data (`data/processed/`)

### 3.1 `graphs_v1.parquet` — see `contracts/dataset_schema.schema.yaml`
Per-material graph rows: `material_id`, `num_nodes`, `num_edges`, `node_features`, `edge_index`, `edge_features`, `target_young`, `target_shear`, `target_poisson`, plus `family` for stratified analysis. Moduli derived exclusively by `code/physics/tensors.py` from the elastic tensor.

### 3.2 `split_indices.json` (T013f, atomic write)
```json
{
  "train_ids": ["..."], "val_ids": ["..."], "test_ids": ["..."],
  "train_families": ["..."], "test_families": ["..."],
  "split_seed": 42, "timestamp": "ISO-8601"
}
```

### 3.3 `model_v1.pt` (T018b)
Torch save containing: state dict, hyperparameters, seed, target normalization stats, disclaimer text.

## 4. Results (`data/results/`)

### 4.1 `training_logs.json`
`run_id`, `epochs`, `train_loss_history`, `val_loss_history`, `peak_memory_gb`, `memory_limit_exceeded`, `device` ("cpu"), `disclaimer_included`.

### 4.2 `split_validation.json` (T017b)
`status` (PASS/FAIL), `train/val/test_counts`, `train_families`, `test_families`, `leakage_check` (boolean — no shared families), `message`.

### 4.3 `generalization_metrics.json` — see `contracts/results_schema.schema.yaml`
Per-property MAPE, overall MAPE, bootstrap 95% CI, RMSE, baseline comparison (`baseline_mape`, `relative_mape_reduction`, SC-002 pass/fail), `test_families`, `status`, `message`.

### 4.4 `predictions.json` (T018b)
List of test-set records: `material_id`, `family`, true/predicted Young/shear/Poisson, absolute errors, per-record APE.

### 4.5 `constitution_title_audit.json` — see `contracts/constitution_audit_schema.schema.yaml`

### 4.6 `inference_benchmark.json`
`avg_inference_time_ms`, `max_inference_time_ms`, `n_materials`, `status`, `message`.

### 4.7 `feature_importance_report.md`
Unified ranked descriptor list with permutation ablation deltas and mean |SHAP| magnitudes; Holm-corrected significance; disclaimer footer from `code/utils/disclaimer_template.py`.

## 5. Data Flow

1. `loader.py` — download + checksum + schema validation (hard gate).
2. `graph_builder.py` — structures → `graphs_v1.parquet`.
3. `split_generator.py` — family clustering → `split_indices.json` (atomic write).
4. `splitter.py` — validation → `split_validation.json`.
5. `train.py` — CPU training under `tracemalloc` → `model_v1.pt`, `training_logs.json`.
6. `eval_runner.py` — metrics + baseline + `predictions.json`, `generalization_metrics.json`.
7. `inference_benchmark.py` → `inference_benchmark.json`.
8. `feature_importance.py` → `feature_importance_report.md`.
9. `verify_constitution_title.py` → `constitution_title_audit.json` (exit-code gate).
