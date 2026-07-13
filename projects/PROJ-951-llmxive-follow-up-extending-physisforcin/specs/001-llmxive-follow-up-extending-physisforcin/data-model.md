# Data Model: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Overview

This document defines the data structures, schemas, and relationships for the `llmXive follow-up` project. The data model supports the pipeline: Generation → Filtering → Training → Evaluation.

## Entity Definitions

### 1. VideoSample
A single generated robotic manipulation video with associated metadata.

**Fields**:
- `id`: Unique identifier (UUID).
- `prompt`: The text prompt used for generation.
- `video_path`: Relative path to the MP4 file.
- `physics_score`: Float (0.0–1.0) from the PyBullet filter.
- `pass_status`: Boolean (True if score ≥ 60th percentile).
- `generation_timestamp`: ISO 8601 timestamp.
- `checksum`: SHA-256 hash of the video file.
- `batch_id`: Identifier for the generation batch (A, B, C).

### 2. CuratedDataset
A collection of `VideoSample` entities that passed the physics filter.

**Fields**:
- `dataset_id`: Unique identifier for the curated batch.
- `total_samples`: Count of videos in the dataset.
- `discarded_count`: Count of videos discarded.
- `samples`: List of `VideoSample` objects.
- `threshold_score`: The 60th percentile score used for filtering.
- `augmentation_applied`: Boolean (True if FR-009 augmentation was triggered).

### 3. TrainedModel
The distilled diffusion model trained on the `CuratedDataset`.

**Fields**:
- `model_id`: Unique identifier.
- `architecture`: String (e.g., "Diffusion-50M").
- `training_config`: JSON object containing hyperparameters.
- `weights_path`: Relative path to model weights.
- `training_log`: List of epoch-wise metrics (loss, learning rate).
- `training_timestamp`: ISO 8601 timestamp.

### 4. BenchmarkResult
The output metrics for a specific model on R-Bench and PAI-Bench.

**Fields**:
- `result_id`: Unique identifier.
- `model_id`: Reference to `TrainedModel`.
- `r_bench_score`: Float.
- `pai_bench_score`: Float.
- `physics_consistency_score`: Float (average score of generated evaluation videos).
- `statistical_test`: Object containing `test_type`, `p_value`, `comparability_flag`, `batch_effect_variance`.

### 5. AugmentationConfig
Configuration for data augmentation applied to the dataset.

**Fields**:
- `config_id`: Unique identifier.
- `dataset_id`: Reference to `CuratedDataset`.
- `technique`: String (e.g., "temporal_jittering", "geometric_flipping").
- `parameters`: JSON object containing augmentation parameters.
- `trigger_reason`: String (e.g., "n < 30").

## Data Flow

1.  **Generation**: `VideoSample` entities are created and stored in `data/raw/`.
2.  **Filtering**: `VideoSample` entities are scored and filtered. Passing samples are moved to `data/curated/` and aggregated into a `CuratedDataset`.
3.  **Training**: The `CuratedDataset` is used to train a `TrainedModel`.
4.  **Evaluation**: The `TrainedModel` is evaluated, producing `BenchmarkResult` entities stored in `data/eval/`.

## Storage Format

-   **Videos**: MP4 format (H.264 codec).
-   **Metadata**: JSON (for small datasets) or Parquet (for large datasets).
-   **Checkpoints**: PyTorch `.pt` files.
-   **Logs**: JSONL format.

## Versioning

-   All data files are versioned via content hashing (SHA-256).
-   The `state/projects/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml` file tracks the latest version of each artifact.
