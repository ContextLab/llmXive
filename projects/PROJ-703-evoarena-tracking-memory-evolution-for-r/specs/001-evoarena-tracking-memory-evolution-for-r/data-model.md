# Data Model: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

## Overview

This document defines the data structures for the validation pipeline. It covers the input dataset schemas (assumed based on verified sources), the intermediate execution artifacts (JSON logs), and the output metrics.

## Input Data Schemas

### 1. TerminalBench-Evo Chain
*Source*: Verified HuggingFace Parquet files (assumed to be loaded by vendored code).
*Assumption*: The vendored code expects a directory structure containing task definitions and initial states.

```yaml
type: object
properties:
  chain_id:
    type: string
    description: "Unique identifier for the task chain (e.g., 'terminal_001')"
  tasks:
    type: array
    description: "List of subtasks in the chain"
    items:
      type: object
      properties:
        task_id:
          type: string
        instruction:
          type: string
        initial_state:
          type: object
          description: "Initial file system or environment state"
        expected_outcome:
          type: object
          description: "Expected result for validation"
```

### 2. PersonaMem-Evo Chain
*Source*: Verified HuggingFace Parquet files (`benchmark_text_32k.parquet`).
*Assumption*: The vendored code maps these to chat history and persona updates.

```yaml
type: object
properties:
  chain_id:
    type: string
    description: "Unique identifier for the persona chain"
  persona_id:
    type: string
  chat_history:
    type: array
    items:
      type: object
      properties:
        role:
          type: string
          enum: ["user", "assistant"]
        content:
          type: string
  dynamic_updates:
    type: array
    description: "Simulated environment updates (if applicable)"
    items:
      type: object
```

## Execution Artifacts (Output of Vendored Code)

### 1. Execution Log (JSON)
*Source*: Output of `launch_terminus2_*.sh` or `evaluate_persona_chain_acc.py`.
*Schema*: `contracts/execution_log.schema.yaml`

### 2. Memory Patch Store
*Source*: Output of EvoMem agent during execution.
*Schema*: `contracts/memory_patch.schema.yaml`

## Aggregated Metrics (Output of Validation Pipeline)

### 1. Accuracy Summary
*Source*: Aggregated from execution logs.
*Schema*: `contracts/accuracy_summary.schema.yaml`

## Data Flow

1. **Input**: Dataset files (Parquet/CSV) -> **Vendored Loader** -> **Agent Execution**
2. **Process**: Agent generates **Execution Logs** and **Memory Patches**.
3. **Validation**: `validators.py` checks logs against schemas.
4. **Aggregation**: `aggregator.py` computes **Accuracy Summary**.
