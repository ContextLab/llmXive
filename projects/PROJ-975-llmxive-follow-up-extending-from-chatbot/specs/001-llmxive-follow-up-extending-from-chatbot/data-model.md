# Data Model: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Overview

Defines JSON and CSV structures used throughout the experiment. All files are validated against the schemas in `contracts/`.

## Entities

### 1. Task (`data/raw/tasks.json`)

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string (UUID) | Unique identifier. |
| `description` | string | Natural‑language description of the task. |
| `complexity` | integer (3‑5) | Number of steps in the solution path. |
| `ground_truth_skills` | list[string] | IDs of the skills that must be executed (3‑5 items). |
| `solution_path` | list[string] | Ordered list of function calls representing the deterministic solution. |

### 2. Skill (`data/raw/skills.json`)

| Field | Type | Description |
|-------|------|-------------|
| `skill_id` | string (UUID) | Unique identifier. |
| `name` | string | Function name. |
| `code` | string | Full Python source code of the skill. |
| `embedding` | list[float] (768) | 768‑dimensional semantic vector. |
| `usage_count` | integer ≥ 0 | Times the skill has been retrieved/executed. |
| `last_used` | string (ISO‑8601) | Timestamp of most recent use. |

### 3. Experiment Log (`data/results/metrics.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | string | Identifier for the experiment configuration (library size, pruning flag, overlap level). |
| `task_id` | string | Reference to the task. |
| `library_size` | integer (10 | 30 | 50 | 100) | Active skill library size at execution time. |
| `pruning_enabled` | boolean | Whether the pruning heuristic was active. |
| `success` | boolean | Task completed correctly (ground‑truth matched). |
| `latency_ms` | number | Execution latency in milliseconds. |
| `tokens_used` | integer | Estimated token count for the simulated LLM call. |
| `retrieval_precision` | number ∈ [0, 1] | Jaccard similarity between top‑5 retrieved skills and ground‑truth set. |
| `retrieval_diversity` | number | Inverse variance of cosine similarities of the top‑5 retrieved skills to the ground‑truth set. |
| `edge_case` | string | Tag for special conditions (`"missing_skill"`, `"memory_limit"`, `"null"` etc.). |

## Data Flow

1. **Generation** – `generate_data.py` creates `tasks.json` & `skills.json`, computes SHA‑256 checksums, and writes them to `state/projects/PROJ-975-...yaml`.  
2. **Validation** – Contract tests (`pytest tests/contract/`) ensure JSON files conform to `task.schema.yaml` & `skill.schema.yaml`.  
3. **Execution** – `agent.py` reads the raw files, runs the experiment loop, and appends rows to `metrics.csv` using the logger from `logging_config.py`.  
4. **Analysis** – `analysis.py` reads `metrics.csv`, fits the PLR, computes VIF, performs hypothesis tests, and writes `analysis_report.json`.  
5. **State Update** – After analysis, the state YAML is updated with a second checksum for `metrics.csv` and a timestamp.

## Constraints

* **Immutability** – `tasks.json` & `skills.json` are read‑only after generation.  
* **Append‑Only Log** – `metrics.csv` is only ever appended; no in‑place edits.  
* **Schema Validation** – Every read/write step validates against the corresponding schema; failures abort the CI run.

---
