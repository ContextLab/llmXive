# Data Model: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Overview

This document defines the data structures for the synthetic experiment. All data is stored in JSON (raw) and CSV (results) formats.

## Entities

### 1. Task

A multi-step problem requiring a specific sequence of skills.

**Source**: `data/raw/tasks.json`
**Contract**: `contracts/task.schema.yaml`

**Attributes**:
- `task_id`: string (UUID)
- `description`: string (Natural language description)
- `complexity`: integer (3-5)
- `ground_truth_skills`: list of strings (Skill IDs)
- `solution_path`: list of strings (Ordered list of function calls)

### 2. Skill

A Python function capability with an embedding vector.

**Source**: `data/raw/skills.json`
**Contract**: `contracts/skill.schema.yaml`

**Attributes**:
- `skill_id`: string (UUID)
- `name`: string (Function name)
- `code`: string (Python source code)
- `embedding`: list of floats (768-dim vector)
- `usage_count`: integer (Runtime metric)
- `last_used`: timestamp (ISO 8601)

### 3. Experiment Log

Record of a single task execution.

**Source**: `data/results/metrics.csv`
**Contract**: `contracts/experiment_log.schema.yaml`

**Attributes**:
- `run_id`: string
- `task_id`: string
- `library_size`: integer
- `pruning_enabled`: boolean
- `success`: boolean
- `latency_ms`: float
- `tokens_used`: integer
- `retrieval_precision`: float (0.0-1.0)
- `retrieval_diversity`: float
- `edge_case`: string (e.g., "missing_skill", "memory_limit", "null")

## Data Flow

1. **Generation**: `generate_data.py` creates `tasks.json` and `skills.json`.
2. **Execution**: `agent.py` reads tasks/skills, writes rows to `metrics.csv`.
3. **Analysis**: `analysis.py` reads `metrics.csv`, computes PLR, VIF.
4. **State**: `state/...yaml` is updated with checksums of `tasks.json`, `skills.json`, and `metrics.csv`.

## Constraints

- **Immutability**: `tasks.json` and `skills.json` are read-only during execution.
- **Append-Only**: `metrics.csv` is appended to; no in-place edits.
- **Schema Validation**: All JSON files must pass `jsonschema` validation before use.
