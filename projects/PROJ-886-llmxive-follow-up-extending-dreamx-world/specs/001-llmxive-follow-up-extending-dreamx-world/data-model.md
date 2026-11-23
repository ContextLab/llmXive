# Data Model: DreamX-Lite Evaluation

## 1. Data Entities

### 1.1. Input Data
- **Camera Pose Matrix**: 4x4 homogeneous transformation matrix (float32). Represents ground-truth extrinsics.
- **Video Frame**: Numpy array (H, W, C, uint8).
- **Camera Prompt**: String description of the desired camera trajectory.

### 1.2. Derived Data
- **Video Rollout**: MP4 file containing 10 seconds of generated frames.
- **Recovered Trajectory**: Sequence of 4x4 matrices estimated by SfM (after Procrustes alignment).
- **Metric Record**: JSON/CSV row containing MAE, convergence flag, scale drift, and failure reason.

## 2. Data Schema

The primary output of the evaluation pipeline is a structured record of metrics for each trajectory. The `metrics.schema.yaml` is the **Single Source of Truth (SSoT)** for the final report.

### `metrics_record` Schema

```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
  trajectory_id:
    type: string
    description: "Unique identifier for the trajectory (e.g., 'traj_001')."
  model_variant:
    type: string
    enum: ["baseline", "dreamx-lite"]
    description: "The model variant used for generation."
  camera_prompt:
    type: string
    description: "The text prompt used to guide the camera."
  ground_truth_extrinsics:
    type: array
    description: "List of 4x4 matrices (flattened) for ground-truth poses."
    items:
      type: array
      items:
        type: number
      minItems: 16
      maxItems: 16
  recovered_extrinsics:
    type: array
    description: "List of 4x4 matrices (flattened) recovered by SfM (after Procrustes alignment)."
    items:
      type: array
      items:
        type: number
      minItems: 16
      maxItems: 16
  convergence:
    type: boolean
    description: "True if SfM converged, False otherwise."
  sfm_failure_reason:
    type: string
    nullable: true
    description: "Reason for SfM failure if convergence is false (e.g., 'insufficient features')."
  sfm_status:
    type: string
    enum: ["success", "failure", "censored"]
    description: "Status of SfM recovery. 'censored' if SfM failed but depth-consistency is available."
  mae_position:
    type: number
    nullable: true
    description: "Mean Absolute Error for position (normalized units, after Procrustes alignment). Null if failed."
  mae_rotation:
    type: number
    nullable: true
    description: "Mean Absolute Error for rotation (degrees, after Procrustes alignment). Null if failed."
  scale_drift:
    type: number
    description: "Ratio of mean depth (recovered) to mean depth (ground-truth) after alignment."
  generation_time_seconds:
    type: number
    description: "Time taken to generate the video rollout."
  sfm_time_seconds:
    type: number
    description: "Time taken for SfM recovery."
  info_sufficiency_ratio:
    type: number
    nullable: true
    description: "Ratio of DreamX-Lite success rate to Baseline success rate (SC-005). Null per-trajectory, computed at aggregate level."
required:
  - trajectory_id
  - model_variant
  - camera_prompt
  - convergence
  - sfm_status
  - mae_position
  - mae_rotation
  - scale_drift
```

## 3. Data Flow

1. **Ingestion**: `code/utils/io.py` downloads DreamX-World subset (or ScanNet fallback) and checksums it.
2. **Generation**: `code/pipeline/generate.py` loads the model, applies the ablation (if Lite), and generates video files.
3. **Evaluation**: `code/pipeline/evaluate.py` runs SfM on video frames, performs Procrustes alignment, computes metrics, and writes `metrics_record` to `data/derived/metrics.csv`.
4. **Analysis**: `code/analysis/stats.py` reads `metrics.csv`, performs statistical tests (Hurdle Model), and outputs `data/derived/statistical_results.json`.

## 4. Constraints & Validation

- **Immutability**: Raw data in `data/raw/` is never modified.
- **Checksums**: All files in `data/raw/` must have a corresponding `.sha256` file.
- **Format**: Metrics must be stored in CSV for easy analysis and JSON for schema validation.
- **Independence**: The `evaluate.py` script must not import any `dreamx` internal modules.
- **Sentinel Handling**: `mae_position` and `mae_rotation` are `null` for failed cases, not -1.0, to prevent contamination of statistical tests.
