# Data Model: EvoMem-Conflict Filtering

## Overview

This document defines the data structures used for the `EvoMem-Conflict` feature. All data is stored in JSON/CSV formats to ensure portability and reproducibility.

## Entity Definitions

### 1. Memory Patch
A discrete record of a state change.
- `patch_id`: Unique string identifier.
- `timestamp`: ISO 8601 string.
- `content`: String (the state description or command).
- `source`: String (e.g., "user_command", "system_log").
- `is_conflict`: Boolean (set by detector).
- `confidence_score`: Float (0.0 - 1.0).

### 2. Task Instance
A single experiment run unit.
- `task_id`: Unique string.
- `ground_truth_commands`: List of strings (expected terminal commands).
- `expected_state_history`: List of `MemoryPatch` objects (full history).
- `seed`: Integer (for reproducibility).

### 3. Execution Log
Record of an agent's action on a task.
- `run_id`: Unique string.
- `task_id`: Reference to `Task Instance`.
- `agent_variant`: Enum (`EvoMem-All`, `EvoMem-Conflict`).
- `step`: Integer.
- `retrieved_patches`: List of `patch_id`.
- `context_tokens`: Integer.
- `inference_time_ms`: Float.
- `command_executed`: String (actual command run).
- `success`: Boolean (command matches ground truth).
- `hallucination_detected`: Boolean.
- `hallucination_reason`: String (e.g., "wrong_command", "state_mismatch", "command_execution_failure").
- `normalized_ground_truth_similarity`: Float (0.0 - 1.0).

### 4. Analysis Result
Aggregated metrics for a task.
- `task_id`: String.
- `variant`: String.
- `accuracy`: Float (0.0 - 1.0).
- `hallucination_rate`: Float.
- `avg_tokens`: Float.
- `p_value`: Float (from Wilcoxon test, if applicable).

## Data Flow

1.  **Generation**: `terminal_bench_evo_generator.py` creates `Task Instance` JSONs.
2.  **Detection**: `conflict_detector.py` processes patches, outputs `is_conflict` and `confidence_score`.
3.  **Execution**: `agents/` generate `Execution Log` CSVs.
4.  **Analysis**: `analysis/stats.py` produces `Analysis Result` JSONs.

## Hallucination Metric Definition
To satisfy **SC-002**, a hallucination is recorded if:
1.  The `command_executed` does not match any command in `ground_truth_commands` (Incorrect Command Execution).
2.  **OR** the `normalized_ground_truth_similarity` (string similarity between the agent's state description and the Normalized Ground Truth) is < 0.90.