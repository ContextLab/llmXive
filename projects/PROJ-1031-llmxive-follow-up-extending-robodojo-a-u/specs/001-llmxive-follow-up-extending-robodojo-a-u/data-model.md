# Data Model: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

## 1. Entity Relationship Overview

The data model consists of three primary entities: `SymbolicState`, `ActionSequence`, and `ExecutionOutcome`. These entities are linked by task execution traces.

```mermaid
erDiagram
    TASK_SPEC ||--o{ ACTION_SEQUENCE : "generates"
    ACTION_SEQUENCE ||--o{ EXECUTION_OUTCOME : "results_in"
    TASK_SPEC ||--o{ EXECUTION_OUTCOME : "validated_by"
    TASK_SPEC ||--o{ COMPUTE_METRIC : "measured_by"
    
    TASK_SPEC {
        string task_id
        string description
        string initial_state
        string goal_state
    }
    
    ACTION_SEQUENCE {
        string sequence_id
        string task_id
        list<SymbolicState> states
        list<string> actions
    }
    
    EXECUTION_OUTCOME {
        string outcome_id
        string sequence_id
        boolean success
        string failure_mode
        int failure_step_index
        string ablation_variant
    }
    
    COMPUTE_METRIC {
        string metric_id
        string sequence_id
        float wall_clock_time
        float cpu_memory_mb
        float cpu_cycles
    }
```

## 2. Data Schemas

### 2.1. Semantic Embedding (Intermediate)
-   **Purpose**: High-level vector representation of visual observations.
-   **Storage**: `data/processed/embeddings/{task_id}.npy`
-   **Shape**: $(T, D)$ where $T$ is time steps and $D$ is embedding dimension (e.g., 768).
-   **Content**: Float32 array. No metadata stored in the array itself; metadata in JSON sidecar.

### 2.2. Symbolic State Graph (Intermediate)
-   **Purpose**: Discrete state representation.
-   **Storage**: `data/processed/state_graphs/{task_id}.json`
-   **Format**: JSON graph (nodes and edges).
-   **Content**:
    -   Nodes: `{id, predicates: ["graspable", "on_table"], object_refs: [...]}`
    -   Edges: `{from_id, to_id, action_type}`

### 2.3. Execution Logs (Final)
-   **Purpose**: Raw results of real-world and oracle executions.
-   **Storage**: `data/interim/execution_logs.parquet`
-   **Columns**:
    -   `task_id`: Unique identifier for the task.
    -   `approach`: "symbolic" or "baseline" or "oracle".
    -   `success`: Boolean (True/False).
    -   `failure_mode`: String ("Planner Infeasibility", "Controller Execution Failure", "None").
    -   `failure_step_index`: Integer (index of failure, or -1 if success).
    -   `wall_clock_time`: Float (seconds).
    -   `cpu_memory_mb`: Float (Peak RAM usage).
    -   `ablation_variant`: String ("full_affordance" or "simplified_connectivity").

## 3. Data Lineage

1.  **Raw Input**: Parquet files from Hugging Face (RoboDojo).
2.  **Preprocessing**: `data_loader.py` extracts video frames and task metadata.
3.  **Embedding**: `vision_encoder.py` generates `SemanticEmbedding` (Numpy).
4.  **Abstraction**: `state_mapper.py` converts embeddings to `SymbolicState` graph (JSON).
5.  **Planning**: `planner.py` generates `ActionSequence` (JSON).
6.  **Execution**:
    -   Real-world: `controller_adapter.py` runs on robot -> `ExecutionOutcome` (Log).
    -   Oracle: `oracle_executor.py` runs in sim -> `ExecutionOutcome` (Log).
7.  **Aggregation**: `stats_analysis.py` reads logs -> `data/final/results.csv`.

## 4. Constraints & Validation

-   **Immutability**: Raw parquet files in `data/raw/` are never modified.
-   **Checksums**: All files in `data/raw/` and `data/processed/` have SHA-256 checksums recorded in `state/`.
-   **Schema Enforcement**: All JSON outputs must validate against the schemas defined in `contracts/`.
-   **No PII**: No personally identifiable information is stored. Only task IDs and anonymous performance metrics.