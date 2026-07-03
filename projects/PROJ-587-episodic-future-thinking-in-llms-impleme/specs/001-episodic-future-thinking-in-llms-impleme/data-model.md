# Data Model: Episodic Future Thinking in LLMs

## Overview

This document defines the data structures for the episodic memory module, planning tasks, and generated scenarios. All data is stored in local files (Parquet/JSONL) with checksums recorded in `data/checksums.txt`.

## Entity Definitions

### 1. EpisodicMemory

Stores individual planning steps as (state, action, outcome) tuples with semantic embeddings.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `episode_id` | `string` | Unique identifier for the trajectory. | UUID v4 |
| `step_id` | `integer` | Step index within the trajectory. | 0-based |
| `state_text` | `string` | Raw textual description of the environment state. | Max 500 chars |
| `action_text` | `string` | Raw textual description of the agent action. | Max 100 chars |
| `outcome_text` | `string` | Raw textual description of the environment response. | Max 500 chars |
| `state_embedding` | `array(float)` | Semantic embedding of `state_text`. | Dim=384 (MiniLM) |
| `action_embedding` | `array(float)` | Semantic embedding of `action_text`. | Dim=384 (MiniLM) |
| `timestamp` | `datetime` | Time of storage. | ISO 8601 |
| `confidence_score` | `float` | Confidence in the stored outcome (0.0-1.0). | Default 1.0 |
| `source_dataset` | `string` | Origin dataset (e.g., "alfworld", "textworld"). | Enum |

### 2. PlanningTask

Represents a benchmark task from ALFWorld or TextWorld.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `task_id` | `string` | Unique task identifier. | UUID v4 |
| `initial_state` | `string` | Starting environment description. | Max 1000 chars |
| `goal_state` | `string` | Target environment description. | Max 500 chars |
| `required_steps` | `integer` | Expected number of steps for ground truth. | > 0 |
| `episodic_dependencies` | `list(string)` | IDs of required episodic memories. | Optional |
| `ground_truth_solution` | `list(string)` | Sequence of correct actions. | Not null |
| `task_variant` | `string` | Category of task (e.g., "hidden_state", "non_deterministic"). | Enum |
| `is_episodic_necessity` | `boolean` | Flag indicating if task meets the pre-registered "episodic necessity" criteria (baseline accuracy < 40%). | Derived |

### 3. FutureScenario

Generated planning output combining episodic memories with current state.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `scenario_id` | `string` | Unique identifier. | UUID v4 |
| `task_id` | `string` | Reference to `PlanningTask`. | Foreign Key |
| `generated_plan` | `list(string)` | Sequence of generated actions. | Not null |
| `episodic_references` | `list(string)` | IDs of retrieved episodes used. | Optional |
| `counterfactual_details` | `list(object)` | Details marked as counterfactual/uncertain. | See below |
| `confidence_scores` | `object` | Confidence map for each step. | Float 0.0-1.0 |
| `coherence_score` | `float` | Human rating (1-5). | Optional |
| `rater_id` | `string` | ID of the human rater. | Optional |

**Counterfactual Details Object**:
```yaml
detail_id: string
text: string
is_known: boolean  # True if verifiable against ground truth
confidence: float
```

## Data Flow

1. **Ingestion**: Raw datasets (ALFWorld/TextWorld) are downloaded, checksummed, and parsed into `PlanningTask` and `EpisodicMemory` records.
2. **Indexing**: `EpisodicMemory` records are embedded and stored in FAISS HNSW index.
3. **Inference**: `PlanningTask` is queried against the index. Retrieved episodes are combined with current state to generate `FutureScenario`.
4. **Evaluation**: `FutureScenario` is compared against `ground_truth_solution`. Confidence scores are validated against perturbed data.
5. **Aggregation**: Results are aggregated by `task_variant` for Mixed-Effects Modeling.

## Storage Format

- **Raw Data**: Parquet (ALFWorld), JSONL (TextWorld).
- **Processed Data**: Parquet (efficient columnar storage for embeddings).
- **Index**: FAISS binary (`.index`).
- **Logs**: JSONL (execution logs, fallback events).

