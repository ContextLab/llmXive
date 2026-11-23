# Data Model: llmXive follow-up: extending "MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru"

## Overview

This document defines the data schemas and transformations used in the pipeline. All data artifacts are stored in `data/processed/` (intermediate) and `data/results/` (final outputs).

## Entities

### 1. Trajectory Instance
A single motion event extracted from the MolmoMotion dataset.
- **Fields**:
  - `instance_id`: Unique identifier (string).
  - `ground_truth_points`: List of 3D coordinates `[[x1, y1, z1], [x2, y2, z2], ...]`.
  - `kinematic_metadata`: Object containing `velocity_vector` (list of 3 floats), `duration` (float).
  - `raw_index`: Original index in the MolmoMotion dataset.

### 2. Instruction Pair
The dual-modality input generated for a trajectory instance.
- **Fields**:
  - `instance_id`: Foreign key to Trajectory Instance.
  - `instruction_nl`: String (Coarse Natural Language, e.g., "move fast right").
  - `instruction_struct`: String (Structured Kinematic, e.g., "vel=[...], dur=...").
  - `synthesis_status`: Enum (`success`, `skipped`, `error`).
  - `nl_embedding_vector`: List of floats (16-dim, pre-computed for the NL Head).

### 3. Prediction Output
The model's output for a specific instruction modality.
- **Fields**:
  - `instance_id`: Foreign key.
  - `instruction_type`: Enum (`nl`, `structured`).
  - `predicted_points`: List of 3D coordinates.
  - `ate`: Float (Average Trajectory Error).
  - `adherence_score`: Float (Cosine similarity of direction).
  - `latency_ms`: Float (Inference time).
  - `status`: Enum (`success`, `nan`, `inf`, `error`).

## Data Flow

1.  **Raw Download**: `trajectories.parquet` -> `data/raw/`.
2.  **Subsampling**: `trajectories.parquet` -> `data/processed/subsampled_instances.parquet` (filtered, sampled).
3.  **Synthesis**: `subsampled_instances.parquet` -> `data/processed/instruction_pairs.jsonl`.
4.  **Inference**: `instruction_pairs.jsonl` + Model -> `data/results/predictions.jsonl`.
5.  **Analysis**: `predictions.jsonl` -> `data/results/ate_comparison.csv` + `data/results/t_test_results.json`.

## Storage Format

- **Intermediate Data**: `Parquet` (columnar, efficient for subsampling) or `JSONL` (streaming friendly).
- **Final Results**: `CSV` (for tabular metrics) and `JSON` (for structured test results).
- **Checksums**: All files in `data/` are accompanied by a `.sha256` checksum file.

## Model Input/Output Specifications

- **Structured Head Input**: `[velocity_x, velocity_y, velocity_z, duration, t_0, t_1, ..., t_T]`
- **NL Head Input**: `[nl_embedding_0, ..., nl_embedding_15, t_0, t_1, ..., t_T]`
- **Output**: `[x_0, y_0, z_0, x_1, y_1, z_1, ..., x_T, y_T, z_T]`