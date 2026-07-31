# Data Model: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Overview

This document defines the data structures, schemas, and storage formats for the project. All data is stored in `projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/data/`.

## Directory Structure

```text
data/
├── raw/
│   ├── .gitkeep
│   ├── gam_reference_stats.json      # Mean/covariance of original GAM training data
│   ├── novel_topology_set.json       # Generated test set (multiple topologies)
│   └── gfm_weights.pth               # Frozen GFM encoder/decoder weights
├── generated/
│   ├── .gitkeep
│   └── latent_trajectories.h5        # Intermediate latent vectors for all trials
└── results/
    ├── .gitkeep
    ├── trial_log.csv                 # Primary results (success, latency, flags)
    └── gradient_flow_log.json        # Solver gradient verification logs
```

## Data Schemas

### 1. Novel Topology Set (`data/raw/novel_topology_set.json`)

Contains the definitions of numerous unique kinematic chains and deformable materials.

```yaml
# contracts/topology_set.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Novel Topology Set"
type: "object"
properties:
  metadata:
    type: "object"
    properties:
      generated_at:
        type: "string"
        format: "date-time"
      seed:
        type: "integer"
      total_count:
        type: "integer"
        minimum: a sufficient threshold to ensure statistical power
      checksum:
        type: "string"
        description: "SHA-256 hash of the topology definitions to verify uniqueness"
  topologies:
    type: "array"
    items:
      type: "object"
      properties:
        topology_id:
          type: "string"
          description: "Unique identifier for this topology"
        type:
          type: "string"
          enum: ["kinematic_chain", "deformable_rope", "deformable_cloth"]
        parameters:
          type: "object"
          description: "Physical parameters (link counts, hinge angles, mesh density)"
        initial_state:
          type: "object"
          description: "Initial positions and velocities for simulation"
        hash:
          type: "string"
          description: "Hash of parameters to verify non-overlap with training set"
      required:
        - topology_id
        - type
        - parameters
        - hash
required:
  - metadata
  - topologies
```

### 2. Trial Log (`data/results/trial_log.csv`)

The primary results file. Each row represents a single trial execution.

```yaml
# contracts/trial_log.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Trial Log"
type: "object"
properties:
  trial_id:
    type: "string"
    description: "Unique identifier for the trial"
  topology_id:
    type: "string"
    description: "Reference to the topology used"
  method:
    type: "string"
    enum: ["symbolic", "baseline"]
    description: "The approach used (Symbolic Solver or Baseline GAM)"
  success:
    type: "integer"
    enum: [0, 1]
    description: "1 if task completed successfully, 0 otherwise"
  latency_ms:
    type: "number"
    description: "Inference latency in milliseconds"
  timeout:
    type: "boolean"
    description: "True if the solver exceeded the time limit"
  timeout_reason:
    type: "string"
    enum: ["step_limit", "infeasible", "collision", "none"]
    description: "Reason for timeout or failure (distinguishes computational vs physical failure)"
  ood_flag:
    type: "boolean"
    description: "True if latent drift exceeded threshold"
  seed:
    type: "integer"
    description: "Random seed used for this trial"
required:
  - trial_id
  - topology_id
  - method
  - success
  - latency_ms
  - timeout
  - timeout_reason
  - seed
```

### 3. Gradient Flow Log (`data/results/gradient_flow_log.json`)

Records the verification of gradient flow through the symbolic solver.

```yaml
# contracts/gradient_flow_log.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Gradient Flow Log"
type: "object"
properties:
  verification_run_id:
    type: "string"
  timestamp:
    type: "string"
    format: "date-time"
  results:
    type: "array"
    items:
      type: "object"
      properties:
        topology_id:
          type: "string"
        gradient_norm:
          type: "number"
          description: "Norm of the gradient from constraint loss to solver params"
        is_differentiable:
          type: "boolean"
          description: "True if gradient norm > 0 and finite"
        error_message:
          type: "string"
          nullable: true
      required:
        - topology_id
        - gradient_norm
        - is_differentiable
required:
  - verification_run_id
  - results
```

## Data Hygiene Rules

1. **Checksumming**: Every file in `data/raw` and `data/results` must have a corresponding SHA-256 hash recorded in `state/projects/PROJ-898-llmxive-follow-up-extending-geometric-ac.yaml`.
2. **Immutability**: Files in `data/raw` are read-only. Any transformation writes to `data/generated` or `data/results`.
3. **Validation**: The `test_schema_validation.py` script must validate `trial_log.csv` and `novel_topology_set.json` against their respective schemas before any statistical analysis is run.
4. **State Update**: After generating `novel_topology_set.json` and `trial_log.csv`, the system must update the `state/...yaml` file with the new checksums.