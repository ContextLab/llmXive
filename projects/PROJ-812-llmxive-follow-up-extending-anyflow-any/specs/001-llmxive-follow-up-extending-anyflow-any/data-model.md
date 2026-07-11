# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## 1. Overview

This document defines the data schemas for the `001-gene-regulation` feature. The data model supports three stages: Curation, Metric Calculation, and Analysis. All data is stored in CSV or JSON formats for simplicity and reproducibility.

## 2. Entities & Attributes

### 2.1 VideoClip
Represents a single video segment used in the study.
- `video_id` (str): Unique identifier (e.g., `ucf101_001`).
- `source` (str): Source dataset (e.g., `UCF101`, `Kinetics`, `DAVIS`).
- `file_path` (str): Relative path to the local video file.
- `duration` (float): Duration in seconds.
- `frame_count` (int): Number of frames (fixed at 16 for this study).

### 2.2 ContinuityScore (Ground Truth)
Manual annotation of temporal continuity.
- `video_id` (str): Foreign key to `VideoClip`.
- `score` (float): Temporal continuity score, range [0.0, 1.0].
- `annotator_id` (str): ID of the human annotator (for traceability).
- `timestamp` (str): ISO 8601 timestamp of annotation.
- `is_double_annotated` (bool): True if this clip was part of the [deferred] reliability check.

### 2.3 DivergenceMetric (Computed)
Computed flow-map divergence and external proxy.
- `video_id` (str): Foreign key to `VideoClip`.
- `divergence_score` (float): L2 distance between predicted and Euler-rolled states (Internal).
- `optical_flow_variance` (float): Variance of optical flow magnitude (External Proxy).
- `computation_time` (float): Time taken to compute (ms).
- `status` (str): `success` or `failed`.
- `error_msg` (str, optional): Error message if failed.
- `model_hash` (str): SHA-256 hash of the ONNX model used.
- `quantization_mode` (str): `float32` or `float16`.

### 2.4 CorrelationResult
Output of the statistical analysis.
- `metric_type` (str): `pearson` or `spearman`.
- `coefficient` (float): Correlation value ($r$ or $\rho$).
- `p_value` (float): Statistical significance.
- `sample_size` (int): Number of valid pairs.
- `framing` (str): Explicit statement on causality ("associational").
- `runtime_env` (str): "CPU-only (ONNX Runtime, no CUDA)".

### 2.5 SensitivityReport
Output of the threshold sensitivity analysis.
- `threshold` (float): The threshold value (e.g., 0.01).
- `true_positive_rate` (float): Recall.
- `false_positive_rate` (float): 1 - Specificity.
- `accuracy` (float): Overall accuracy.
- `binarization_rule` (str): "Score < 0.4 = 0, Score > 0.6 = 1".

### 2.6 ScoreDistribution
Output of the distribution analysis (SC-004).
- `mean_score` (float): Mean of manual scores.
- `variance_score` (float): Variance of manual scores.
- `min_score` (float): Minimum score.
- `max_score` (float): Maximum score.
- `sample_size` (int): Total number of annotated clips.

## 3. Data Flow

1.  **Raw Input**: Video files from UCF101/Kinetics/DAVIS.
2.  **Curation Output**: `data/raw/annotations.csv` (VideoClip + ContinuityScore).
3.  **Processing Output**: `data/processed/divergence_metrics.csv` (VideoClip + DivergenceMetric).
4.  **Analysis Output**: `data/processed/correlation_results.json`, `data/processed/sensitivity_report.json`, `data/processed/score_distribution.json`.

## 4. Constraints

- **Score Range**: `ContinuityScore.score` MUST be in [0.0, 1.0].
- **Uniqueness**: `video_id` MUST be unique across all datasets.
- **Immutability**: `data/raw/annotations.csv` MUST NOT be modified after initial creation.
- **Missing Data**: If `status` is `failed` in `DivergenceMetric`, the clip is excluded from correlation analysis.
- **Reliability**: If Krippendorff's Alpha < 0.6, the `data/raw/annotations.csv` is marked invalid.
- **Dependencies**: `requirements.txt` MUST pin `ucimlrepo` and `datasets` versions to ensure canonical source access.