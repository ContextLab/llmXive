# Data Model: Astrocyte-Inspired Meta-Learning

## 1. Overview

This document defines the data structures, file formats, and schemas used throughout the project. All data flows from raw datasets (downloaded) to processed logs (training) and finally to aggregated results (analysis).

## 2. Data Flow

1.  **Raw Data**: Downloaded from `torchvision` (Omniglot) and custom loader (Mini-ImageNet). Stored in `data/raw/`.
2.  **Processed Data**: None. The training loop loads images on-the-fly.
3.  **Training Logs**: Generated per episode, stored in `results/logs/`.
4.  **Aggregated Results**: Generated per seed, stored in `results/stats/`.
5.  **Analysis Output**: Statistical test results, stored in `results/stats/`.

## 3. Data Entities

### 3.1 Episode
A single execution instance of a 5-way 1-shot classification problem.
- `episode_id`: Unique integer identifier for the episode within a run.
- `seed`: Random seed used for this run.
- `support_set`: List of (image, label) pairs.
- `query_set`: List of (image, label) pairs.

### 3.2 Homeostatic State
Internal state of the astrocyte module.
- `calcium_concentration`: $Ca_t$ (float).
- `homeostatic_factor`: $h_t$ (float).
- `task_history_buffer`: List of past activation signals (used for ODE).

### 3.3 Performance Metric
Record of performance for a single episode.
- `episode_id`: ID of the episode (integer).
- `seed`: Random seed.
- `plasticity_score`: Accuracy on current task (after 1, 5, 10 steps). **Scalar**.
- `stability_score`: Accuracy on **Meta-Test Buffer** (last 5 completed tasks **excluded** from the Calcium history). **Scalar**.
- `loss`: MAML loss for the episode.
- `timestamp`: UTC timestamp of the log.

### 3.4 Statistical Result
Result of the Permutation Test.
- `test_name`: "Permutation Test".
- `observed_distance`: Euclidean distance between mean vectors.
- `p_value`: P-value from permutations.
- `significant`: Boolean (p < 0.05).
- `seeds_used`: Number of seeds.
- `permutations`: Number of permutations performed.

## 4. File Formats

### 4.1 Training Log (JSON Lines)
File: `results/logs/seed_<N>_run.jsonl`
Each line is a JSON object representing one episode.

```json
{"episode_id": 1, "seed": 42, "plasticity_score": 0.85, "stability_score": 0.72, "loss": 0.45, "timestamp": "2026-07-03T12:00:00Z"}
```

### 4.2 Aggregated Results (CSV)
File: `results/stats/aggregated_results.csv`
One row per seed.

```csv
seed,final_plasticity,final_stability,avg_loss
42,0.88,0.75,0.32
43,0.87,0.74,0.33
...
```

### 4.3 Statistical Test Output (JSON)
File: `results/stats/statistical_test.json`

```json
{
  "test": "Permutation Test",
  "observed_distance": 0.12,
  "p_value": 0.03,
  "significant": true,
  "seeds_used": 5,
  "permutations": 10000,
  "baseline_model": "MAML",
  "experimental_model": "Astrocyte-MAML"
}
```

## 5. Data Hygiene & Versioning

- **Checksums**: All raw data files in `data/raw/` are checksummed (SHA-256) and recorded in `state/...yaml`.
- **Immutability**: Raw data is never modified. Derived files (logs, stats) are new files with timestamps.
- **PII**: No personally identifiable information is present in the datasets or logs.
- **Versioning**: Every artifact (log, result) is versioned by its content hash.

## 6. Data Validation Rules

- **Plasticity/Stability**: Must be in range [0.0, 1.0].
- **Loss**: Must be non-negative.
- **Episode ID**: Must be unique per seed and integer.
- **Seed**: Must be an integer.
- **Disjoint Buffer**: The `stability_score` must be calculated on a buffer of episodes explicitly excluded from the `task_history_buffer` used for the current `calcium_concentration` calculation.