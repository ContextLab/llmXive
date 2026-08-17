# Data Model: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## 1. Overview

This document defines the data schemas for the `VideoSample`, `CuratedDataset`, `TrainedModel`, `BenchmarkResult`, and `MuJoCoValidationResult` entities. All data is stored in `data/` with checksums for reproducibility (Constitution Principle III).

## 2. Entity Definitions

### 2.1 VideoSample
A single generated video with metadata.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique UUID for the sample. | Required, UUIDv4 |
| `prompt` | string | Text prompt used for generation. | Required |
| `raw_path` | string | Relative path to the MP4 file in `data/raw/`. | Required |
| `physics_score` | float | Score from PyBullet filter (0-100). | Range: 0.0 to 100.0 |
| `status` | string | `pass` or `fail`. | Enum: ["pass", "fail"] |
| `generation_seed` | integer | Random seed used for generation. | Required |
| `timestamp` | string | ISO 8601 timestamp of generation. | Required |

### 2.2 CuratedDataset
A collection of `VideoSample` records that passed the filter.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `dataset_id` | string | Unique ID for the curated batch. | Required |
| `samples` | list | List of `VideoSample` objects. | Non-empty |
| `threshold_score` | float | The fixed absolute threshold used for cutoff (60.0). | Required (Source: 2506.09162) |
| `total_generated` | integer | Total videos generated before filtering. | Required |
| `retained_count` | integer | Number of videos retained. | Required |
| `retention_rate` | float | `retained_count / total_generated`. | Range: 0.0 to 1.0 |

### 2.3 TrainedModel
The state of the diffusion model after training.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `model_id` | string | Unique ID for the model checkpoint. | Required |
| `checkpoint_path` | string | Relative path to model weights in `models/`. | Required |
| `training_config` | object | Hyperparameters used (lr, epochs, batch_size). | Required |
| `dataset_id` | string | Reference to the `CuratedDataset` used. | Required |
| `training_seed` | integer | Random seed for training. | Required |
| `loss_history` | list | List of loss values per epoch. | Required |
| `training_duration` | float | Elapsed time in seconds. | Required (SC-005) |

### 2.4 MuJoCoValidationResult
Independent validation of the PyBullet filter.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `validation_id` | string | Unique ID for the validation run. | Required |
| `sample_ids` | list | List of video IDs validated. | Required |
| `mujoco_scores` | list | List of MuJoCo scores. | Required |
| `correlation_coefficient` | float | Pearson/Spearman correlation with PyBullet. | Range: -1.0 to 1.0 |
| `independence_verified` | boolean | True if correlation < 0.95. | Required (SC-006) |

### 2.5 BenchmarkResult
Evaluation metrics for a model.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `result_id` | string | Unique ID for the result. | Required |
| `model_id` | string | Reference to the `TrainedModel`. | Required |
| `r_bench_score` | float | Physical consistency score on R-Bench. | Required |
| `pai_bench_score` | float | Physical consistency score on PAI-Bench. | Required |
| `downstream_success_rate` | float | Success rate on the separate control task. | Required |
| `mujoco_correlation` | float | Correlation with MuJoCo validator (if applicable). | Range: -1.0 to 1.0 |
| `tost_p_value` | float | P-value from TOST equivalence test. | Range: 0.0 to 1.0 |
| `equivalence_flag` | boolean | `True` if equivalent within 15% margin. | Required |
| `training_duration` | float | Elapsed time in seconds. | Required (SC-005) |

## 3. File Formats

- **Videos**: `.mp4` (H.264 codec).
- **Metadata**: `.jsonl` (one JSON object per line) for `VideoSample` lists.
- **Configuration**: `.yaml` for `config.yaml`.
- **Results**: `.json` for `BenchmarkResult`.

## 4. Data Flow

1. **Generation**: `src/generation/wan2_generator.py` produces `VideoSample` records (raw MP4 + metadata).
2. **Filtering**: `src/filters/pybullet_filter.py` updates `physics_score` and `status`.
3. **Curation**: `src/cli/main.py` aggregates passing samples into `CuratedDataset`.
4. **Training**: `src/training/trainer.py` consumes `CuratedDataset` and produces `TrainedModel`.
5. **Evaluation**: `src/evaluation/` consumes `TrainedModel` and produces `BenchmarkResult` and `MuJoCoValidationResult`.