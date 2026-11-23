# Data Model: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

## 1. Overview
Defines the schema for puzzle instances, solution attempts, evaluation logs, and aggregated statistical results. All files conform to the JSON‑Schema contracts located in `contracts/`.

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
        string verifier_script
        int complexity_score
    }

    SOLUTION_ATTEMPT {
        string attempt_id PK
        string puzzle_id FK
        string method "symbolic" | "neural"
        int generation
        string solution_text
        float cost_time
        float cost_energy
    }

    EVALUATION_LOG {
        string log_id PK
        string attempt_id FK
        bool is_valid
        string error_code "valid" | "PARSE_FAILURE" | "CONTRADICTION_DETECTED" | "INVALID_PATH"
        string timestamp
    }

    STATISTICAL_RESULT {
        string result_id PK
        string method
        float success_rate
        float feasibility_rate "ratio of puzzles where symbolic planner succeeded"
        float mean_time
        float std_time
        float p_value_z
        float p_value_t
        bool significance
        float logical_contradiction_rate
    }
```

## 3. Schemas

- **Puzzle Instance** – `contracts/dataset.schema.yaml`  
- **BES Run Output** – `contracts/output.schema.yaml` (includes optional `feasibility_rate`).  

These schemas are validated against generated JSONL/JSON files during Phase 1 (tasks 1.8 & 1.9).

## 4. Data Flow
1. `generator.py` → writes a JSON object with a `"puzzles"` list (conforms to `dataset.schema.yaml`).  
2. `main.py` loads puzzles, runs the BES loop, writes solution attempts to `attempts.jsonl`.  
3. `verifier.py` consumes each `solution_text`, produces `evaluation_log` entries.  
4. `stats.py` aggregates logs into a single `STATISTICAL_RESULT` JSON (`output.schema.yaml`).  

## 5. Integrity & Validation
- **Checksums**: SHA‑256 recorded in `state/...yaml`.  
- **Immutability**: Raw puzzle files never altered after creation.  
- **Validation**: Unit tests (`tests/unit/test_generator.py`, `tests/unit/test_symbolic_planner.py`) assert schema conformity.

---

