# Data Model: llmXive Follow-up: Physics-Teacher Distillation

## Overview
The project manipulates three primary data entities:

1. **PhysicsTrajectory** – deterministic state‑vector sequence produced by Box2D.  
2. **VideoSequence** – rendered 16‑frame MP4 aligned with a PhysicsTrajectory.  
3. **EvaluationResults** – per‑sequence metrics and aggregated statistical outputs.

All entities are versioned, checksummed, and validated against the contracts below. The **VideoSequence** schema is defined in `contracts/video_sequence.schema.yaml` and is enforced during data generation (see T1.2).

## Schemas

### contracts/physics_trajectory.schema.yaml
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "PhysicsTrajectory"
description: "Deterministic state‑vector trajectory for a multi‑frame simulation."
type: object
required:
  - sequence_id
  - seed
  - time_step
  - states
  - checksum
properties:
  sequence_id:
    type: string
    description: "Unique identifier, e.g., 'traj_000123'."
  seed:
    type: integer
    description: "Random seed used to initialise the Box2D world."
  time_step:
    type: number
    description: "Fixed integration time‑step (seconds)."
  states:
    type: array
    description: "List of multiple state dictionaries."
    items:
      type: object
      required: [frame_index, positions, velocities]
      properties:
        frame_index:
          type: integer
        positions:
          type: array
          items:
            type: number
        velocities:
          type: array
          items:
            type: number
  checksum:
    type: string
    description: "SHA256 checksum of the `.npz` file storing the trajectory."
```

### contracts/evaluation_results.schema.yaml
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "EvaluationResults"
description: "Aggregated per‑sequence metrics and statistical summaries."
type: object
required:
  - sequence_id
  - model_type
  - ssim
  - psnr
  - lpips
  - fid
properties:
  sequence_id:
    type: string
    description: "ID linking to the original VideoSequence."
  model_type:
    type: string
    enum:
      - "physics_teacher"
      - "neural_teacher"
    description: "Which model generated the prediction."
  ssim:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Structural Similarity Index (higher is better)."
  psnr:
    type: number
    minimum: 0.0
    description: "Peak Signal‑to‑Noise Ratio in dB."
  lpips:
    type: number
    minimum: 0.0
    description: "Learned Perceptual Image Patch Similarity (lower is better)."
  fid:
    type: number
    minimum: 0.0
    description: "Fréchet Inception Distance between generated set and baseline."
  additional_info:
    type: object
    description: "Optional free‑form fields (e.g., friction coefficient for ablation)."
    additionalProperties: true
```

### contracts/video_sequence.schema.yaml
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "VideoSequence"
description: "Rendered 16‑frame MP4 video paired with a PhysicsTrajectory."
type: object
required:
  - sequence_id
  - video_path
  - trajectory_checksum
  - frame_rate
properties:
  sequence_id:
    type: string
    description: "Unique identifier matching the associated PhysicsTrajectory."
  video_path:
    type: string
    description: "Relative path to the `.mp4` file stored under `data/physics/...`."
  trajectory_checksum:
    type: string
    description: "SHA256 checksum of the linked `.npz` trajectory file."
  frame_rate:
    type: number
    description: "Frames per second; fixed to a consistent frame rate for all sequences."
```

## Data Flow Diagram (textual)

```
Box2D metadata (verified) → generate.py → PhysicsTrajectory (.npz) + VideoSequence (.mp4)
Training loader (student) reads both → student_diffusion.py → student checkpoint
Baseline loader reads Causal Forcing++ → neural_teacher.py → baseline checkpoint
Control baseline loader reads physics data → neural_teacher.py → control checkpoint
Evaluation/metrics.py consumes videos + trajectories → per‑sequence EvaluationResults
Statistical analysis aggregates EvaluationResults → JSON/CSV reports
```

All intermediate files are stored under `data/` (raw) or `outputs/` (derived) and referenced by checksum in the manifest.

---


