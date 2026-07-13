# Data Model: llmXive follow-up: extending "PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents "

## 1. Overview

This document defines the data structures used in the experiment, including the raw dataset schema, the derived failure signature index (based on synthetic injection), and the execution logs. All data is stored in `data/` and processed by `code/`.

## 2. Raw Dataset Schema

**Source**: PlanBench (Parquet)
**File**: `data/raw/planbench_train.parquet`

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | String | Unique identifier for the task. |
| `goal` | String | The natural language goal of the task. |
| `tool_definitions` | JSON | Schema of available tools (name, description, parameters). |
| `ground_truth_success` | Boolean | `True` if the task was successfully completed in the ground truth. |
| `ground_truth_trace` | List[JSON] | The sequence of tool calls and outcomes in the ground truth. |
| `metadata` | JSON | Additional task metadata (e.g., domain, complexity). |

## 3. Derived Data Structures

### 3.1. Synthetic Injection Log
**File**: `data/derived/injection_log.json`
**Purpose**: Records which tasks were selected for synthetic failure injection and what patterns were injected.

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | String | Task identifier. |
| `injected_pattern` | String | The error pattern injected (e.g., "Error: None"). |
| `original_status` | Boolean | The original `ground_truth_success` (should be `True`). |

### 3.2. Failure Signature Index
**File**: `data/derived/failure_signatures.json`
**Purpose**: Static mapping of tool IDs to *injected* failure patterns and recovery strategies.

```json
{
  "tool_id_1": {
    "name": "tool_name",
    "failure_signatures": [
      "Error: None",
      "Result: []"
    ],
    "recovery_strategy": "retry_with_backoff"
  },
  "tool_id_2": {
    "name": "another_tool",
    "failure_signatures": [
      "Timeout",
      "Invalid Input"
    ],
    "recovery_strategy": "fallback_to_alternative"
  }
}
```

### 3.3. Execution Log (Baseline)
**File**: `data/logs/baseline_execution_log.json`
**Purpose**: Record of the baseline agent's execution.

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | String | Task identifier. |
| `agent_type` | String | "baseline". |
| `steps` | List[JSON] | Sequence of actions (tool call, output, reasoning). |
| `final_status` | String | "success" or "failure". |
| `ground_truth_match` | Boolean | `True` if `final_status` matches `ground_truth_success` (original). |

### 3.4. Execution Log (Augmented)
**File**: `data/logs/augmented_execution_log.json`
**Purpose**: Record of the augmented agent's execution.

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | String | Task identifier. |
| `agent_type` | String | "augmented". |
| `steps` | List[JSON] | Sequence of actions, including signature checks. |
| `signature_matches` | List[JSON] | Records of detected failure signatures. |
| `recovery_actions` | List[JSON] | Actions taken upon signature match. |
| `final_status` | String | "success" or "failure". |
| `ground_truth_match` | Boolean | `True` if `final_status` matches `ground_truth_success` (original). |

## 4. Data Flow

1. **Download**: `data/raw/planbench_train.parquet` is downloaded from the verified URL.
2. **Injection**: `code/dataset/injector.py` selects a subset of tasks and injects error patterns, generating `data/derived/injection_log.json`.
3. **Indexing**: `code/dataset/indexer.py` constructs `data/derived/failure_signatures.json` from the injection logic.
4. **Execution**:
   - `code/agents/baseline.py` runs on the injected subset, producing `data/logs/baseline_execution_log.json`.
   - `code/agents/augmented.py` runs on the same subset, producing `data/logs/augmented_execution_log.json`.
5. **Analysis**: `code/analysis/stats.py` reads the logs to compute success rates and statistical significance (z-test).

## 5. Data Hygiene & Versioning

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/`.
- **Immutability**: Raw data is never modified. Derived files (injection log, index) are overwritten only if the source or logic changes.
- **PII**: No personally identifiable information is present in the PlanBench dataset.
