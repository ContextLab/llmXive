# Data Model: Social Memory Networks

## Overview
This document defines the data structures, schemas, and relationships required for the Social Memory Networks simulation. It ensures that the `run_experiment.py` script produces outputs strictly adhering to the `contracts/` schemas.

## Key Entities

### 1. Agent
Represents a single LLM instance participating in the simulation.
-   **Attributes**:
    -   `agent_id`: Unique identifier (string).
    -   `model_name`: Name of the underlying LLM (string).
    -   `memory_actions`: List of actions performed (write/read) during the game.
    -   `generated_text`: Raw text generated in the last turn.

### 2. MemoryBuffer
The shared external store.
-   **Attributes**:
    -   `key`: Unique identifier for the fact (string).
    -   `value`: The content of the fact (string).
    -   `timestamp`: ISO 8601 timestamp of the write (float/string).
    -   `owner_agent_id`: ID of the agent that wrote the fact (string).
    -   `cue`: Associated cue string (string, optional).

### 3. GameResult
A single row in the output CSV representing one simulated game.
-   **Attributes**:
    -   `game_id`: Unique identifier (string).
    -   `specialization_index`: Float (0 to log₂(N)).
    -   `retrieval_efficiency`: Float (0 to 1).
    -   `context_condition`: "full" or "limited".
    -   `agent_count`: Integer (3, 5, or 7).
    -   `token_limit`: Integer (128, 256, 512, or "unlimited").

## Data Flow

1.  **Input**: Raw dataset (Parquet/CSV) -> Parsed into `GameContext` objects.
2.  **Simulation**: `GameContext` + `Agent` instances + `MemoryBuffer` -> `InteractionLog` (JSON).
3.  **Metric Calculation**: `InteractionLog` -> `GameResult` (CSV).
4.  **Analysis**: `GameResult` (CSV) -> `ANOVA_Table` (JSON) + `Scaling_Plot` (PDF).

## Storage Strategy

-   **Raw Data**: Stored in `data/raw/` with original filenames. Checksums recorded.
-   **Derived Data**:
    -   `data/derived/results_full.csv`: Baseline metrics.
    -   `data/derived/results_limited.csv`: Truncated context metrics.
    -   `data/derived/scaling_data.csv`: Aggregated data for power-law fitting.
    -   `data/derived/interaction_logs/`: Per-game JSON logs (optional, for debugging).
-   **Logs**: `experiment.log` (append-only, timestamped).

## Schema Definitions

The following schemas are defined in `contracts/` and must be validated before analysis proceeds.

### Output Schema (GameResult)
See `contracts/game_result.schema.yaml` for the strict definition of the CSV columns.

### Interaction Log Schema
See `contracts/interaction_log.schema.yaml` for the structure of the per-game JSON logs.

## Constraints

-   **Determinism**: Given the same seed and input data, the `GameResult` values must be identical.
-   **Bounds**: `specialization_index` must be within [0, log₂(N_agents)].
-   **Completeness**: No missing values in `results_*.csv` (SC-001).
-   **Size**: `MemoryBuffer` size must not exceed 500MB per game to prevent disk overflow.

## Synthetic Cue Generator Algorithm

If the dataset lacks explicit cue annotations, the system will generate synthetic cues using the following algorithm:
1.  **N-gram Extraction**: Extract N-grams (n=3 to 5) from the dialogue turns.
2.  **Random Sampling**: Randomly sample these N-grams to create cue-response pairs.
3.  **Minimum Count**: Ensure a minimum of 10 synthetic cues per game.
