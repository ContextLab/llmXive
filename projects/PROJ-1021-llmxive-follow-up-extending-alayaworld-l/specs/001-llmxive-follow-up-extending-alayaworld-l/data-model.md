# Data Model: llmXive follow-up: extending "AlayaWorld"

## Overview

This document defines the data structures used to track the symbolic state, visual state, and the resulting drift metrics. All data is stored in JSON/CSV formats to ensure reproducibility and ease of parsing for the statistical analysis phase. The "Semantic Drift Score" is decomposed into "Intrinsic Drift" (caused by the mock's generative errors) and "Observational Noise" (CV error) to avoid circular validation.

## Entities

### 1. Action Sequence
A discrete list of user inputs driving the simulation.

```yaml
ActionSequence:
  type: object
  properties:
    id:
      type: string
      description: "Unique identifier for the sequence (e.g., 'seed-001-seq-05')"
    seed:
      type: integer
      description: "Random seed used for generation"
    actions:
      type: array
      items:
        type: object
        properties:
          timestamp:
            type: integer
            description: "Frame index of the action"
          action_type:
            type: string
            description: "e.g., 'hit', 'summon', 'die', 'teleport'"
          target_id:
            type: string
            description: "ID of the target object"
```

### 2. Symbolic State Log
The deterministic ground truth trajectory.

```yaml
SymbolicStateLog:
  type: object
  properties:
    sequence_id:
      type: string
    states:
      type: array
      items:
        type: object
        properties:
          frame_index:
            type: integer
          object_id:
            type: string
          hp:
            type: integer
            description: "Current HP (0 = Dead)"
          inventory:
            type: array
            items:
              type: string
          state:
            type: string
            enum: ["Alive", "Dead", "Teleported", "Missing"]
          position:
            type: object
            properties:
              x:
                type: number
              y:
                type: number
```

### 3. Visual State Log
The state extracted from the video via CV.

```yaml
VisualStateLog:
  type: object
  properties:
    sequence_id:
      type: string
    confidence:
      type: number
      description: "Average confidence of CV detections (0.0 - 1.0)"
    detections:
      type: array
      items:
        type: object
        properties:
          frame_index:
            type: integer
          object_id:
            type: string
          detected_state:
            type: string
            enum: ["Alive", "Dead", "Missing", "Phantom"]
          position:
            type: object
            properties:
              x:
                type: number
              y:
                type: number
          is_low_confidence:
            type: boolean
            description: "True if occlusion or low match score"
```

### 4. Drift Metric
The final calculated score for a sequence.

```yaml
DriftMetric:
  type: object
  properties:
    sequence_id:
      type: string
    mode:
      type: string
      enum: ["baseline", "hybrid"]
    semantic_drift_score:
      type: number
      description: "0.0 to 1.0, lower is better"
    intrinsic_drift:
      type: number
      description: "Drift caused by the mock's injected generative errors (the target of correction)"
    observational_noise:
      type: number
      description: "Drift caused by CV measurement error"
    permanence_violations:
      type: integer
      description: "Count of 'Alive in Video' when 'Dead in Logic'"
    phantom_objects:
      type: integer
      description: "Count of 'Alive in Video' when 'Missing in Logic'"
    render_failures:
      type: integer
      description: "Count of 'Teleport' mismatches"
    cv_accuracy:
      type: number
      description: "Validation accuracy on the 50-frame subset (expected to be < 85% due to injected errors)"
    is_valid:
      type: boolean
      description: "True if CV accuracy >= 85% (for validation purposes only)"
    resource_usage:
      type: object
      properties:
        peak_ram_mb:
          type: number
        wall_clock_seconds:
          type: number
```

## File Layout

-   `data/raw/`: Mock video files (if generated) or raw logs.
-   `data/processed/symbolic_logs/`: JSON files per sequence.
-   `data/processed/visual_logs/`: JSON files per sequence.
-   `data/processed/metrics/`: CSV file containing all `DriftMetric` records.
-   `data/annotations/gt_subset.json`: The 50-frame ground truth for CV validation.
