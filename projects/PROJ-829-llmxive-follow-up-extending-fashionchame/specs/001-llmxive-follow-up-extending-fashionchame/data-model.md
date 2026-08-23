# Data Model: 001-garment-text-fidelity

## Overview

This document defines the data structures, schemas, and flows for the `001-garment-text-fidelity` feature. All data artifacts are versioned and checksummed as per Constitution Principle V.

## Key Entities

### 1. GarmentFeatureClass
An enumeration of the visual attributes being tested.
- `COLOR`: Global color attributes.
- `PATTERN`: Local pattern density (e.g., plaid, stripes).
- `TEXTURE`: Surface roughness/material properties (e.g., silk, wool).

### 2. FidelityScore
A quantitative metric record for a single frame or clip.
- `clip_id`: Unique identifier for the video clip.
- `feature_class`: One of `COLOR`, `PATTERN`, `TEXTURE`.
- `lpips_score`: Float (0.0 - 1.0). Lower is better.
- `ssim_score`: Float (0.0 - 1.0). Higher is better.
- `optical_flow_variance`: Float. Measures motion coherence.
- `latency_ms`: Float. Inference time per frame.
- `source_mode`: `TEXT` or `IMAGE` (baseline).

### 3. TextPrompt
A natural language description with metadata.
- `prompt_text`: The string description.
- `feature_class`: The tag assigned by the VLM.
- `vlm_confidence`: Float (0.0 - 1.0).
- `is_verified`: Boolean (True if confidence >= 0.8).

### 4. InferenceLog
A record of the execution state.
- `timestamp`: ISO8601 string.
- `clip_id`: String.
- `frame_id`: Integer.
- `status`: `SUCCESS`, `FAIL`, `OOM`, `SKIP`.
- `error_message`: String (if failed).

### 5. MotionLabel
Binary label derived from skeletal data.
- `clip_id`: String.
- `label`: `CORRECT` or `INCORRECT`.
- `velocity_threshold`: Float (e.g., 0.5 m/s).

## Data Flow

1. **Ingestion**: `Human3.6M` (streamed) -> `Feasibility Filter` (VLM) -> `Stratified Subset`.
2. **Processing**:
   - Input: `TextPrompt` + `Video Frame`.
   - Model: `FashionChameleon` (Text Adapter) -> `Generated Frame`.
   - Metrics: `LPIPS`, `SSIM`, `Optical Flow` calculated against `Ground Truth Frame`.
3. **Aggregation**: Metrics aggregated per `feature_class` and `source_mode`.
4. **Analysis**: ANOVA, Sensitivity Sweep.
5. **Output**: `fidelity_report.json`, `latency_log.csv`, `manifest.json`.

## File Artifacts

| Path | Description | Format |
|------|-------------|--------|
| `data/raw/h36m_stream_manifest.json` | Checksums and metadata for streamed shards | JSON |
| `data/processed/fidelity_scores.parquet` | Aggregated metrics for all clips | Parquet |
| `data/processed/latency_log.csv` | Per-frame latency measurements | CSV |
| `data/processed/anova_results.json` | Statistical test results | JSON |
| `data/processed/sensitivity_analysis.csv` | Threshold sweep results | CSV |
| `data/manifest.json` | Content hashes for all artifacts | JSON |

## Schema Definitions

See `contracts/fidelity_report.schema.yaml` and `contracts/dataset_manifest.schema.yaml` for formal JSON Schema definitions.
