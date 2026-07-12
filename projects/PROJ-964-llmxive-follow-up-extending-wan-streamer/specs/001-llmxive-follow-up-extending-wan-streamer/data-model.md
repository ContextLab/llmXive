# Data Model: llmXive follow-up

## 1. Overview

This document defines the data structures for the `llmXive` follow-up project. All data flows from the extraction phase (raw logs/VoxCeleb2) through preprocessing (labeled time-series) to model training and hybrid simulation. The schema definitions in `contracts/` serve as the source of truth for validation.

**Note on FID Calculation**: FID is a batch metric. All FID-related metrics in this model are computed over *segments* (windows of frames) or the *entire sequence*, not individual frames. The term "frame" in the spec (FR-010, SC-003) is interpreted as "segment" for the purpose of FID stability calculation.

## 2. Data Entities

### 2.1 Raw Input (Source)
*   **Wan-Streamer Logs**: JSON/Parquet logs containing latent vectors, timestamps, and metadata.
*   **VoxCeleb2**: Audio-visual sequences with speaker IDs. Used as a fallback to generate proxy latents.

### 2.2 Extracted Dataset (Processed)
*   **File Format**: Parquet (compressed).
*   **Granularity**: Per-segment (aggregated from per-frame data).
*   **Key Fields**:
    *   `segment_id`: Integer (Unique identifier for the segment/window).
    *   `timestamp`: Float (Start time of the segment).
    *   `turn_label`: Categorical (`"interruption"`, `"pause"`, `"normal"`).
    *   `semantic_feature`: Vector (float32) representing text/content embedding (averaged over segment).
    *   `prosodic_feature`: Vector (float32) representing audio energy/pitch (averaged over segment).
    *   `latent_delta_magnitude`: Float (Average Euclidean distance of latent vectors within the segment).
    *   `uncertainty_target`: Float (optional, derived from model error in training).

### 2.3 Model Output (Prediction)
*   **File Format**: Pickle/Onnx (model weights) + JSON (predictions).
*   **Fields**:
    *   `predicted_delta`: Float.
    *   `predicted_uncertainty`: Float (0.0–1.0).
    *   `action`: Categorical (`"skip"`, `"full_solve"`).

### 2.4 Simulation Metrics (Result)
*   **File Format**: CSV/Parquet.
*   **Fields**:
    *   `segment_id`: Integer.
    *   `latency_ms`: Float.
    *   `fid_score`: Float (FID computed over the segment).
    *   `proxy_mos`: Float.
    *   `skip_action`: Boolean.
    *   `randomized_intervention`: Boolean (True if forced skip).
    *   `fid_stability`: Float (Relative change in FID between skipped and full-solver versions of the segment).

## 3. Data Flow

1.  **Extraction**: `extract_latents.py` reads raw logs/VoxCeleb2 → Outputs `data/processed/extracted.parquet`.
    *   *Contract*: `contracts/dataset.schema.yaml`.
2.  **Preprocessing**: `preprocess.py` normalizes features, splits train/val/test → Outputs `data/processed/train.parquet`, `data/processed/val.parquet`.
3.  **Training**: `trainer.py` loads `train.parquet` → Trains `EstimatorModel` → Outputs `data/artifacts/model.pt`.
4.  **Simulation**: `hybrid_sim.py` loads `model.pt` and `val.parquet` → Runs hybrid pipeline → Outputs `data/artifacts/simulation_metrics.parquet`.
    *   *Contract*: `contracts/model_output.schema.yaml`, `contracts/metrics.schema.yaml`.
5.  **Validation**: `stats_tests.py` reads `simulation_metrics.parquet` → Computes TOST/Bootstrap → Outputs `data/artifacts/statistical_results.json`.

## 4. Schema Definitions

See `contracts/` directory for detailed YAML schemas:
*   `dataset.schema.yaml`: Validates the extracted time-series data.
*   `model_output.schema.yaml`: Validates the estimator predictions.
*   `metrics.schema.yaml`: Validates the simulation results.

## 5. Assumptions & Constraints

*   **Missing Data**: If `Wan-Streamer` logs are missing, `VoxCeleb2` is used. The `latent_delta_magnitude` will be derived, not native.
*   **PII**: No Personally Identifiable Information is stored. VoxCeleb2 is public; Wan-Streamer logs are assumed anonymized.
*   **Storage**: All intermediate files are deleted after processing if not needed for final artifacts to stay within 14 GB disk limit.
*   **FID Granularity**: FID is computed over segments (batches) to ensure mathematical validity.