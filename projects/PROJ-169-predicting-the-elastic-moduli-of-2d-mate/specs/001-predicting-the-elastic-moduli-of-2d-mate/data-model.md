# Data Model: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview

This document defines the data schemas, transformations, and storage formats for the surrogate model pipeline. All data artifacts are versioned and checksummed.

## 2. Raw Data Schema

The raw data is ingested from HuggingFace Parquet files (`matbench/elasticity`).

**Source**: `data/raw/matbench_elasticity.parquet`
**Format**: Apache Parquet

| Field | Type | Description | Source Column |
| :--- | :--- | :--- | :--- |
| `material_id` | string | Unique identifier. | `material_id` |
| `formula` | string | Chemical formula. | `formula` |
| `structure` | object | Atomic structure (dict: species, coords). | `structure` |
| `elastic_tensor` | list[float] | 6 independent components (Voigt). | `elastic_tensor` |
| `space_group` | integer | Space group number. | `space_group` |
| `family` | string | Composite key (Space Group + Motif). | Derived |

**Note**: `family` is derived from `space_group` and `formula` (e.g., "TMD" if SG=187 and "S" in formula).

## 3. Processed Data Schema

### 3.1 Graph Dataset (`data/processed/graphs_v1.parquet`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `material_id` | string | Unique ID. |
| `num_nodes` | int | Number of atoms. |
| `num_edges` | int | Number of bonds. |
| `node_features` | list[list[float]] | Atomic features. |
| `edge_index` | list[list[int]] | Connectivity matrix (PBC-aware). |
| `edge_features` | list[list[float]] | Bond features (distance, etc.). |
| `target_young` | float | Young's modulus (GPa). |
| `target_shear` | float | Shear modulus (GPa). |
| `target_poisson` | float | Poisson's ratio. |

### 3.2 Split Indices (`data/processed/split_indices.json`)

```json
{
  "train_families": ["TMD", "Graphene"],
  "test_families": ["MXene"],
  "train_ids": ["id1", "id2"],
  "test_ids": ["id3"],
  "split_seed": 42,
  "timestamp": "2026-07-08T12:00:00Z"
}
```

### 3.3 Model Weights (`data/processed/model_v1.pt`)

PyTorch state dictionary. Contains:
- Model parameters.
- Training hyperparameters.
- Random seed.
- Disclaimer text.

## 4. Output Data Schema

### 4.1 Training Logs (`data/results/training_logs.json`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | UUID. |
| `epochs` | int | Number of epochs. |
| `train_loss_history` | list[float] | Loss per epoch. |
| `val_loss_history` | list[float] | Validation loss per epoch. |
| `peak_memory_gb` | float | Peak RAM usage. |
| `memory_limit_exceeded` | boolean | True if > 7.0 GB. |
| `disclaimer_included` | boolean | True if Feynman quote is present. |

### 4.2 Generalization Metrics (`data/results/generalization_metrics.json`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `mape_young` | float | MAPE for Young's modulus. |
| `mape_shear` | float | MAPE for Shear modulus. |
| `mape_poisson` | float | MAPE for Poisson's ratio. |
| `overall_mape` | float | Weighted average MAPE. |
| `mape_ci_lower` | float | 95% CI Lower Bound for MAPE. |
| `mape_ci_upper` | float | 95% CI Upper Bound for MAPE. |
| `rmse_young` | float | RMSE for Young's modulus. |
| `threshold` | float | Success threshold (0.15). |
| `status` | string | "PASS" or "FAIL". |
| `test_families` | list[string] | Families in the test set. |
| `message` | string | Error message if FAIL. |

### 4.3 Constitution Title Audit (`data/results/constitution_title_audit.json`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | string | "PASS" or "FAIL". |
| `found_title` | string | Title found in constitution file. |
| `expected_title` | string | "Structure-Only Surrogate Model for 2D Material Elastic Moduli". |
| `message` | string | Error message if FAIL. |

### 4.4 Inference Benchmark (`data/results/inference_benchmark.json`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `avg_inference_time_ms` | float | Average time per material. |
| `max_inference_time_ms` | float | Max time per material. |
| `status` | string | "PASS" or "FAIL". |
| `message` | string | Error message if FAIL. |

## 5. Data Flow

1.  **Ingest**: `loader.py` downloads raw Parquet.
2.  **Transform**: `graph_builder.py` converts raw to `graphs_v1.parquet` (PBC-aware).
3.  **Split**: `splitter.py` generates `split_indices.json` (Composite Key).
4.  **Train**: `train.py` trains model, logs memory, saves `model_v1.pt` and `training_logs.json`.
5.  **Eval**: `eval_runner.py` computes metrics (RMSE, MAPE, CI), saves `generalization_metrics.json`.
6.  **Benchmark**: `inference_benchmark.py` measures time, saves `inference_benchmark.json`.
7.  **Audit**: `verify_constitution_title.py` validates constitution, saves `constitution_title_audit.json`.