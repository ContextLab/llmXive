# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## 1. Conceptual Entities

### VideoClip
Represents a single input unit (16 frames) processed by the pipeline.
- **Attributes**: `clip_id` (UUID), `source_dataset` (str), `file_path` (str), `status` (str: `processed`, `skipped`, `timeout`), `error_message` (str, optional).

### StatisticalFeature
Derived numerical properties from a `VideoClip`.
- **Attributes**: `clip_id` (FK), `optical_flow_variance` (float), `frame_to_frame_mse` (float), `temporal_gradient_sparsity` (float), `computed_at` (timestamp).

### DivergenceMetric
The core measurement of instability.
- **Attributes**: `clip_id` (FK), `predicted_latent_hash` (str), `euler_state_hash` (str), `l2_distance` (float), `euler_steps` (int: 100), `computation_time_sec` (float), `is_primary_analysis` (bool).

### HumanLabel
Manual annotation for threshold validation.
- **Attributes**: `clip_id` (FK), `rater_id` (int), `label` (str: `stable`, `unstable`), `timestamp` (timestamp).

### ThresholdModel
Derived model for classification.
- **Attributes**: `threshold_value` (float), `precision` (float), `recall` (float), `f1_score` (float), `sweep_range` (str), `sensitivity_results` (json).

## 2. Physical Data Model (CSV/Parquet Schema)

The system will output intermediate and final results in CSV/Parquet format for analysis.

### `data/processed/features.csv`
| Column | Type | Description |
| :--- | :--- | :--- |
| clip_id | string | Unique identifier |
| source_dataset | string | Kinetics-400 or UCF101 |
| optical_flow_variance | float | Variance of optical flow magnitude |
| frame_to_frame_mse | float | Mean Squared Error between frames |
| temporal_gradient_sparsity | float | Ratio of high-gradient pixels |
| status | string | processed, skipped, timeout |
| error_message | string | Optional error details |

### `data/processed/divergence_metrics.csv`
| Column | Type | Description |
| :--- | :--- | :--- |
| clip_id | string | Unique identifier |
| l2_distance | float | Flow-map divergence value |
| euler_steps | int | 100 (primary) |
| computation_time_sec | float | Time taken for calculation |
| is_primary_analysis | boolean | True if computation succeeded within 15m |

### `data/processed/annotations.csv`
| Column | Type | Description |
| :--- | :--- | :--- |
| clip_id | string | Unique identifier |
| rater_id | int | Rater 1 or 2 |
| label | string | stable or unstable |

### `data/processed/threshold_results.json`
| Key | Type | Description |
| :--- | :--- | :--- |
| optimal_threshold | float | Best F1 threshold |
| precision | float | Precision at optimal threshold |
| recall | float | Recall at optimal threshold |
| f1_score | float | F1 at optimal threshold |
| sensitivity_sweep | array | Array of {threshold, fpr, fnr} objects |

## 3. Data Flow

1.  **Ingestion**: Raw video files from `data/raw/` are loaded into `VideoClip` entities.
2.  **Feature Extraction**: `StatisticalFeature` records are created and saved to `features.csv`.
3.  **Divergence Calculation**: `DivergenceMetric` records are created. Clips failing the 15-min timeout are marked `timeout`.
4.  **Analysis**: `features.csv` and `divergence_metrics.csv` are joined (only `is_primary_analysis=True`). Ridge regression and correlation are performed.
5.  **Annotation**: Human labels are ingested into `annotations.csv`.
6.  **Thresholding**: `ThresholdModel` is computed and saved to `threshold_results.json`.