# Data Model: MobileForge Logic Distillation

## Overview

This document defines the data structures, schemas, and transformation logic for the `ExtractionDataset`, `DistilledModel` artifacts, and `EvaluationResult` metrics. All data is processed according to the **Data Hygiene** principle (checksummed, immutable raw, derived new files).

## Entity Definitions

### 1. ExtractionDataset
The intermediate dataset containing `(UI_state, Corrective_Hint, Action)` triples.

*   **Source**: `data/raw/mobileforge_logs.csv` (derived from verified Hugging Face URL).
*   **Filtering**: Only "failed-then-success" trajectories with purely linguistic hints.
*   **Format**: Parquet (compressed).
*   **Schema**:
    *   `triples`: List of objects.
        *   `ui_state_description` (string): Non-empty text describing the UI state.
        *   `corrective_hint` (string): Non-empty text hint, no coordinates.
        *   `optimal_action_sequence` (string): JSON list of actions or comma-separated string.
        *   `trajectory_id` (string): Unique identifier for the source trajectory.
        *   `source_app` (string): App name from metadata.

### 2. DistilledModel
The lightweight, CPU-optimized language model (T5-small).

*   **Format**: Hugging Face `transformers` directory (config.json, pytorch_model.bin, tokenizer).
*   **Constraints**: ≤ 100M parameters, CPU-only weights.
*   **Metadata**:
    *   `training_seed` (int): Random seed used.
    *   `final_loss` (float): Loss at end of training.
    *   `training_time_hours` (float): Duration.

### 3. EvaluationResult
The output metrics for a specific task run.

*   **Format**: CSV or JSON Lines.
*   **Schema**:
    *   `task_id` (string): Unique ID of the AndroidWorld task.
    *   `model_type` (string): "distilled", "baseline_tinyllama", or "ablation_retry".
    *   `success` (boolean): Task completed successfully.
    *   `steps_taken` (int): Number of actions executed.
    *   `optimal_steps` (int): Ground truth steps.
    *   `inconsistency_tolerance` (float): Threshold used for matching.
    *   `execution_time_sec` (float): Inference time.
    *   **Generation Logic for `ablation_retry`**: The `corrective_hint` is replaced with a generic "Try again" prompt during inference.

## Transformation Pipeline

1.  **Download**: `download_mobileforge.py` fetches raw CSV from verified URL.
    *   *Output*: `data/raw/mobileforge_logs.csv` (checksum recorded).
2.  **Extract**: `extract_triples.py` filters raw logs.
    *   *Input*: `data/raw/mobileforge_logs.csv`.
    *   *Logic*: Regex for coordinates, status checks.
    *   *Output*: `data/processed/extraction_dataset.parquet`.
3.  **Train**: `train_distilled.py` consumes Parquet.
    *   *Output*: `models/distilled_model/`.
4.  **Evaluate**: `run_tasks.py` consumes model and AndroidWorld tasks.
    *   *Output*: `data/processed/evaluation_results.csv`.

## Data Integrity & Checksums

*   **Raw Data**: SHA-256 checksum recorded in `state/...yaml` upon download.
*   **Derived Data**: SHA-256 checksum recorded for `extraction_dataset.parquet` and `evaluation_results.csv`.
*   **Immutability**: Raw files are never modified. All transformations write to new files.