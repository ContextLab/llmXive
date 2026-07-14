# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Overview

This document defines the data structures, schemas, and file formats used in the project. All data is stored in `data/` and validated against the contracts in `contracts/`.

## Entity Definitions

### VideoClip
A short video segment extracted from a public repository.
*   **Attributes**:
    *   `video_id`: Unique string identifier (e.g., `kinetics_001`).
    *   `source_url`: Original URL of the video (from manifest).
    *   `file_path`: Local path to the 16-frame clip.
    *   `frame_count`: Integer (always 16).
    *   `fps`: Integer (always 30).
    *   `has_cut`: Boolean (derived from stratified sampling metadata).

### ContinuityScore
Manual ground-truth label for a `VideoClip`.
*   **Attributes**:
    *   `video_id`: Foreign key to `VideoClip`.
    *   `score`: Float, range [0.0, 1.0].
    *   `annotator_id`: String (identifier for the human annotator).
    *   `timestamp`: ISO 8601 timestamp.

### DivergenceMetric
Computed instability metric for a `VideoClip`.
*   **Attributes**:
    *   `video_id`: Foreign key to `VideoClip`.
    *   `divergence_score`: Float (L2 distance).
    *   `euler_steps`: Integer (N=500 or N=200).
    *   `inference_time_sec`: Float.
    *   `status`: String ("success", "error", "skipped").

### CorrelationResult
Output of the statistical analysis.
*   **Attributes**:
    *   `pearson_r`: Float.
    *   `spearman_rho`: Float.
    *   `p_value`: Float.
    *   `relationship_type`: String ("Associational").
    *   `variance_score`: Float.

## File Formats

### `data/raw/clip_metadata.csv`
*   **Format**: CSV
*   **Columns**: `video_id`, `source_url`, `file_path`, `has_cut`
*   **Description**: Inventory of downloaded clips.

### `data/annotations/continuity_scores.csv`
*   **Format**: CSV
*   **Columns**: `video_id`, `score`, `annotator_id`, `timestamp`
*   **Description**: Manual ground-truth labels.

### `data/processed/divergence_metrics.csv`
*   **Format**: CSV
*   **Columns**: `video_id`, `divergence_score`, `euler_steps`, `inference_time_sec`, `status`
*   **Description**: Computed model instability metrics.

### `data/processed/correlation_results.json`
*   **Format**: JSON
*   **Description**: Final statistical results (Pearson, Spearman, p-value, variance).

### `data/processed/sensitivity_report.csv`
*   **Format**: CSV
*   **Columns**: `threshold`, `false_positive_rate`, `false_negative_rate`
*   **Description**: Sensitivity analysis for thresholds {0.01, 0.05, 0.1}.

### `data/processed/variance_report.csv`
*   **Format**: CSV
*   **Columns**: `metric`, `variance`, `threshold_met`
*   **Description**: Variance check for `continuity_score`.

## Data Flow

1.  **Ingestion**: `download.py` creates `clip_metadata.csv`.
2.  **Annotation**: Manual process creates `continuity_scores.csv`.
3.  **Inference**: `inference.py` creates `divergence_metrics.csv`.
4.  **Analysis**: `analysis.py` creates `correlation_results.json`, `sensitivity_report.csv`, `variance_report.csv`.

## Constraints

*   **Score Range**: `continuity_score` must be in [0.0, 1.0].
*   **Divergence**: `divergence_score` must be non-negative.
*   **Variance**: `variance_score` must be ≥ 0.05 for analysis to proceed.
*   **No PII**: No personally identifiable information in `data/`.
