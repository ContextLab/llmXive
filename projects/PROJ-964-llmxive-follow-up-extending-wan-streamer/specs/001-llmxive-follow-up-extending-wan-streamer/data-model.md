# Data Model: llmXive follow-up: extending "Wan-Streamer v0.1"

## Overview

This document defines the data schemas for the research pipeline. All data is stored in Parquet format for efficient columnar access and compression.

## Entities

### 1. `LatentTrajectory`
Time-series record of audio-visual latent vectors.
- **Source**: Extracted from Wan-Streamer v0.1 logs.
- **Granularity**: Per-frame.

### 2. `TurnTakingEvent`
Labeled segment of interaction.
- **Source**: Derived from semantic/prosodic features.
- **Granularity**: Per-frame (with event type label).

### 3. `EstimatorPrediction`
Output of the lightweight GRU model.
- **Source**: Inference pipeline.
- **Granularity**: Per-frame.

### 4. `HybridOutputMetrics`
Aggregated metrics for the hybrid inference run.
- **Source**: Metrics computation script.
- **Granularity**: Per-segment / Per-run.

## Schema Definitions

### Table: `extracted_latents`
| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `timestamp` | `int64` | Unix timestamp of the frame. | Non-null, unique per segment. |
| `segment_id` | `string` | Identifier for the conversation segment. | Non-null. |
| `semantic_feature` | `float32` | Semantic embedding vector (flattened or PCA reduced). | Non-null. |
| `prosodic_feature` | `float32` | Prosodic features (energy, pitch, duration). | Non-null. |
| `latent_delta_magnitude` | `float32` | Magnitude of the latent vector displacement ($||z_t - z_{t-1}||$). | Non-null, $\ge 0$. |
| `turn_label` | `string` | Label: "interruption", "pause", "normal". | Non-null, enum. |
| `is_high_priority` | `boolean` | Derived: True if "interruption" or `latent_delta` > threshold. | Non-null. |

### Table: `estimator_predictions`
| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `timestamp` | `int64` | Frame timestamp. | Non-null. |
| `segment_id` | `string` | Segment identifier. | Non-null. |
| `predicted_delta` | `float32` | Predicted magnitude of the next latent delta. | Non-null. |
| `uncertainty_score` | `float32` | Confidence score (0.0 to 1.0). | Non-null, range [0, 1]. |
| `action` | `string` | "skip" or "solve". | Non-null, enum. |
| `actual_delta` | `float32` | Ground truth delta (for validation). | Non-null. |

### Table: `hybrid_metrics`
| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `run_id` | `string` | Unique identifier for the simulation run. | Non-null. |
| `baseline_latency_ms` | `float32` | Latency of full flow-matching baseline. | Non-null. |
| `hybrid_latency_ms` | `float32` | Latency of hybrid pipeline. | Non-null. |
| `latency_reduction_pct` | `float32` | Percentage reduction. | Non-null. |
| `baseline_fid` | `float32` | FID of baseline generation. | Non-null. |
| `hybrid_fid` | `float32` | FID of hybrid generation. | Non-null. |
| `fid_degradation_pct` | `float32` | Percentage degradation. | Non-null. |
| `proxy_mos` | `float32` | Proxy Mean Opinion Score. | Non-null. |
| `tost_p_value` | `float32` | P-value from TOST equivalence test. | Non-null. |
| `bootstrap_p_value` | `float32` | P-value from stratified bootstrap. | Non-null. |

## Data Flow

1.  **Raw Logs** (`data/raw/`) → `extract_logs.py` → `extracted_latents.parquet`
2.  `extracted_latents.parquet` → `train_estimator.py` → `estimator_model.pth`
3.  `extracted_latents.parquet` + `estimator_model.pth` → `hybrid_pipeline.py` → `estimator_predictions.parquet`
4.  `estimator_predictions.parquet` + `baseline_output` → `metrics.py` → `hybrid_metrics.parquet`

## Constraints & Validations

- **Turn Label Consistency**: `turn_label` must be one of: "interruption", "pause", "normal".
- **Uncertainty Range**: `uncertainty_score` must be in $[0.0, 1.0]$.
- **Delta Non-Negative**: `latent_delta_magnitude` and `predicted_delta` must be $\ge 0$.
- **No PII**: No personally identifiable information is stored in `extracted_latents`.
