# Data Model: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Overview

This document defines the data structures, schemas, and file formats used in the project. All data is stored in `data/` with strict checksumming and versioning.

## Directory Structure

```text
data/
├── raw/
│   ├── gfm_weights.pt          # Frozen GFM encoder/decoder weights
│   ├── original_gam_metadata.json # Metadata from original GAM training set (for uniqueness check)
│   └── gam_reference_stats.json   # Mean/Covariance of training latent vectors (Phase 1.4)
├── generated/
│   ├── topology_shift_set/
│   │   ├── topology_000.json   # Topology definition (hinges, links, material params)
│   │   ├── topology_001.json
│   │   └── ...
│   ├── physics_states/
│   │   ├── trial_000_states.jsonl # Simulation states (latent inputs, ground truth actions)
│   │   └── ...
│   └── generation_manifest.json   # Checksums and metadata for generated set
└── results/
    ├── trial_log.csv            # Primary results: trial_id, method, success, latency, timeout
    ├── stats_report.json        # Statistical test results (p-values, CIs, effect sizes)
    ├── gradient_flow_log.json   # Numerical gradient verification logs (Phase 2.5)
    ├── failure_report.json      # Logs of infeasible/timeout failures
    └── pilot_latency_report.json # Pilot study results (Phase 0.2)
```

## Key Entities & Schemas

### 1. Topology Definition (`data/generated/topology_shift_set/topology_XXX.json`)

Defines a unique kinematic chain or deformable material.

```yaml
# contracts/topology_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  topology_id:
    type: string
    pattern: "^topology_[0-9]{3}$"
  type:
    type: string
    enum: ["kinematic_chain", "deformable_rope", "deformable_cloth"]
  parameters:
    type: object
    properties:
      link_count:
        type: integer
        minimum: 2
      hinge_count:
        type: integer
        minimum: 1
      material_properties:
        type: object
        properties:
          stiffness:
            type: number
            minimum: 0
          damping:
            type: number
            minimum: 0
    required: ["stiffness", "damping"]
  checksum:
    type: string
    description: "SHA256 hash of the topology definition for uniqueness check"
required: ["topology_id", "type", "parameters", "checksum"]
```

### 2. Trial Log (`data/results/trial_log.csv`)

Primary results file. One row per trial step or trial summary.

```yaml
# contracts/trial_log_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  trial_id:
    type: string
  method:
    type: string
    enum: ["symbolic", "baseline_gam"]
  topology_id:
    type: string
  step:
    type: integer
    minimum: 0
  success:
    type: boolean
    description: "True if manipulation completed successfully"
  latency_ms:
    type: number
    description: "Inference time in milliseconds"
  timeout:
    type: boolean
    description: "True if the step exceeded the time limit"
  error_reason:
    type: string
    nullable: true
    description: "Reason for failure (e.g., 'infeasible', 'collision', 'timeout')"
required: ["trial_id", "method", "topology_id", "step", "success", "latency_ms", "timeout"]
```

### 3. Statistical Report (`data/results/stats_report.json`)

```yaml
# contracts/stats_report_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  success_rate_comparison:
    type: object
    properties:
      test:
        type: string
        const: "Fisher_Exact_Test"
      p_value:
        type: number
      confidence_interval:
        type: array
        items:
          type: number
      effect_size:
        type: number
        description: "Odds Ratio"
  latency_comparison:
    type: object
    properties:
      test:
        type: string
        enum: ["Paired_T_Test", "Wilcoxon_Signed_Rank", "Log_Rank_Test"]
        description: "Selected test based on data distribution (censored vs uncensored)"
      p_value:
        type: number
      confidence_interval:
        type: array
        items:
          type: number
      effect_size:
        type: number
        description: "Cohen's d or Hazard Ratio"
  null_hypothesis_rejected:
    type: boolean
    description: "True if p < 0.05"
required: ["success_rate_comparison", "latency_comparison", "null_hypothesis_rejected"]
```

### 4. Reference Stats (`data/raw/gam_reference_stats.json`)

```yaml
# contracts/reference_stats.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  mean:
    type: array
    items:
      type: number
    description: "Mean of latent vectors from training set (or prior)"
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
  topology_list:
    type: array
    items:
      type: object
      properties:
        id:
          type: string
        parameters:
          type: object
      required: ["id", "parameters"]
    description: "Discrete list of training topologies for overlap check."
required: ["mean", "covariance", "sample_size", "topology_list"]
```

### 5. Gradient Flow Log (`data/results/gradient_flow_log.json`)

```yaml
# contracts/gradient_flow_log.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: "object"
properties:
  verification_run_id:
    type: "string"
  timestamp:
    type: "string"
    format: "date-time"
  method:
    type: "string"
    const: "numerical_finite_difference"
    description: "The method used for verification."
  results:
    type: "array"
    items:
      type: "object"
      properties:
        topology_id:
          type: "string"
        solver_param_perturbation:
          type: "number"
          description: "The epsilon value used for perturbation."
        gradient_norm:
          type: "number"
          description: "Norm of the gradient from constraint loss to solver params."
        is_differentiable:
          type: "boolean"
          description: "True if gradient norm > 0 and finite."
        decoder_frozen:
          type: "boolean"
          const: true
          description: "Confirms decoder was frozen during check."
        error_message:
          type: "string"
          nullable: true
      required:
        - topology_id
        - solver_param_perturbation
        - gradient_norm
        - is_differentiable
        - decoder_frozen
required:
  - verification_run_id
  - method
  - results
additionalProperties: false
```

## Data Flow

1.  **Generation**: `code/data/generator.py` -> `data/generated/topology_shift_set/` (JSON) + `data/generated/physics_states/` (JSONL).
2.  **Reference Stats**: `code/data/generator.py` (Phase 1.4) -> `data/raw/gam_reference_stats.json`.
3.  **Execution**: `code/eval/runner.py` reads `topology_shift_set`, runs `symbolic` and `baseline_gam`, writes to `data/results/trial_log.csv`.
4.  **Gradient Check**: `code/models/symbolic_solver.py` (Phase 2.5) -> `data/results/gradient_flow_log.json`.
5.  **Analysis**: `code/eval/stats.py` reads `trial_log.csv`, computes stats, writes to `data/results/stats_report.json`.

## Data Hygiene Rules

-   **Checksums**: Every generated file in `data/generated/` is checksummed (SHA256) and recorded in `generation_manifest.json`.
-   **Immutability**: Files in `data/raw` and `data/generated` are never modified in place. New versions get new filenames.
-   **No PII**: No personal data is involved; all data is synthetic or public.
