# Data Model: Reproduce & Validate OpenComputer

## Overview

This document defines the data structures used for task execution, verification, and reporting. All data is serialized as JSON for compatibility with the OpenComputer ecosystem and the CI pipeline. The schema has been updated to support the **Blinded Manual Inspection** and **Qualitative Case Study** methodology.

## Core Entities

### 1. Task Definition
Represents a single unit of work to be executed.

```yaml
# contracts/task.schema.yaml
$schema: http://json-schema.org/draft-07/schema#
title: OpenComputer Task
type: object
properties:
  task_id:
    type: string
    description: "Unique identifier for the task (e.g., 'audacity_export_wav_440')"
  env_manifest:
    type: object
    description: "Docker image and environment requirements"
    properties:
      image_name:
        type: string
        description: "Docker image to use (e.g., 'opencomputer:audacity')"
      apps:
        type: array
        items:
          type: string
        description: "List of applications required (e.g., ['audacity'])"
  task_spec:
    type: object
    description: "Human-readable or structured instructions for the agent"
    properties:
      prompt:
        type: string
        description: "The instruction given to the agent"
      expected_artifact:
        type: string
        description: "Path or pattern for the expected output file"
      verification_logic:
        type: string
        description: "Description of how the verifier checks success"
required:
  - task_id
  - env_manifest
  - task_spec
```

### 2. Verification Report
The output of the `run_eval.py` script for a batch of tasks. Updated to include manual ground truth fields.

```yaml
# contracts/verification_report.schema.yaml
$schema: http://json-schema.org/draft-07/schema#
title: OpenComputer Verification Report
type: object
properties:
  run_id:
    type: string
    description: "Unique identifier for this execution run"
  timestamp:
    type: string
    format: date-time
    description: "ISO 8601 timestamp of the run"
  tasks:
    type: array
    items:
      type: object
      properties:
        task_id:
          type: string
        status:
          type: string
          enum: ["success", "failed", "partial_success", "skipped"]
        verifier_judgment:
          type: boolean
          description: "True if the hardcode verifier passed"
        failure_reason:
          type: string
          nullable: true
          description: "Specific reason for failure (e.g., 'file_not_found')"
        artifact_path:
          type: string
          description: "Path to the generated artifact in the container"
        manual_ground_truth:
          type: boolean
          description: "True if the blinded human adjudicator judged the task as successful (independent of verifier)"
        manual_judgment_notes:
          type: string
          nullable: true
          description: "Qualitative notes from the human adjudicator (e.g., 'Audio plays but has noise', 'File exists but is empty')"
      required:
        - task_id
        - status
        - verifier_judgment
        - manual_ground_truth
  summary:
    type: object
    properties:
      tasks_attempted:
        type: integer
      tasks_passed:
        type: integer
      alignment_observation:
        type: string
        description: "Qualitative summary of alignment (e.g., '4/5 aligned; 1 diverged due to verifier logic flaw')"
required:
  - run_id
  - timestamp
  - tasks
  - summary
```

### 3. Smoke Report
The output of the `smoke_loop.py` script.

```yaml
# contracts/smoke_report.schema.yaml
$schema: http://json-schema.org/draft-07/schema#
title: OpenComputer Smoke Report
type: object
properties:
  status:
    type: string
    enum: ["success", "partial_success", "build_failed", "disk_quota_exceeded"]
  task_id:
    type: string
  error_log:
    type: string
    nullable: true
    description: "Full error output if status is not success"
required:
  - status
  - task_id
```

## Data Flow

1.  **Input**: `task.json` files from `external/OpenComputer/task_generator/`.
2.  **Processing**:
    - `smoke_loop.py` reads a single task, builds the container, runs the task, writes `smoke_report.json`.
    - `run_eval.py` reads 5 tasks, runs them, compares output to `hardcode` verifier, writes `verification_report.json` (including `manual_ground_truth` placeholders).
    - **Manual Step**: A human adjudicator inspects the artifacts and fills in `manual_ground_truth` and `manual_judgment_notes` in the JSON (or a separate JSON file merged later).
3.  **Output**: Reports are consumed by `generate_report.py` to produce `reproduction_report.md` with a qualitative case study narrative.
