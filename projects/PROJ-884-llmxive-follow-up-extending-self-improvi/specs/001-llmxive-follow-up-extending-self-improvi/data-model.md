# Data Model: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

## 1. Overview

This document defines the data structures for the `001-symbolic-bes` project. The model supports the curation of logic puzzles, the execution of the hybrid BES loop, and the recording of statistical results. All data is stored in local files (`data/raw/`, `data/processed/`) with checksums for reproducibility (Constitution Principle III).

## 2. Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    PUZZLE_INSTANCE ||--|{ SOLUTION_ATTEMPT : "generates"
    PUZZLE_INSTANCE ||--|| VERIFIER_SCRIPT : "has"
    SOLUTION_ATTEMPT ||--|{ EVALUATION_LOG : "produces"
    EVALUATION_LOG ||--|| STATISTICAL_RESULT : "aggregates_to"
    
    PUZZLE_INSTANCE {
        string puzzle_id PK
        string puzzle_type
        string constraints
        string initial_state
        string target_state
        string verifier_script_path
        int complexity_score
    }
    
    SOLUTION_ATTEMPT {
        string attempt_id PK
        string puzzle_id FK
        string method "symbolic" | "neural"
        string generation
        string solution_text
        float cost_time
        float cost_energy
    }
    
    EVALUATION_LOG {
        string log_id PK
        string attempt_id FK
        boolean is_valid
        string error_code "valid" | "PARSE_FAILURE" | "CONTRADICTION_DETECTED" | "INVALID_PATH"
        string timestamp
    }
    
    STATISTICAL_RESULT {
        string result_id PK
        string method
        float success_rate
        float mean_time
        float p_value_z
        float p_value_t
        float logical_contradiction_rate
    }
```

## 3. Data Schemas

### 3.1 Puzzle Instance Schema
- **Source**: `data/raw/puzzles.jsonl` (or generated on-the-fly).
- **Fields**:
  - `puzzle_id`: Unique string (UUID or hash).
  - `puzzle_type`: Enum (e.g., "sudoku_4x4", "pathfinding_grid").
  - `constraints`: String (formal language representation).
  - `initial_state`: String/JSON (starting configuration).
  - `target_state`: String/JSON (goal configuration).
  - `verifier_script`: Relative path to `data/raw/verifiers/<puzzle_id>.py`.
  - `complexity_score`: Integer (N) for scaling analysis.

### 3.2 Solution Attempt Schema
- **Source**: `data/processed/bes_runs/<run_id>/attempts.jsonl`.
- **Fields**:
  - `attempt_id`: Unique string.
  - `puzzle_id`: FK to Puzzle Instance.
  - `method`: "symbolic" or "neural".
  - `generation`: Integer (0 to N).
  - `solution_text`: String (LLM output).
  - `cost_time`: Float (seconds).
  - `cost_energy`: Float (Joules, estimated).

### 3.3 Evaluation Log Schema
- **Source**: `data/processed/bes_runs/<run_id>/evaluations.jsonl`.
- **Fields**:
  - `log_id`: Unique string.
  - `attempt_id`: FK to Solution Attempt.
  - `is_valid`: Boolean (from verifier).
  - `error_code`: String (if invalid, e.g., "PARSE_FAILURE", "CONTRADICTION_DETECTED", "INVALID_PATH").
  - `timestamp`: ISO 8601.

### 3.4 Statistical Result Schema
- **Source**: `data/processed/analysis/results.json`.
- **Fields**:
  - `run_id`: String.
  - `method`: "symbolic" or "neural".
  - `total_instances`: Integer.
  - `excluded_instances`: Integer (symbolic planner failures).
  - `success_count`: Integer.
  - `success_rate`: Float.
  - `mean_time`: Float.
  - `std_time`: Float.
  - `p_value_z`: Float (success rate comparison - TOST).
  - `p_value_t`: Float (time comparison).
  - `significance`: Boolean (p < 0.05).
  - `logical_contradiction_rate`: Float (rate of 'CONTRADICTION_DETECTED' errors).

## 4. Data Flow

1. **Curation**: `code/dataset/generator.py` creates `puzzle_id`, `constraints`, `initial_state`, `target_state`, `complexity_score` and writes `verifier_script` to `data/raw/`.
2. **Execution**: `code/main.py` loads puzzles, runs BES loop (Symbolic/Neural), and writes `solution_text` and `cost_time` to `data/processed/bes_runs/`.
3. **Verification**: `code/dataset/verifier.py` is called for each `solution_text`, writing `is_valid` and `error_code` to `data/processed/bes_runs/`.
4. **Analysis**: `code/analysis/stats.py` aggregates logs, performs TOST/t-test, and writes `results.json`.

## 5. Integrity & Validation

- **Checksums**: All files in `data/raw/` and `data/processed/` are checksummed (SHA-256) and recorded in `state/...yaml`.
- **Immutability**: Raw data is never modified. Derivations (logs, results) are written to new files.
- **Validation**: `code/dataset/verifier.py` must return a boolean and error code for every input; no silent failures.