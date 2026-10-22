# Data Model: llmXive follow-up: extending "ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain"

**Feature**: `001-llmxive-static-proxy`  
**Date**: 2026‑10‑22  

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **VideoSegment** | A contiguous egocentric video clip (e.g., of short duration) with associated ground‑truth dynamic reliability score. | `segment_id` (str), `video_path` (str), `duration_s` (float), `dynamic_reliability` (float) |
| **StaticFeatureVector** | Aggregated static cues for a `VideoSegment`. | `segment_id` (str), `entropy_mean` (float), `entropy_std` (float), `hand_conf_mean` (float), `hand_conf_std` (float), `lighting_mean` (float), `lighting_std` (float), `timestamp_mean` (float), `exposure_mean` (float), `focal_length_mean` (float) |
| **TemporalWindowFeatures** | Optical‑flow statistics for a defined temporal window length. | `segment_id` (str), `window_sec` (int), `flow_mag_mean` (float), `flow_mag_std` (float), `flow_dir_hist` (list[float] of length 8) |
| **RegressionPrediction** | Output of the static‑only model. | `segment_id` (str), `predicted_reliability` (float), `prediction_std` (float) |
| **StaticResidual** | Residual error between prediction and dynamic reliability. | `segment_id` (str), `residual` (float) |
| **VLAExperimentResult** | Success/failure for a single benchmark episode. | `model_variant` (enum[dynamic, uniform, static_proxy]), `benchmark` (enum[robocasa, robotwin]), `episode_id` (str), `success` (bool) |

## File Formats
- **Static features** → CSV (`data/static_features.csv`).  
- **Temporal features** → CSV (`data/temporal_features_{window}s.csv`).  
- **Regression predictions** → CSV (`data/static_predictions.csv`).  
- **Static residuals** → CSV (`data/static_residuals.csv`).  
- **Benchmark results** → CSV (`results/vla_{variant}_{benchmark}.csv`).  

All CSVs must conform to the schema defined in `contracts/static_features.schema.yaml` (static features) and analogous schemas for temporal, prediction, residual, and VLA result files.

## Relationships
- One `VideoSegment` ⇢ one `StaticFeatureVector`.  
- One `VideoSegment` ⇢ up to four `TemporalWindowFeatures` (different windows).  
- `RegressionPrediction` references the same `segment_id`.  
- `StaticResidual` references the same `segment_id`.  
- `VLAExperimentResult` references a `model_variant` and a `benchmark` but not a specific video segment (downstream evaluation).

## Data Lineage
1. Raw videos → **VideoSegment** (no modification).  
2. Extraction scripts → **StaticFeatureVector** (new file).  
3. Temporal script → **TemporalWindowFeatures** (new file).  
4. Regression model → **RegressionPrediction** (new file).  
5. Residual computation → **StaticResidual** (new file).  
6. Filtering step (FR‑007) → subset of `VideoSegment` IDs used for VLA training.  
7. VLA training → model checkpoints (binary).  
8. Benchmark evaluation → **VLAExperimentResult** (new file).  

All transformations are pure functions; original video files remain unchanged.

---

