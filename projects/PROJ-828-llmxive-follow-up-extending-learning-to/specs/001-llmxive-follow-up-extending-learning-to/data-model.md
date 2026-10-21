# Data Model: Low-Rank RL for Foresight in LLM Training

## Overview
Defines the persistent data artifacts produced by the experiment, their schemas, and the flow between raw, intermediate, and analysis stages.

## Data Flow Diagram (textual)
1. **Raw Data** → `src/data/loader.py` → `data/gsm8k_subset.parquet` (checksumed).  
2. **OPD Training** → `results/opd/update_trajectory.npy` (ΔW per step).  
3. **Subspace Extraction** → `results/opd/stable_subspace.npy` (top‑k vectors).  
4. **RL Variants** → `results/<variant>/` containing:  
   - `checkpoint_{step}.pt` (model state).  
   - `update_trajectory.npy`.  
   - `convergence_log.csv`.  
   - `relevance_log.csv` (Low‑Rank RL only).  
5. **Analysis** → `results/analysis/` with:  
   - `alignment_metrics.json`.  
   - `analysis_summary.json`.  
   - Plots (`*.png`).  
6. **Schema Validation** → `contracts/` JSON‑Schema files used by CI tests.

## Core Entities & Schemas

### 1. Training Run Configuration (`contracts/run_config.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Training Run Configuration"
type: object
properties:
  run_id:
    type: string
    description: "Unique identifier for the run (e.g., opd_20231020_seed0)."
  variant:
    type: string
    enum: ["opd","standard_rl","low_rank_rl","random_projection","random_walk_prior","opd_initialized_rl"]
  seed:
    type: integer
  model_config:
    type: object
    properties:
      hidden_size:
        type: integer
      num_layers:
        type: integer
      num_heads:
        type: integer
    required: ["hidden_size","num_layers","num_heads"]
  dataset:
    type: object
    properties:
      name:
        type: string
      subset_size:
        type: integer
      source_url:
        type: string
    required: ["name","subset_size","source_url"]
  hyperparameters:
    type: object
    properties:
      learning_rate:
        type: number
      batch_size:
        type: integer
      total_steps:
        type: integer
      rank_k:
        type: integer
    required: ["learning_rate","batch_size","total_steps"]
required: ["run_id","variant","seed","model_config","dataset","hyperparameters"]
additionalProperties: false
```

### 2. OPD Stable Subspace (`contracts/opd_subspace.schema.yaml`)
*Same as provided in the original artifact (quoted strings retained).*

### 3. Training Log (`contracts/training_log.schema.yaml`)
*Same as provided in the original artifact (quoted strings retained).*

### 4. Analysis Results (`contracts/analysis_results.schema.yaml`)
*Same as provided in the original artifact (quoted strings retained).*

## Data Integrity Measures
- **Checksums**: `src/data/checksums.py` computes SHA‑256 for every raw file; stored in `state/data_checksums.yaml`.  
- **Version Hashes**: After each run, `src/utils/hasher.py` hashes the entire `results/<variant>/` directory (excluding large `.pt` checkpoints) and writes the hash to `state/run_hashes.yaml`.  
- **Immutability**: Raw GSM8K files are never overwritten; derived matrices are written to new paths with timestamps.

## Storage Estimates (fits within free‑tier limits)
| Artifact | Approx. Size |
|----------|--------------|
| GSM8K subset (parquet) | 100 MB |
| OPD update trajectory (500 steps × 300 M params, FP16) | ~300 MB |
| Stable subspace (`k=10`) | ~2 MB |
| Each RL checkpoint (FP16) | ~600 MB |
| Logs & CSVs per seed | < 10 MB |
| Total (10 seeds × 6 variants) | ≈ 4.5 GB (well under 7 GB RAM & 14 GB disk) |

---
