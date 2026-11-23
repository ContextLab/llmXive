# Data Model: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

## 1. Overview

This document defines the data structures used in the `Symbolic-Guava` pipeline. All data is stored in JSON/JSONL format for interoperability and versioning. Raw data is preserved in `data/raw/`; derived data in `data/processed/`.

## 2. Entity Definitions

### 2.1 SymbolicObservation
Represents the state of the environment at a single timestep, derived from a raw image frame.
- **Source**: `code/data/transform_symbolic.py` (FR-001)
- **Format**: JSON object.

### 2.2 Trajectory
A sequence of `SymbolicObservation` and `Action` pairs.
- **Source**: `data/processed/symbolic_guava/` (FR-002)
- **Format**: JSONL (one trajectory per line).

### 2.3 TaskOutcome
Record of a single evaluation run.
- **Source**: `code/models/inference.py` (FR-004)
- **Format**: JSON.

### 2.4 PerceptionLog
Detailed log of perception module performance.
- **Source**: `code/utils/logger.py` (FR-007)
- **Format**: JSONL.

## 3. Schema Definitions

### SymbolicObservation
```yaml
type: object
properties:
  frame_id:
    type: integer
    description: "Unique identifier for the frame within the trajectory."
  timestamp:
    type: string
    format: date-time
    description: "Timestamp of the frame capture."
  detected_objects:
    type: array
    items:
      type: object
      properties:
        class_label:
          type: string
          description: "Class name (e.g., 'red_block', 'blue_drawer')."
        bounding_box_2d:
          type: array
          items:
            type: number
          minItems: 4
          maxItems: 4
          description: "Format: [x_min, y_min, x_max, y_max]."
        centroid:
          type: array
          items:
            type: number
          minItems: 2
          maxItems: 2
          description: "Format: [center_x, center_y]."
        color_histogram:
          type: array
          items:
            type: integer
          description: "Binned color histogram (e.g., 64 bins)."
      required:
        - class_label
        - bounding_box_2d
        - centroid
        - color_histogram
  scene_empty:
    type: boolean
    description: "True if no manipulable objects detected."
  perception_latency_ms:
    type: number
    description: "Time taken to process this frame in milliseconds."
  object_missing_if_visible:
    type: boolean
    description: "True if object is present in ground truth but missed by perception."
required:
  - frame_id
  - timestamp
  - detected_objects
  - scene_empty
  - perception_latency_ms
  - object_missing_if_visible
```

### Trajectory
```yaml
type: object
properties:
  trajectory_id:
    type: string
    description: "Unique identifier for the trajectory."
  source:
    type: string
    description: "Source dataset (e.g., 'guava_original')."
  steps:
    type: array
    items:
      type: object
      properties:
        observation:
          $ref: "#/properties/steps/items/properties/observation"
        action:
          type: string
          description: "Action abstraction (e.g., 'GRAB_OBJECT')."
        reward:
          type: number
          description: "Reward signal (if available)."
      required:
        - observation
        - action
  metadata:
    type: object
    properties:
      duration_seconds:
        type: number
      total_steps:
        type: integer
required:
  - trajectory_id
  - source
  - steps
```

### TaskOutcome
```yaml
type: object
properties:
  task_id:
    type: string
    description: "Unique identifier for the task."
  success:
    type: boolean
    description: "True if the task was completed successfully."
  steps_taken:
    type: integer
    description: "Number of steps taken to complete the task."
  failure_category:
    type: string
    enum:
      - geometric
      - semantic
      - perception
      - latency
      - timeout
      - null
    description: "Category of failure if success is false."
  execution_time:
    type: number
    description: "Total time taken to execute the task."
  perception_failures:
    type: integer
    description: "Count of perception failures during the task."
required:
  - task_id
  - success
  - steps_taken
  - failure_category
  - execution_time
```

### PerceptionLog
```yaml
type: object
properties:
  timestamp:
    type: string
    format: date-time
  frame_id:
    type: integer
  detected_objects:
    type: array
    items:
      type: object
      properties:
        class_label:
          type: string
        confidence:
          type: number
          format: float
  ground_truth_objects:
    type: array
    items:
      type: object
      properties:
        class_label:
          type: string
  object_missing_if_visible:
    type: boolean
  latency_ms:
    type: number
required:
  - timestamp
  - frame_id
  - detected_objects
  - ground_truth_objects
  - object_missing_if_visible
  - latency_ms
```