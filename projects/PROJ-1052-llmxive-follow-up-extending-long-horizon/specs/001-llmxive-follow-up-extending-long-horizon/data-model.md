# Data Model: llmXive Follow-up: Reward Fidelity vs. Error Recovery Density

## Overview
This document defines the data structures for the project's inputs, execution logs, and analysis results. All data is stored in `data/processed/` as CSVs or JSONL, with schemas defined in `contracts/`.

## Key Entities

### 1. TaskTrajectory
A sequence of agent actions, observations, and rewards for a single benchmark task.
- `task_id`: Unique identifier (string).
- `condition`: Experimental condition (`baseline`, `binary`, `dense_pruning`).
- `reward_fidelity_level`: Granularity of reward signal (`dense`, `binary`).
- `success`: Boolean (1/0).
- `tokens_consumed`: Integer.
- `recovery_segment_ids`: List of strings (IDs of context segments required for recovery).
- `pruned_segment_ids`: List of strings (IDs of segments removed).
- `state_diff_metric`: Float (magnitude of state change between pre-error and post-recovery).
- `semantic_similarity_score`: Float (similarity between segments, used for criticality).

### 2. RecoverySegment
A specific slice of the context window containing information necessary for the agent to self-correct.
- `segment_id`: Unique identifier.
- `task_id`: Reference to parent task.
- `start_token_idx`: Integer.
- `end_token_idx`: Integer.
- `contribution_score`: Float (0.0 to 1.0).
- `is_critical`: Boolean (True if contribution > 0.05).
- `state_diff_metric`: Float (contribution to state change).
- `semantic_similarity_score`: Float (similarity to recovery state).

### 3. AnalysisResult
Aggregated results for statistical modeling.
- `fidelity_level`: Categorical.
- `success_rate`: Float.
- `tokens_saved_pct`: Float.
- `p_value`: Float.
- `is_significant`: Boolean (after correction).
- `inflection_point_detected`: Boolean.
- `method_used`: String (`cochran_armitage`, `fisher_exact`).

## Data Flow

1.  **Input**: `AgentBench` (Raw) -> `data/raw/`.
2.  **Processing**:
    - `download.py` -> Validates checksum, moves to `data/raw/`.
    - `agent_runner.py` -> Generates `execution_logs.csv` (TaskTrajectory + RecoverySegment data).
    - `analysis.py` -> Generates `analysis_results.csv` (AnalysisResult).
3.  **Output**: `results/summary.md` (derived from `analysis_results.csv`).

## Schema References
- `execution_log.schema.yaml`: Validates `execution_logs.csv` (or JSONL).
- `analysis_result.schema.yaml`: Validates `analysis_results.csv`.

## Constraints

- **Data Hygiene**: Raw data is immutable. All derivations create new files.
- **Checksums**: SHA256 of raw data recorded in `state/...yaml`.
- **PII**: No PII in benchmark data (assumed clean).