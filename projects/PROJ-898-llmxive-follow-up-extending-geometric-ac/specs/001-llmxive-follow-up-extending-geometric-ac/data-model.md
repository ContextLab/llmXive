# Data Model: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Overview

This document defines the data structures, schemas, and flows for the project. All data is stored in `data/` with checksums tracked in `state/`.

## Directory Structure

```text
data/
├── raw/
│   ├── gfm_weights.pt          # Frozen GFM encoder/decoder weights
│   ├── baseline_gam.pt         # Baseline GAM weights
│   └── gam_reference_stats.json # Mean/covariance for drift detection (T010b)
├── generated/
│   ├── topology_set_v1/
│   │   ├── metadata.json       # Topology definitions, seeds
│   │   ├── states_001.npy      # Simulation states for task 1
│   │   └── ...
│   └── topology_set_v2/        # New versions if regeneration needed
└── results/
    ├── trial_log.csv           # Primary results: success, latency, topology_id
    ├── gradient_flow_log.json  # Verification of differentiability (T014a)
    ├── drift_detection_log.json # Mahalanobis distance logs
    └── statistical_report.json # Final analysis results
```

## Schema Definitions

### 1. Topology Metadata (`data/generated/*/metadata.json`)

```yaml
# contracts/topology_metadata.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  version:
    type: string
    description: "Version of the topology generation script"
  seed:
    type: integer
    description: "Random seed used for generation"
  topologies:
    type: array
    items:
      type: object
      properties:
        id:
          type: string
          description: "Unique topology identifier"
        type:
          type: string
          enum: ["kinematic_chain", "deformable_rope", "deformable_cloth"]
        parameters:
          type: object
          properties:
            hinge_count:
              type: integer
              description: "Number of hinges for kinematic chains"
            stiffness:
              type: number
              description: "Stiffness coefficient for deformable materials"
            length:
              type: number
              description: "Length of the object"
          required: ["hinge_count", "stiffness", "length"]
        hash:
          type: string
          description: "SHA-256 hash of the topology definition"
      required: ["id", "type", "parameters", "hash"]
required: ["version", "seed", "topologies"]
```

### 2. Trial Log (`data/results/trial_log.csv`)

```yaml
# contracts/trial_log.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  type: "object"
  required: ["trial_id", "condition", "topology_id", "success", "latency_ms", "timeout", "drift_flag", "failure_reason"]
  properties:
    trial_id:
      type: string
      description: "Unique trial identifier"
    condition:
      type: string
      enum: ["symbolic", "baseline"]
      description: "Experimental condition"
    topology_id:
      type: string
      description: "Reference to topology in metadata"
    success:
      type: integer
      enum: [0, 1]
      description: "Binary success (1) or failure (0)"
    latency_ms:
      type: number
      description: "Inference latency in milliseconds"
    timeout:
      type: integer
      enum: [0, 1]
      description: "Flag for timeout failure"
    drift_flag:
      type: integer
      enum: [0, 1]
      description: "Flag for latent drift (Mahalanobis distance > threshold)"
    failure_reason:
      type: string
      enum: ["none", "timeout", "infeasible", "collision", "drift"]
      description: "Reason for failure if success is 0"
    error_message:
      type: string
      description: "Optional error message if failed"
```

### 3. Gradient Flow Log (`data/results/gradient_flow_log.json`)

```yaml
# contracts/gradient_flow_log.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  type: "object"
  required: ["solver_params", "decoder_gradients", "constraint_loss", "valid_path"]
  properties:
    solver_params:
      type: array
      items:
        type: number
      description: "Values of solver parameters"
    decoder_gradients:
      type: array
      items:
        type: number
      description: "Gradients flowing through the decoder"
    constraint_loss:
      type: number
      description: "Value of constraint violation loss"
    valid_path:
      type: boolean
      description: "True if gradients successfully flowed through decoder"
```

### 4. Reference Stats (`data/raw/gam_reference_stats.json`)

```yaml
# contracts/reference_stats.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  type: "object"
  required: ["mean", "covariance", "sample_size"]
  properties:
    mean:
      type: array
      items:
        type: number
      description: "Mean of latent vectors from training set"
    covariance:
      type: array
      items:
        type: array
        items:
          type: number
      description: "Covariance matrix of latent vectors"
    sample_size:
      type: integer
      description: "Number of samples used to compute stats"
```

## Data Flow

1. **Generation**: `generate_topology.py` creates `data/generated/topology_set_v1/`.
2. **Stats**: `utils/drift_detector.py` computes `data/raw/gam_reference_stats.json` (once) from standard normal samples.
3. **Execution**: `inference_loop.py` runs trials, writing to `data/results/trial_log.csv` and `gradient_flow_log.json`.
4. **Analysis**: `analysis.py` reads `trial_log.csv`, computes statistics, writes `statistical_report.json`.