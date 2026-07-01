# Data Model: Reproduce & Validate iLLaDA

## Overview
This document defines the data structures for the iLLaDA reproduction pipeline, focusing on the input dataset subsets, the evaluation results, and the visualization artifacts.

## Input Data Model

### Dataset Subset
The input is a subset of a standard benchmark dataset.

```yaml
type: object
properties:
  dataset_name:
    type: string
    description: "Name of the benchmark (e.g., 'gsm8k', 'bbh')"
  subset_id:
    type: string
    description: "Identifier for the specific subset (e.g., 'N=5_S=42_F=None')"
  samples:
    type: array
    description: "List of sample objects"
    items:
      type: object
      properties:
        id:
          type: string
          description: "Unique sample identifier"
        question:
          type: string
          description: "The input prompt/question"
        answer:
          type: string
          description: "The ground truth answer (if available)"
        choices:
          type: array
          items:
            type: string
          description: "Multiple choice options (for ARC/BBH)"
          nullable: true
```

## Output Data Model

### Evaluation Result
The primary output of `eval_llada.py`.

```yaml
type: object
properties:
  benchmark_name:
    type: string
    description: "Name of the benchmark run"
  model_id:
    type: string
    description: "Identifier of the iLLaDA model used"
  subset_size:
    type: integer
    description: "Number of samples evaluated"
  metrics:
    type: object
    description: "Key metrics (accuracy, exact_match, etc.)"
    additionalProperties:
      type: number
  metadata:
    type: object
    properties:
      hardware:
        type: string
        description: "Hardware config (e.g., 'CPU: 2 cores, 7GB RAM')"
      seed:
        type: integer
        description: "Random seed used for reproducibility"
      execution_time_seconds:
        type: number
        description: "Total runtime in seconds"
      status:
        type: string
        enum: [success, partial_success, memory_fallback]
        description: "Execution status"
      subset_id:
        type: string
        description: "Traceable ID: 'N={size}_S={seed}_F={fallback_flag}'"
```

### Visualization Artifact
Metadata for generated images.

```yaml
type: object
properties:
  artifact_type:
    type: string
    enum: [svg, png, gif]
    description: "File format"
  filename:
    type: string
    description: "Relative path to the file"
  description:
    type: string
    description: "Description of the visualization (e.g., 'Diffusion steps for sample X')"
```

## Data Flow

1. **Ingestion**: `opencompass` loaders fetch data from verified HuggingFace sources.
2. **Filtering**: Data is sliced to `N` samples (configurable via `--subset-size`).
3. **Traceability**: `subset_id` is generated as `N={size}_S={seed}_F={fallback_flag}`.
4. **Processing**: `eval_llada.py` iterates through samples, generating tokens.
5. **Aggregation**: Metrics are computed and aggregated into `results.json`.
6. **Validation**: `results.json` is validated against `contracts/evaluation_result.schema.yaml`.
7. **Visualization**: Diffusion steps for a representative sample are rendered to SVG.