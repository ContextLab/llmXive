# Data Model: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Overview

This document defines the data structures used to represent Skill Vectors, Evaluation Results, and the configuration for the retrieval system. All data is stored in CPU-friendly formats (NumPy, CSV, JSON) to ensure compatibility with the GitHub Actions runner.

## Entities

### 1. Skill Vector
Represents a single LoRA adapter flattened and normalized.

*   **ID**: Unique string (e.g., `alfworld_task_001`).
*   **Task Description**: Text string describing the task.
*   **Vector**: 1D float32 array (L2 normalized).
*   **Source**: Original dataset name (ALFWorld or Search-QA).
*   **Dimensions**: Total elements = sum of elements in A and B matrices.

### 2. Composite Task
A novel task formed by combining existing skills, used for evaluation.

*   **ID**: Unique string.
*   **Description**: Text description.
*   **Ground Truth**: (Optional) The actual LoRA weights if available for reconstruction error calculation (SC-005).

### 3. Evaluation Result
Record of a single task run.

*   **Task ID**: Reference to Composite Task.
*   **Method**: `nearest_neighbor`, `arithmetic_mean`, `weighted_mean`, `baseline`.
*   **Run ID**: Integer (1 to N).
*   **Success**: Boolean (1/0).
*   **Latency**: Float (seconds for selection only).
*   **Timestamp**: ISO 8601.

### 4. Statistical Summary
Aggregated results for reporting.

*   **Method**: Strategy name.
*   **Mean Success**: Float.
*   **Std Dev**: Float.
*   **P-Value**: Float (raw).
*   **P-Value BH**: Float (corrected).
*   **Significant**: Boolean.

## Storage Formats

*   **Skill Vector Database**: `data/processed/skill_vectors.npy` (NumPy array) + `data/processed/skill_metadata.json`.
*   **Evaluation Logs**: `data/results/eval_log.csv`.
*   **Synthesized Adapters**: `artifacts/synthesized_adapters/{task_id}_{method}.npz`.

## Data Lineage

1.  **Raw**: `data/raw/{task_id}_A.npy`, `data/raw/{task_id}_B.npy` (Downloaded).
2.  **Processed**: `data/processed/skill_vectors.npy` (Derived via `src/ingestion/flatten_lora.py`).
3.  **Derived**: `data/results/eval_log.csv` (Derived via `src/evaluation/runner.py`).
4.  **Final**: `data/results/stats_summary.json` (Derived via `src/evaluation/stats.py`).
