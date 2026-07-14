# Data Model: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

## Overview

This document defines the data structures, schemas, and persistence strategy for the project. All data is stored in JSON/CSV formats with strict checksumming for reproducibility.

## Entities

### Task Instance
A specific experimental task from ResearchClawBench.
- **Fields**: `task_id`, `description`, `hidden_target_paper`, `failure_mode`, `domain`, `metadata`.
- **Source**: ResearchClawBench dataset.

### Protocol Scaffold
A static, domain-specific procedural template.
- **Fields**: `template_id`, `version`, `content_path`, `constraint_keywords`.
- **Source**: `assets/templates/`.

### Execution Log
The complete trace of an agent's interaction.
- **Fields**: `run_id`, `task_id`, `agent_id`, `condition` (Zero-Shot/Scaffolded), `start_time`, `end_time`, `status` (Success/Timeout/Error), `output_text`, `prompt_snapshot`.
- **Storage**: `results/logs/`.

### Score Pair
Linked scores for a single task instance under both conditions.
- **Fields**: `task_id`, `zero_shot_protocol`, `zero_shot_core`, `scaffolded_protocol`, `scaffolded_core`, `diff_protocol`, `diff_core`.
- **Storage**: `results/paired_scores.json`.

### Constraint Keywords
A list of keywords used to detect scaffold-task conflicts.
- **Fields**: `keywords` (list of strings).
- **Source**: `contracts/constraint_keywords.yaml`.

## File Formats

### Input: Dataset Subset (`data/processed/10_tasks_protocol_mismatch.json`)
```json
[
  {
    "task_id": "RCB-001",
    "description": "...",
    "failure_mode": "experimental protocol mismatch",
    "domain": "chemistry"
  },
  ...
]
```

### Input: Rubric Schema (`contracts/rubric_schema.json`)
See `contracts/rubric_schema.json` for the full schema.

### Input: Constraint Keywords (`contracts/constraint_keywords.yaml`)
```yaml
# FR-007: Constraint keywords for conflict detection
keywords:
  - "temperature"
  - "pressure"
  - "pH"
  - "solvent"
  - "catalyst"
  - "reaction_time"
  - "concentration"
  - "atmosphere"
  - "stirring_rate"
  - "light_exposure"
```

### Output: Execution Log (`results/logs/run_{run_id}.json`)
```json
{
  "run_id": "uuid-1234",
  "task_id": "RCB-001",
  "agent_id": "agent-7",
  "condition": "Scaffolded",
  "start_time": "2026-07-12T10:00:00Z",
  "end_time": "2026-07-12T11:30:00Z",
  "status": "Success",
  "output_text": "...",
  "prompt_snapshot": "..."
}
```

### Output: Paired Scores (`results/paired_scores.json`)
```json
[
  {
    "task_id": "RCB-001",
    "zero_shot_protocol": 25,
    "zero_shot_core": 40,
    "scaffolded_protocol": 45,
    "scaffolded_core": 38,
    "diff_protocol": 20,
    "diff_core": -2
  },
  ...
]
```

### Output: Failure Mode Audit (`results/failure_mode_audit.csv`)
```csv
task_id,dominant_failure_mode,expected_mode,match
RCB-001,experimental protocol mismatch,experimental protocol mismatch,true
RCB-002,retrieval_failure,experimental protocol mismatch,false
```

## Checksum & Versioning
- **Raw Data**: `data/raw/` files are checksummed on fetch.
- **Derived Data**: `data/processed/` files are checksummed on creation (T008).
- **State File**: `state/projects/PROJ-957-.../artifact_hashes` maps file paths to SHA-256 hashes.
- **Reproducibility**: Any change to input data invalidates downstream results; state file is updated.
