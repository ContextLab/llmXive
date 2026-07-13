# Data Model: llmXive Follow-up: Extending "Enhancing Train-Free Infinite-Frame Generation for Consistent Long Vid"

## Overview

This document defines the data structures, schemas, and relationships for the project. It ensures that all data generated, processed, and analyzed adheres to the "Single Source of Truth" principle (Constitution Principle IV) and is validated against the contracts defined in `contracts/`.

## Entity Definitions

### 1. VideoSequence
Represents a generated video clip associated with a specific prompt and experimental condition.
- **id**: Unique identifier (UUID or hash of prompt + condition).
- **prompt_id**: Reference to the original prompt.
- **condition**: Enum: `baseline_full`, `baseline_naive`, `flow_corrected`.
- **file_path**: Relative path to the video file in `data/processed/`.
- **duration_sec**: Duration in seconds.
- **frame_count**: Total number of frames.
- **resolution**: Tuple (width, height).
- **generation_time_sec**: Wall-clock time taken to generate.

### 2. FlowField
Represents the optical flow vectors between two consecutive frames.
- **sequence_id**: Reference to the parent VideoSequence.
- **frame_pair_id**: Unique ID for the pair (frame_i, frame_i+1).
- **file_path**: Relative path to the flow field file (e.g., `.npy` or `.pt`).
- **mean_magnitude**: Average pixel displacement magnitude.
- **max_magnitude**: Maximum pixel displacement magnitude.
- **failure_flag**: Boolean indicating if fallback logic was used.

### 3. ConsistencyMetric
Quantitative scores for a VideoSequence.
- **sequence_id**: Reference to the VideoSequence.
- **metric_name**: Enum: `vbench_temporal`, `object_permanence`, `fvd`.
- **score**: Float value.
- **model_version**: Version of the evaluation model used.
- **timestamp**: Time of calculation.

### 4. FailureCase
A record of a video where the flow correction failed to maintain perceptual stability.
- **sequence_id**: Reference to the VideoSequence.
- **failure_type**: Enum: `permanence_drop`, `consistency_drop`, `artifact_tearing`, `3d_geometric_collapse`.
- **baseline_score**: Score from Condition B.
- **corrected_score**: Score from Condition C.
- **drop_percentage**: Calculated drop (e.g., `(baseline - corrected) / baseline`).
- **reason**: String explanation.
- **qualitative_note**: Optional note on 3D geometric collapse observed.

## Data Flow

1.  **Ingestion**: Raw datasets (Parquet/Tar) are downloaded to `data/raw/` and checksummed.
2.  **Generation**: `generate.py` produces `VideoSequence` artifacts in `data/processed/`.
3.  **Correction**: `correct.py` produces `FlowField` and corrected `VideoSequence` artifacts.
4.  **Evaluation**: `evaluate.py` produces `ConsistencyMetric` records.
5.  **Analysis**: `analyze.py` aggregates metrics, performs statistical tests, and produces `FailureCase` records.
6.  **Output**: Final results are written to `data/results/summary.csv` and `data/results/statistics.json`.
7.  **Validation**: All data writes are validated against schemas in `contracts/` before proceeding.

## Schema Validation

All data written to disk (CSV, JSON, Parquet) MUST conform to the schemas defined in `contracts/`. The Implementer Agent will use these schemas to validate data integrity before proceeding to the next phase.

-   `contracts/dataset.schema.yaml`: Validates raw and processed dataset metadata.
-   `contracts/metrics.schema.yaml`: Validates the structure of the results CSV and statistical output.

## Assumptions & Constraints

-   **File Formats**: Videos are stored as `.mp4` (H.264) for compatibility; flow fields as `.npy` (NumPy) for CPU efficiency.
-   **Precision**: Floating-point scores are stored with 4 decimal places.
-   **Immutability**: Once a file is written to `data/raw/` or `data/processed/`, it is never modified. Derivations create new files.