# Data Model: llmXive follow-up: extending "COLLEAGUE.SKILL"

## 1. Overview

This document defines the data structures, schemas, and flows for the `llmXive` follow-up project. All data is stored in `data/` with checksums.

## 2. Entity Definitions

### 2.1 ExpertProfile
Represents a single expert persona with decoupled capability and behavior tracks.

**Fields**:
*   `profile_id`: Unique identifier (UUID).
*   `domain`: Domain of expertise (e.g., "Python Developer", "Mathematician").
*   `capability_track`: List of rules/heuristics (strings).
*   `behavior_track`: List of style definitions (keywords, tone, structure).
*   `seed`: Random seed used to generate this profile.

### 2.2 TaskScenario
A specific task instance with ground truth.

**Fields**:
*   `task_id`: Unique identifier.
*   `domain`: Task domain.
*   `prompt`: The user prompt.
*   `context_trace`: Ground-truth facts and logic steps (list of strings). Used for Hallucination Rate verification via logic chain checks.
*   `validation_rules`: Rules to check for Heuristic Adherence.
*   `exclusion_flag`: Boolean (True if context is ambiguous or task is malformed).

### 2.3 InferenceOutput
Raw output from the model.

**Fields**:
*   `run_id`: Unique run identifier.
*   `profile_id`: Reference to `ExpertProfile`.
*   `task_id`: Reference to `TaskScenario`.
*   `condition`: "Monolithic", "Separated", or "Generic".
*   `output_text`: Generated text.
*   `status`: "success", "timeout", "error", "oom".
*   `latency_ms`: Time taken.

### 2.4 EvaluationResult
Scored metrics.

**Fields**:
*   `run_id`: Reference to `InferenceOutput`.
*   `heuristic_adherence`: 0 or 1.
*   `hallucination_rate`: Float (0-1).
*   `style_consistency`: Float (0-1).
*   `exclusion_reason`: String (if excluded).

## 3. Data Flow

1.  **Generation**: `profile_generator.py` → `data/raw/profiles.jsonl`
2.  **Generation**: `task_generator.py` → `data/raw/tasks.jsonl` (with `exclusion_flag` for ambiguous tasks)
3.  **Inference**: `run_inference.py` reads profiles/tasks → `data/interim/inference_outputs.jsonl` (with `status: 'timeout'` or `'oom'` for failed runs)
4.  **Evaluation**: `score.py` reads inference outputs → `data/processed/evaluation_results.jsonl`
5.  **Analysis**: `stats.py` reads evaluation results → `data/processed/statistical_results.csv`

## 4. Schema Contracts

See `contracts/` directory for YAML schemas.