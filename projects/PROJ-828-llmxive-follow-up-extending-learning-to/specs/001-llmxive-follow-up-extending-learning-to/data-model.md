# Data Model: Low-Rank RL for Foresight in LLM Training

## Overview

This document defines the data structures, schemas, and flow for the Low-Rank RL experiment. All data is stored in `data/` (raw) and `results/` (derived) directories.

## Data Flow

1. **Raw Data**: GSM8K subset downloaded from verified HuggingFace URLs.
2. **Training Logs**: Accuracy, loss, and update directions recorded at each step.
3. **Model Artifacts**: Checkpoints of the OPD baseline, Standard RL, Low-Rank RL, Random Projection, and Random Walk variants.
4. **Analysis Results**: Convergence metrics, alignment scores, and statistical test results.

## Key Entities

### 1. Update Trajectory
- **Definition**: Sequence of parameter difference matrices ($\Delta W_t$) recorded during training.
- **Storage**: `results/<variant>/update_trajectory.npy`
- **Shape**: `(num_steps, num_layers, layer_dim)` or flattened `(num_steps, total_params)`.

### 2. Stable Subspace
- **Definition**: Top-$k$ singular vectors from OPD update matrices.
- **Storage**: `results/opd/stable_subspace.npy`
- **Shape**: `(k, total_params)` or `(k, layer_dim)` per layer.

### 3. Convergence Log
- **Definition**: Steps to reach [deferred] accuracy.
- **Storage**: `results/<variant>/convergence_log.csv`
- **Fields**: `seed`, `step`, `accuracy`, `loss`, `alignment_score`, `relevance_score`.

### 4. Alignment Metrics
- **Definition**: Cosine similarity between update directions and baselines.
- **Storage**: `results/analysis/alignment_metrics.json`
- **Fields**: `variant`, `final_alignment`, `early_alignment`, `p_value`.

### 5. Projection Relevance Metric
- **Definition**: Cosine similarity between the current RL update direction and the OPD subspace at each step.
- **Storage**: `results/<variant>/relevance_log.csv`
- **Fields**: `step`, `relevance_score` (cosine similarity).

## Schema Definitions

### Training Run Configuration
```yaml
run_id: string
variant: enum["opd", "standard_rl", "low_rank_rl", "random_projection", "random_walk_prior"]
seed: integer
model_config: object
  hidden_size: integer
  num_layers: integer
  num_heads: integer
dataset: object
  name: string
  subset_size: integer
  source_url: string
hyperparameters: object
  learning_rate: float
  batch_size: integer
  total_steps: integer
  rank_k: integer (for low_rank_rl, random_projection, random_walk_prior)
```

### Convergence Log Entry
```yaml
step: integer
accuracy: float
loss: float
alignment_score: float (optional, for RL variants)
relevance_score: float (optional, for low_rank_rl)
memory_usage_mb: float
timestamp: string
```

### Analysis Summary
```yaml
variant: string
seed: integer
steps_to_80pct: integer
final_alignment_score: float
early_alignment_score: float
relevance_score_mean: float
```

## Data Integrity

- **Checksums**: All raw data files are checksummed using a secure hashing algorithm upon download.
- **Versioning**: Model checkpoints and logs include a hash of the training configuration. A SHA-256 hash of the `results/` directory (excluding full model checkpoints to respect storage limits, but including logs, metrics, and small matrices) is computed and stored in `state/` after each run.
- **Immutability**: Raw data is never modified. Derived data is written to new files.

## Storage Constraints

- **Raw Data**: ~100MB (GSM8K subset).
- **Training Logs**: ~10MB per run (text/CSV).
- **Model Checkpoints**: ~600MB per run (FP16, 300M params).
- **Total Estimated**: < 5GB (10 seeds * 5 variants * ~600MB + logs). This fits within the disk limit of the free-tier runner, with logs and metrics being hashed for versioning.