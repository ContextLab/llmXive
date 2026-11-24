# Data Model: Low-Rank RL for Foresight in LLM Training

## Overview
Defines the persistent data artifacts produced by the experiment, their schemas, and the flow between raw, intermediate, and analysis stages.

## Data Flow Diagram (textual)
1. **Raw Data** → `src/data/loader.py` → `data/gsm8k_subset.parquet` (checksumed).  
2. **Test Set Creation** → `data/gsm8k_long_chain_test.parquet` (≥4 reasoning steps, frozen before training).
3. **Run Config Generation** → `results/run_config.json` per `contracts/run_config.schema.yaml` (one per variant × seed).
4. **OPD Training** → `results/opd/update_trajectory.npy` (ΔW per step).  
5. **Subspace Extraction** → `results/opd/stable_subspace.npy` (top‑k vectors).  
6. **RL Variants** → `results/<variant>/` containing:  
   - `checkpoint_{step}.pt` (model state).  
   - `update_trajectory.npy`.  
   - `convergence_log.csv`.  
   - `relevance_log.csv` (Low‑Rank RL & Random Low‑Rank RL, diagnostic only).  
7. **Analysis** → `results/analysis/` with:  
   - `alignment_metrics.json`.  
   - `analysis_summary.json`.  
   - Plots (`*.png`).  
8. **Schema Validation** → `contracts/` JSON‑Schema files used by CI tests.

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
    enum: ["opd","standard_rl","low_rank_rl","random_low_rank_rl"]
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
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "OPD Stable Subspace Schema"
type: object
properties:
  run_id:
    type: string
  variant:
    type: string
    enum: ["opd"]
  rank_k:
    type: integer
  explained_variance_ratio:
    type: array
    items:
      type: number
  cumulative_variance:
    type: number
  subspace_matrix_path:
    type: string
    pattern: "^results/.+\\.npy$"
  checksum:
    type: string
required:
  - run_id
  - variant
  - rank_k
  - explained_variance_ratio
  - cumulative_variance
  - subspace_matrix_path
  - checksum
additionalProperties: false
```

### 3. Training Log (`contracts/training_log.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Training Log Schema"
type: object
properties:
  run_id:
    type: string
  variant:
    type: string
    enum: ["opd","standard_rl","low_rank_rl","random_low_rank_rl"]
  seed:
    type: integer
  steps:
    type: array
    items:
      type: object
      properties:
        step:
          type: integer
        accuracy:
          type: number
          minimum: 0.0
          maximum: 1.0
        loss:
          type: number
        alignment_score:
          type: number
          minimum: -1.0
          maximum: 1.0
        relevance_score:
          type: number
          minimum: -1.0
          maximum: 1.0
        memory_usage_mb:
          type: number
        timestamp:
          type: string
          format: date-time
      required:
        - step
        - accuracy
        - loss
        - timestamp
  convergence_step:
    type: integer
  final_alignment_score:
    type: number
required:
  - run_id
  - variant
  - seed
  - steps
  - convergence_step
  - final_alignment_score
additionalProperties: false
```

### 4. Analysis Results (`contracts/analysis_results.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Analysis Results Schema"
type: object
properties:
  experiment_id:
    type: string
  variants:
    type: array
    items:
      type: object
      properties:
        variant_name:
          type: string
          enum: ["opd","standard_rl","low_rank_rl","random_low_rank_rl"]
        seeds:
          type: array
          items:
            type: integer
        steps_to_80pct:
          type: array
          items:
            type: integer
        mean_steps:
          type: number
        std_steps:
          type: number
        final_accuracy_long:
          type: array
          items:
            type: number
          description: "Generalization accuracy on held-out long-chain test set."
        mean_final_accuracy:
          type: number
        std_final_accuracy:
          type: number
        projection_constraint_scores:
          type: array
          items:
            type: number
          description: "Mean cosine similarity with subspace (diagnostic only)."
      required:
        - variant_name
        - seeds
        - steps_to_80pct
        - mean_steps
        - std_steps
  statistical_tests:
    type: object
    properties:
      comparison:
        type: string
      test_type:
        type: string
        enum: ["wilcoxon","t-test"]
      p_value:
        type: number
      significant:
        type: boolean
    required:
      - comparison
      - test_type
      - p_value
      - significant
  power_analysis:
    type: object
    properties:
      effect_size_assumed:
        type: number
        description: "A priori assumed Cohen's d."
      sample_size:
        type: integer
      power_a_priori:
        type: number
        description: "A priori power (target 0.8)."
      effect_size_observed:
        type: number
        description: "Observed Cohen's d from results."
      power_post_hoc:
        type: number
        description: "Post-hoc power based on observed effect."
    required:
      - effect_size_assumed
      - sample_size
      - power_a_priori
      - effect_size_observed
      - power_post_hoc
required:
  - experiment_id
  - variants
  - statistical_tests
  - power_analysis
additionalProperties: false
```

## Data Integrity Measures
- **Checksums**: `src/data/checksums.py` computes SHA‑256 for every raw file; stored in `state/data_checksums.yaml`.  
- **Version Hashes**: After each run, `src/utils/hasher.py` hashes the entire `results/<variant>/` directory (excluding large `.pt` checkpoints) and writes the hash to `state/run_hashes.yaml`.  
- **Immutability**: Raw GSM8K files are never overwritten; derived matrices are written to new paths with timestamps. Test set is frozen before training begins.

## Storage Estimates (fits within free‑tier limits)
| Artifact | Approx. Size |
|----------|--------------|
| GSMK subset (parquet) | ~100 MB |
| GSMK long‑chain test set (parquet) | ~20 MB |
| OPD update trajectory (several steps × millions of parameters, FP32) | hundreds of MB |
| Stable subspace (`k=10`) | ~2 MB |
| Each RL checkpoint (FP precision) | ~500 MB |
| Logs & CSVs per seed | < 10 MB |
| Total (multiple seeds × 4 variants + ablation) | ≈ several GB (well under 7 GB RAM & 14 GB disk) |

---
