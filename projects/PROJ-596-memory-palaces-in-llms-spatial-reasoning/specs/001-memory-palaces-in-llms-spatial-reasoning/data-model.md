# Data Model: Memory Palaces in LLMs

## Overview

This document defines the data structures, schemas, and storage formats used in the project. All data is stored in `data/` (raw) and `artifacts/results/` (processed).

## Raw Data

-   **bAbI Task 3**: Downloaded from `facebook/babi` and stored as parquet.
-   **LAMBADA**: Downloaded from `EleutherAI/lambada_openai` and stored as parquet.
-   **Story Cloze**: Downloaded from `rocstories` and stored as parquet.
-   **Checksums**: SHA-256 checksums are recorded for all raw files in `state/...yaml`.

## Processed Data

### 1. Model Checkpoints

-   **Format**: Hugging Face `transformers` checkpoint (`.bin`, `.json`).
-   **Location**: `code/models/spatial/` and `code/models/non_spatial/`.
-   **Naming**: `model_seed_{seed}_variant_{variant}.pt`.

### 2. Evaluation Results

-   **Format**: JSON.
-   **Location**: `artifacts/results/run_summary.json`.
-   **Schema**: See `contracts/results.schema.yaml`.

### 3. Structural Metrics (Per-Epoch)

-   **Format**: JSON.
-   **Location**: `artifacts/metrics/epoch_{epoch}.json`.
-   **Content**: Slot occupancy, coordinate variance, interference distance per sample.
-   **Schema**: See `contracts/epoch_metrics.schema.yaml`.

### 4. Training Run Logs

-   **Format**: JSON.
-   **Location**: `artifacts/logs/training_run_{run_id}.json`.
-   **Content**: Hyperparameters, resource usage, subsampling rate.
-   **Schema**: See `contracts/training_run.schema.yaml`.

## Contracts

The following contracts define the structure of the data.

### Dataset Schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  dataset_name:
    type: string
    description: "Name of the dataset (e.g., 'babi_task3')"
  source_url:
    type: string
    description: "Verified URL or Hugging Face ID"
  checksum:
    type: string
    description: "SHA-256 checksum of the raw file"
  num_samples:
    type: integer
    description: "Total number of samples in the dataset"
```

### Model Output Schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  seed:
    type: integer
    description: "Random seed used for this run"
  variant:
    type: string
    enum: ["spatial", "non_spatial"]
    description: "Model variant"
  dataset:
    type: string
    description: "Dataset name"
  recall_accuracy:
    type: number
    description: "Exact-match recall accuracy"
  interference_distance:
    type: number
    description: "Drop in recall under interference"
  slot_occupancy:
    type: array
    items:
      type: integer
    description: "Count of items per slot"
  coordinate_variance:
    type: number
    description: "Trace of the 2D covariance matrix"
```

### Results Schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  experiment_id:
    type: string
    description: "Unique ID for the experiment run"
  timestamp:
    type: string
    format: date-time
    description: "UTC timestamp of the run"
  datasets:
    type: array
    items:
      type: object
      properties:
        name:
          type: string
        spatial_mean:
          type: number
        spatial_std:
          type: number
        non_spatial_mean:
          type: number
        non_spatial_std:
          type: number
        p_value:
          type: number
        effect_size:
          type: number
        ci_lower:
          type: number
        ci_upper:
          type: number
        interference_spatial:
          type: number
        interference_non_spatial:
          type: number
```
