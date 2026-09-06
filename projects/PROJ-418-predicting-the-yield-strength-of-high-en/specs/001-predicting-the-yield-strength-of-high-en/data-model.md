# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The data model defines the schema for every artifact exchanged between pipeline stages. All JSON/YAML files must validate against the corresponding schema in `contracts/`.

## Core Schemas

| Schema File | Purpose | Key Fields |
|-------------|---------|------------|
| `contracts/dataset.schema.yaml` | Raw HEA dataset (composition + target) | `composition` (mapping element → fraction), `yield_strength` (float) |
| `contracts/processed_data.schema.yaml` | Descriptor matrix after VIF handling | `descriptors` (mapping descriptor_name → float), `sample_id` (string) |
| `contracts/metrics.schema.yaml` | Model performance metrics | `r2`, `pearson_r`, `p_value`, `bootstrap_ci` (list of two floats) |
| `contracts/importance.schema.yaml` | Permutation‑importance results | `feature`, `importance_score`, `p_value`, `significant` (bool) |
| `contracts/manifest.schema.yaml` | Provenance log | `seed`, `software_versions` (mapping), `checksums` (mapping file → sha256), `timestamp` |
| `contracts/runtime.schema.yaml` | CI/runtime summary | `status`, `duration_seconds`, `warnings` (int) |

## Data Flow

1. **Raw Data** (`data/raw/heas.csv`) → validated by `dataset.schema.yaml`.  
2. **Descriptors** (`output/descriptors.parquet`) → validated by `processed_data.schema.yaml`.  
3. **Model Artifact** (`output/model.joblib`) → not schema‑validated (binary).  
4. **Metrics** (`output/metrics.json`) → `metrics.schema.yaml`.  
5. **Importance** (`output/importance.json`) → `importance.schema.yaml`.  
6. **Manifest** (`output/manifest.json`) → `manifest.schema.yaml`.  
7. **Runtime** (`output/pipeline_runtime.json`) → `runtime.schema.yaml`.  

All files are checksum‑recorded in the manifest (Principle III).  

---
