# Data Model: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Overview

This document defines the data structures, file formats, and schemas used throughout the project. All data is stored in `data/` with strict versioning and checksumming.

## File Hierarchy

```text
data/
├── raw/
│   ├── weights.npz          # Raw LoRA A/B matrices (downloaded)
│   └── task_descriptions.json # Task descriptions (metadata)
├── processed/
│   ├── skill_index.npz      # Flattened, normalized vectors + metadata
│   └── text_embeddings.npy  # Sentence embeddings for all tasks
└── results/
    ├── stats_raw.json       # Raw success rates (unadjusted)
    └── stats_report.json    # Final report with BH-corrected p-values
```

## Data Schemas

### 1. Skill Vector Index (`data/processed/skill_index.npz`)

A NumPy archive containing:
*   `vectors`: `(N, D)` float32 array. Flattened, normalized LoRA vectors.
*   `task_ids`: `(N,)` string array. Unique identifiers.
*   `descriptions`: `(N,)` string array. Original task text.
*   `metadata`: JSON string (serialized) containing base model version, rank, etc.

### 2. Raw Statistics (`data/results/stats_raw.json`)

A JSON object mapping task IDs to their success rates across strategies.

```json
{
  "task_001": {
    "baseline": 0.8,
    "nearest_neighbor": 0.7,
    "arithmetic_mean": 0.65,
    "weighted_avg": 0.75
  },
  ...
}
```

### 3. Statistical Report (`data/results/stats_report.json`)

A JSON object containing the final analysis, including p-values and BH corrections.

```json
{
  "summary": {
    "total_tasks": a small number,
    "runs_per_task": "multiple",
    "baseline_success_rate": "a high baseline success rate"
  },
  "comparisons": [
    {
      "strategy": "nearest_neighbor",
      "raw_p_value": "statistically significant",
      "bh_corrected_p_value":,
      "significant": false
    },
    {
      "strategy": "weighted_avg",
      "raw_p_value": "a statistically significant threshold",
      The study will evaluate whether the Benjamini-Hochberg corrected p-value falls below the conventional significance threshold of 0.05 to determine statistical significance.,
      "significant": true
    }
  ],
  "alignment_check": {
    "pearson_correlation": "a moderate to strong positive association",
    p_value: statistically significant.
    "valid": true
  },
  "linearity_validation": {
    "reconstruction_error": a low magnitude,
    "threshold": 0.05,
    "valid": true
  }
}
```

## Data Hygiene Rules

1.  **Checksums**: Every file in `data/raw/` and `data/processed/` must have a corresponding SHA256 hash recorded in `state/...yaml`.
2.  **Immutability**: Files in `data/raw/` are never modified. Derived files in `data/processed/` and `data/results/` are written as new files.
3.  **Format**:
    *   `.npz` files must be readable by `numpy.load()`.
    *   `.json` files must be valid JSON (no trailing commas, proper escaping).
4.  **PII**: No personally identifiable information is allowed in task descriptions or metadata.