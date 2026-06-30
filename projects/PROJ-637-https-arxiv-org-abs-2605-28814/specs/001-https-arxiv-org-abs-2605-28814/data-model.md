# Data Model: Reproduce & Validate Bidirectional Evolutionary Search (BES)

## Overview

This document defines the data structures used by the BES pipeline, focusing on the input configuration, the search state, and the output artifacts. The data model is designed to be serializable to YAML/JSON for validation against the contracts defined in `contracts/`.

## Entities

### 1. SearchConfig
Configuration for a single BES run.
- `task_name`: String (e.g., "circle_packing").
- `num_candidates`: Integer (Target number of solutions to generate).
- `max_generations`: Integer (Limit on evolutionary steps).
- `timeout_minutes`: Integer (Max runtime per task).
- `model_config`: Object (LLM provider details).

### 2. SearchState
The internal state of the search process.
- `forward_pool`: List of Candidate objects.
- `goal_tree`: Tree structure representing backward decomposition.
  - `root`: Node.
  - `nodes`: List of Node objects.
- `event_log`: List of Event objects.

### 3. Candidate
A generated solution artifact.
- `id`: String (UUID).
- `content`: String (The code/text artifact).
- `generation_step`: Integer.
- `parent_ids`: List of String (References to parents).
- `evaluation_result`: Object (Score, validity flags).

### 4. Event
A log entry for search dynamics.
- `timestamp`: ISO 8601 String.
- `type`: Enum ["forward_expansion", "backward_decomposition", "evaluation", "timeout"].
- `details`: Object (Context-specific data).

### 5. EvaluationResult
The output of `evaluate.py`.
- `candidate_id`: String.
- `is_valid`: Boolean.
- `score`: Float (0.0 to 1.0).
- `constraints_violated`: List of String (e.g., "circle_overlap", "out_of_bounds").

## Relationships

- `SearchConfig` drives the creation of `SearchState`.
- `SearchState` contains a list of `Candidate` and `Event`.
- `EvaluationResult` is attached to a `Candidate` after the `evaluate.py` step.
- `Event` logs the transitions between states (e.g., a `backward_decomposition` event creates new nodes in `goal_tree`).

## Data Flow

1. **Input**: `SearchConfig` is loaded from `config/local_openai_config.py` or CLI args.
2. **Execution**: `run_evo.py` initializes `SearchState`.
3. **Loop**:
   - `forward_expansion` event -> New `Candidate` added to `forward_pool`.
   - `backward_decomposition` event -> New nodes added to `goal_tree`.
   - `evaluation` event -> `EvaluationResult` generated for `Candidate`.
4. **Output**: Final `SearchState` (including `goal_tree` and `evaluation_result`) is serialized to `inference/results/circle_packing/run_*.json`.
