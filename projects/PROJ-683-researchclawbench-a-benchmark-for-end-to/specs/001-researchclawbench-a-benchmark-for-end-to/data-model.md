# Data Model: Reproduce & Validate ResearchClawBench

## Overview

This document defines the data structures used in the ResearchClawBench reproduction pipeline. The model focuses on the **Input** (Task Definition, Rubric), **Process** (Execution Log, Synthetic Artifacts), and **Output** (Score, Aggregation).

## Entity Definitions

### 1. Task Definition
Represents a specific scientific challenge to be evaluated.
- **Source**: `tasks/<task_id>/task_info.json`
- **Purpose**: Defines the task metadata, data paths, and required artifacts.

### 2. Rubric (Checklist)
Defines the weighted criteria for scoring a specific task.
- **Source**: `tasks/<task_id>/target_study/checklist.json`
- **Purpose**: Provides the scoring logic and weights.

### 3. Score Artifact
The result of applying the Rubric to an Agent's output.
- **Target**: `results/<task_id>_score.json`
- **Purpose**: Stores the final score, breakdown, and execution metadata.

### 4. Aggregation Summary
The statistical summary of multiple agent runs.
- **Target**: `results/summary.json`
- **Purpose**: Stores mean, std dev, and individual scores for comparison.

### 5. Synthetic Test Artifact
Programmatically generated output used for validation (Golden/Negative cases).
- **Source**: `src/validation/synthetic_generator.py`
- **Purpose**: Provides known-pass and known-fail inputs to verify the scoring engine's content inspection logic.

## Data Flow

1.  **Load**: `task_info.json` and `checklist.json` are read from `tasks/<ID>/`.
2.  **Validate**: `rubric_checker.py` validates `checklist.json` weights.
3.  **Generate**: `synthetic_generator.py` creates Golden and Negative test artifacts.
4.  **Execute**: `rcb-eval` (with `mock` agent) generates output artifacts (or uses synthetic ones).
5.  **Score**: `scorer.py` applies weights to artifacts to generate `score.json`.
6.  **Aggregate**: `aggregator.py` combines multiple `score.json` files into `summary.json`.

## Schema Specifications

### Task Info Schema
```yaml
type: object
properties:
  task_id:
    type: string
    description: Unique identifier for the task (e.g., "Astronomy_000")
  description:
    type: string
    description: Human-readable description of the scientific challenge
  data_files:
    type: array
    items:
      type: string
    description: List of relative paths to required data files (CSV, PDF, etc.)
  target_study_path:
    type: string
    description: Path to the target study directory containing the rubric
```

### Rubric (Checklist) Schema
```yaml
type: object
properties:
  task_id:
    type: string
    description: Must match the task_id in task_info.json
  criteria:
    type: array
    description: List of scoring criteria
    items:
      type: object
      properties:
        id:
          type: string
          description: Unique ID for the criterion
        description:
          type: string
          description: Description of what is being scored
        weight:
          type: number
          description: Weight of this criterion (0-100)
      required:
        - id
        - description
        - weight
  total_weight:
    type: number
    description: Expected sum of all weights (100.0)
```

### Score Artifact Schema
```yaml
type: object
properties:
  task_id:
    type: string
  agent_id:
    type: string
    description: Identifier of the agent used (e.g., "mock")
  score:
    type: number
    description: Final calculated score (0-100)
  breakdown:
    type: array
    description: Score per criterion
    items:
      type: object
      properties:
        criterion_id:
          type: string
        weight:
          type: number
        achieved:
          type: number
        status:
          type: string
          enum: ["passed", "failed", "partial"]
  execution_time:
    type: number
    description: Wall-clock time in seconds
  status:
    type: string
    enum: ["success", "failed"]
  error_message:
    type: string
    description: Present only if status is "failed"
```

### Aggregation Summary Schema
```yaml
type: object
properties:
  task_id:
    type: string
  agents:
    type: array
    description: List of agent results
    items:
      type: object
      properties:
        agent_id:
          type: string
        score:
          type: number
        status:
          type: string
  statistics:
    type: object
    properties:
      mean_score:
        type: number
      std_dev:
        type: number
      total_runs:
        type: integer
      failed_runs:
        type: integer
```

### Synthetic Test Artifact (Internal)
```yaml
type: object
properties:
  test_type:
    type: string
    enum: ["golden", "negative"]
  target_criterion_id:
    type: string
    description: The criterion this test case targets
  expected_score:
    type: number
    description: The expected score for this test case
  artifacts:
    type: object
    description: Map of file paths to content (for mock output)
```

## Constraints & Validation Rules

1.  **Rubric Weight Sum**: The sum of `criteria[].weight` MUST equal `100.0` (or `1.0` if normalized) within a tolerance of `0.01`. If not, the system MUST raise a `ValueError`.
2.  **Data File Existence**: All paths in `task_info.json.data_files` MUST exist. If any are missing, the system MUST raise a `FileNotFoundError` before execution.
3.  **Score Range**: The final `score` MUST be between `0.0` and `100.0`.
4.  **Execution Time**: The `execution_time` MUST be recorded for performance monitoring (SC-005).
5.  **Synthetic Ground Truth**: For "Negative" test cases, the `expected_score` MUST be `100.0 - weight_of_target_criterion`.