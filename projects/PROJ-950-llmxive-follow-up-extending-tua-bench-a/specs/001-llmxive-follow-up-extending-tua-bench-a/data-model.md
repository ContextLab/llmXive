# Data Model: llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

## Overview
All artifacts are stored as JSON files under `data/`. The schemas below are expressed as JSON‑Schema (draft) and are enforced by the `contracts/execution_result.schema.yaml` contract.

### 1. Task (`task.schema.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Task",
  "type": "object",
  "required": ["task_id", "description", "validation_script", "task_type"],
  "properties": {
    "task_id": { "type": "string", "description": "Unique identifier (e.g., T001)" },
    "description": { "type": "string", "description": "Natural‑language description of the scientific workflow" },
    "validation_script": { "type": "string", "description": "Shell script that returns exit code 0 on success" },
    "task_type": { "type": "string", "enum": ["complex", "routine"], "description": "Complex multi‑step vs. single‑command" }
  }
}
```

### 2. MemoryEntry (`memory_entry.schema.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MemoryEntry",
  "type": "object",
  "required": ["entry_id", "command", "description", "embedding"],
  "properties": {
    "entry_id": { "type": "string", "description": "Unique identifier (e.g., M001)" },
    "command": { "type": "string", "description": "Exact shell command string" },
    "description": { "type": "string", "description": "Human‑written description of the command's purpose" },
    "embedding": {
      "type": "array",
      "items": { "type": "number" },
      "description": "Pre‑computed MiniLM embedding vector"
    }
  }
}
```

### 3. ExecutionResult (`execution_result.schema.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExecutionResult",
  "type": "object",
  "required": [
    "seed",
    "task_id",
    "condition",
    "k",
    "success",
    "error_type",
    "retrieved_ids",
    "false_positive",
    "execution_time_sec"
  ],
  "properties": {
    "seed": { "type": "integer", "minimum": 0, "maximum": 4 },
    "task_id": { "type": "string" },
    "condition": { "type": "string", "enum": ["baseline", "augmented"] },
    "k": { "type": ["integer", "null"], "description": "top‑k used; null for baseline" },
    "success": { "type": "boolean" },
    "error_type": {
      "type": "string",
      "enum": ["none", "syntax_error", "wrong_command", "infinite_loop", "timeout", "other"]
    },
    "retrieved_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "IDs of memory entries returned by retrieval (empty for baseline or miss)"
    },
    "false_positive": {
      "type": "boolean",
      "description": "True if any retrieved entry is not marked relevant for this task"
    },
    "execution_time_sec": { "type": "number", "minimum": 0 }
  }
}
```

### 4. AggregatedResult (`aggregated_result.schema.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AggregatedResult",
  "type": "object",
  "required": ["condition", "k", "overall_success_rate", "false_positive_rate", "retrieval_miss_rate", "failure_modes"],
  "properties": {
    "condition": { "type": "string", "enum": ["baseline", "augmented"] },
    "k": { "type": ["integer", "null"] },
    "overall_success_rate": { "type": "number", "minimum": 0, "maximum": 1 },
    "false_positive_rate": { "type": "number", "minimum": 0, "maximum": 1 },
    "retrieval_miss_rate": { "type": "number", "minimum": 0, "maximum": 1 },
    "failure_modes": {
      "type": "object",
      "additionalProperties": { "type": "integer" },
      "description": "Counts per error_type"
    }
  }
}
```

## Data Flow Diagram (high‑level)
```
synthetic_tasks.json ──► run_baseline.py ──► baseline_results/*.json
memory_bank.json ──► retrieval.py ──► run_augmented.py ──► augmented_results/k_*/seed_*.json
baseline/augmented JSONs ──► stats.py ──► stats/*.json + results/summary.md
```

All files are checksum‑tracked (`data/manifest.json`) to satisfy Constitution Principle III.
