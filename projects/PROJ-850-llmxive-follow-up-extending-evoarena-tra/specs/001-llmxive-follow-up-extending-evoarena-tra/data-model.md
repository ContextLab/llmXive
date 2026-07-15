# Data Model: EvoMem-Conflict Filtering

## Overview

This document defines the data structures, schemas, and storage formats for the EvoMem-Conflict project. All data is stored locally in `data/` and processed via Python scripts.

## Entities

### 1. Memory Patch
A discrete record of a state change.
- **Fields**:
  - `id`: Unique identifier (UUID).
  - `timestamp`: ISO 8601 string.
  - `content`: String (the state description or command).
  - `source`: String (origin of the patch).
  - `is_conflict`: Boolean (flag set by heuristic).
  - `confidence`: Float (0.0-1.0, probability of conflict).

### 2. Task Instance
A specific terminal command sequence requiring state tracking.
- **Fields**:
  - `task_id`: Unique identifier.
  - `initial_state`: String (description of starting state).
  - `goal`: String (desired end state).
  - `patches`: List of `MemoryPatch` objects.
  - `ground_truth_commands`: List of strings (expected commands).

### 3. Agent Execution Log
Record of a single task execution by an agent variant.
- **Fields**:
  - `run_id`: UUID.
  - `task_id`: FK to `TaskInstance`.
  - `agent_variant`: String (`EvoMem-All` or `EvoMem-Conflict`).
  - `step`: Integer (step number within the task execution).
  - `retrieved_patches_count`: Integer.
  - `retrieved_patches`: List of `MemoryPatch` IDs.
  - `context_tokens`: Integer.
  - `inference_time_ms`: Float (milliseconds).
  - `command_executed`: String (the actual terminal command executed).
  - `success`: Boolean.
  - `hallucination_detected`: Boolean.
  - `hallucination_reason`: String (e.g., "wrong_command", "state_mismatch", "command_execution_failure", "none").
  - `normalized_ground_truth_similarity`: Float (0.0-1.0, string similarity score).
  - `confidence_score`: Float (only for EvoMem-Conflict, null otherwise).
  - `additional_metadata`: Object (optional).

### 4. Statistical Result
Aggregated results from the analysis.
- **Fields**:
  - `test_type`: String (e.g., "McNemar").
  - `p_value`: Float.
  - `statistic`: Float.
  - `effect_size`: Float.
  - `noise_reduction_pct`: Float.
  - `threshold_used`: Float.

## File Formats

### Input Data (JSON)
- **Location**: `data/raw/synthetic_conflicts.json`, `data/raw/tasks.json`.
- **Format**: JSON array of objects.

### Execution Logs (CSV)
- **Location**: `data/logs/execution_logs.csv`.
- **Format**: CSV with headers: `run_id,task_id,agent_variant,step,retrieved_patches_count,retrieved_patches,context_tokens,inference_time_ms,command_executed,success,hallucination_detected,hallucination_reason,normalized_ground_truth_similarity,confidence_score,additional_metadata`.

### Checksums (YAML)
- **Location**: `state/projects/PROJ-850-.../artifact_hashes.yaml`.
- **Format**: YAML mapping filenames to SHA256 hashes.

## Data Flow

1. **Ingestion**: Raw data loaded from `data/raw/`.
2. **Processing**:
   - Synthetic conflicts generated (if needed).
   - Patches filtered by conflict detector.
   - Agent logs written to `data/logs/`.
3. **Analysis**: Logs aggregated into statistical results.
4. **Archiving**: All raw and processed data checksummed.