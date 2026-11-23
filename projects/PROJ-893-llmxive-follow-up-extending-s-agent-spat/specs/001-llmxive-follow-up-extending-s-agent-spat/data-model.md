# Data Model: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

## Overview

This document defines the data structures used to transport information between the extraction, solving, and benchmarking phases. All data is stored in `data/` (raw) and `data/derived/` (processed).

## Entity Definitions

### 1. StaticScene
Represents a single static multi-view environment.
- **scene_id**: Unique identifier (string).
- **source_dataset**: Name of the source (e.g., "S-Agent-300K" or "Pilot/Csplk/hipcam").
- **geometry_raw**: Raw JSON/Parquet blob containing 3D coordinates and relations.
- **ground_truth_label**: The correct answer (integer count or relative position string).
- **vlm_baseline_prediction**: The prediction from the original VLM (if available).
- **exclusion_reason**: Null if included, or string (e.g., "missing_geometry", "missing_semantic_label") if excluded.

### 2. ConstraintSystem
The input to the CSP solver.
- **scene_id**: Link to `StaticScene`.
- **variables**: List of variable definitions (e.g., `{"name": "obj_A", "domain": [0, 1, 2, 3], "semantic_label": "cup"}`).
- **constraints**: List of constraint definitions (e.g., `{"type": "left_of", "args": ["obj_A", "obj_B"]}`).
- **task_type**: "counting" or "positioning".
- **gt_projection_status**: "Satisfies", "Violates", "Unknown". (Populated in Phase 3 for failure analysis).

### 3. SpatialPrediction
The output of the CSP solver.
- **scene_id**: Link to `StaticScene`.
- **predicted_answer**: The solver's output (integer or string).
- **solver_status**: "Solved", "No Solution", "Ambiguous", "Timeout".
- **inference_time_ms**: Wall-clock time in milliseconds.
- **solver_log**: Optional debug string (truncated).
- **constraint_completeness_check**: Boolean. True if the solver could verify the constraint graph was fully connected and domains were non-empty (used for internal debugging, not the primary failure category).

### 4. BenchmarkResult
The final comparative record.
- **scene_id**: Link to `StaticScene`.
- **symbolic_prediction**: From `SpatialPrediction`.
- **vlm_prediction**: From `StaticScene`.
- **ground_truth**: From `StaticScene`.
- **symbolic_correct**: Boolean.
- **vlm_correct**: Boolean.
- **latency_symbolic_ms**: Float.
- **failure_category**: "None", "Geometric Ambiguity", "Semantic Gap", "Other".
- **gt_projection_result**: "Satisfies" (if GT satisfies constraints) or "Violates" (if GT violates constraints). This is the *primary* determinant for the failure category.

### 5. DistributionalValidityRecord
The record of the Distributional Validity Gate check.
- **dataset_name**: Name of the dataset being validated.
- **reference_dataset**: Name of the reference dataset (e.g., "S-Agent-300K").
- **p_values**: Dictionary of p-values for KS-tests (e.g., `{"object_density": 0.45, "spatial_variance": 0.02}`).
- **is_valid_proxy**: Boolean. True if all p > 0.05 or if documentation confirms equivalence.
- **validation_method**: "KS-test", "Documentation Review", or "Unverified".
- **gate_status**: "PASS", "FAIL", or "ABORTED".

## Data Flow

1.  **Raw Download**: `data/raw/*.zip`, `data/raw/*.parquet`, `data/raw/*.csv` (Verified sources).
2.  **Distributional Check**: `data/derived/distributional_validity.json` (DistributionalValidityRecord). **GATE**: If FAIL, stop.
3.  **Extraction**: `data/derived/constraints.jsonl` (ConstraintSystem).
4.  **Solving**: `data/derived/predictions.jsonl` (SpatialPrediction).
5.  **Benchmarking**: `data/derived/benchmark_results.csv` (BenchmarkResult).

## Versioning & Checksums

- All files in `data/` are checksummed (SHA-256) upon creation.
- Checksums are recorded in `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml`.
- No file in `data/` is modified in place.