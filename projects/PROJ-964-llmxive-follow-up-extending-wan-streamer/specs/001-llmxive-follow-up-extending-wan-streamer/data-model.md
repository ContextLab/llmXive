# Data Model: llmXive follow-up: extending "Wan-Streamer v0.1"

## Overview

This document defines the data structures used throughout the project, ensuring alignment with the `contracts/` schemas and the requirements of the `spec.md`. All data is stored in `data/` with checksums recorded in `state.yaml`.

## Entity Definitions

### 1. LatentTrajectory
A time-series record of audio-visual latent vectors.
*   **Purpose**: Represents the state of the generation model at each timestep.
*   **Key Fields**:
    *   `timestamp`: Unix timestamp or frame index.
    *   `latent_vector`: Float32 array (flattened).
    *   `latent_delta_magnitude`: Scalar (Euclidean distance to previous frame).
    *   `turn_label`: Enum (`interruption`, `pause`, `normal`).

### 2. TurnTakingEvent
A labeled segment of interaction.
*   **Purpose**: Provides the semantic/prosodic context for the estimator.
*   **Key Fields**:
    *   `event_type`: `interruption` or `pause`.
    *   `start_time`, `end_time`: Duration in seconds.
    *   `semantic_features`: Vector (e.g., ASR embeddings).
    *   `prosodic_features`: Vector (e.g., pitch, energy, zero-crossing).

### 3. EstimatorInput
Input to the lightweight RNN/Transformer.
*   **Purpose**: Causal history of signals.
*   **Key Fields**:
    *   `history_window`: List of `TurnTakingEvent` features (last N frames).
    *   `current_frame_index`: Integer.

### 4. EstimatorOutput
Prediction from the lightweight model.
*   **Purpose**: Decision support for skipping.
*   **Key Fields**:
    *   `predicted_delta`: Scalar (predicted `latent_delta_magnitude`).
    *   `uncertainty_score`: Scalar (0.0-1.0).
    *   `skip_decision`: Boolean (derived from uncertainty threshold).

### 5. HybridOutput
Result of the hybrid inference pipeline.
*   **Purpose**: Final generated sequence.
*   **Key Fields**:
    *   `frame_index`: Integer.
    *   `generation_method`: `skipped` (estimated) or `full` (flow-matching).
    *   `latency_ms`: Inference time for this frame.
    *   `is_counterfactual`: Boolean (was this frame forced to skip?).

### 6. MetricsAggregation
Aggregated results for validation.
*   **Purpose**: Summary statistics for reporting.
*   **Key Fields**:
    *   `metric_name`: `fid`, `proxy_mos`, `latency`.
    *   `baseline_value`: Float.
    *   `hybrid_value`: Float.
    *   `relative_change`: Float.
    *   `p_value`: Float (from statistical tests).
    *   `equivalence_passed`: Boolean.

## Data Flow

1.  **Raw Data** (`data/raw/`) -> **Extraction** (`code/data/extract_turn_taking.py`) -> **Processed Dataset** (`data/processed/turn_taking_dataset.parquet`).
2.  **Processed Dataset** -> **Training** (`code/model/estimator_train.py`) -> **Model Checkpoint** (`data/artifacts/estimator.pt`).
3.  **Processed Dataset** + **Model Checkpoint** -> **Simulation** (`code/model/hybrid_simulate.py`) -> **Hybrid Results** (`data/processed/hybrid_results.parquet`).
4.  **Hybrid Results** -> **Metrics** (`code/metrics/...`) -> **Metrics JSON** (`data/artifacts/metrics.json`).

## Schema References

*   `contracts/dataset.schema.yaml`: Defines the structure of `turn_taking_dataset.parquet`.
*   `contracts/output.schema.yaml`: Defines the structure of `hybrid_results.parquet` and `metrics.json`.
