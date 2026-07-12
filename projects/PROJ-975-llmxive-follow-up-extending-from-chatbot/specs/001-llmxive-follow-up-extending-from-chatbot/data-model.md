# Data Model: llmXive follow-up: extending "From Chatbot to Digital Colleague"

## Overview

This document defines the data structures used in the synthetic experiment. The data model is designed to be lightweight, JSON-native, and strictly typed to support contract testing.

## Entity Definitions

### 1. Skill
A Python function with an associated embedding vector and metadata.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `skill_id` | string | Unique identifier (e.g., "skill_001") | Unique, non-empty |
| `code_snippet` | string | The Python function code | Valid Python syntax |
| `embedding` | list[float] | Vector representation | Length 384 (for MiniLM) |
| `semantic_group` | string | Category for overlap control | Low, Medium, High |
| `usage_count` | integer | Number of times used in experiment | >= 0 |

### 2. Task
A synthetic multi-step problem requiring specific skills.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `task_id` | string | Unique identifier (e.g., "task_001") | Unique, non-empty |
| `description` | string | Natural language description | Non-empty |
| `ground_truth_path` | list[string] | Ordered list of skill_ids required | Length 3-5, all exist in library |
| `complexity` | integer | Number of steps | 3, 4, or 5 |

### 3. ExperimentLog
A record of a single task execution within a specific configuration.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `run_id` | string | Unique run identifier | Unique |
| `task_id` | string | Reference to task | Exists in dataset |
| `library_size` | integer | Size of active library | 10, 30, 50, or 100 |
| `pruning_enabled` | boolean | Whether pruning was active | True/False |
| `execution_success` | boolean | Did retrieved code run and match output? | True/False |
| `retrieval_precision` | float | Jaccard similarity (retrieved vs ground truth) | 0.0 to 1.0 |
| `retrieval_diversity` | float | Inverse variance of similarities | >= 0 |
| `pruning_risk_count` | integer | Number of high-risk skills pruned | >= 0 |
| `latency_ms` | float | Execution time | >= 0 |
| `token_usage` | integer | Tokens consumed | >= 0 |

## File Formats

- **`data/raw/skills.json`**: Array of `Skill` objects.
- **`data/raw/tasks.json`**: Array of `Task` objects.
- **`data/results/experiment_log.csv`**: CSV representation of `ExperimentLog` (flattened for analysis).

**Metric Mapping**:
- `execution_success`: Primary outcome metric (Execution Fidelity).
- `retrieval_precision`: Secondary diagnostic metric (Retrieval Fidelity).
- `retrieval_diversity`: Diagnostic metric for noise collapse.
- `pruning_risk_count`: Diagnostic metric for pruning intervention safety.

## Relationships

- **Task -> Skills**: Many-to-Many (via `ground_truth_path`).
- **ExperimentLog -> Task**: Many-to-One.
- **ExperimentLog -> Configuration**: Many-to-One (implied by `library_size` and `pruning_enabled`).