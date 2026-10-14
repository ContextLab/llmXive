# Data Model: Energy Profiling of Quantized LLM Inference

## Overview
The **​** ​ ​ 
​  



The content appears truncated due to an earlier mistake. We need to provide full corrected data-model.md content. Let's reconstruct based on original, with minor updates (maybe note schema change). We'll provide complete file.

Original data-model.md content had sections and schemas. We'll reproduce fully, ensuring correctness.

===BEGIN_ARTIFACT data-model.md===

# Data Model: Energy Profiling of Quantized LLM Inference on Edge CPUs

## Overview
The project manipulates three core entity types—**Configuration**, **InferenceRun**, and **AggregatedMetric**—each defined by a JSON schema stored under `contracts/`. These schemas are used by the testing harness to validate that generated files conform to the expected structure.

## Schemas

### `contracts/config.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: Configuration
type: object
required:
  - model_name
  - model_size_m
  - quantization
  - seed
properties:
  model_name:
    type: string
    description: "Identifier of the base model (e.g., 'gpt-neo-125M')."
  model_size_m:
    type: integer
    description: "Model parameter count in millions (e.g., 125)."
  quantization:
    type: string
    enum: [fp16, int8, 4bit]
    description: "Quantization level applied to the model."
  seed:
    type: integer
    description: "Random seed used for this run (ensures reproducibility)."
  checkpoint_path:
    type: string
    description: "Absolute path to the (quantized) model checkpoint on disk."
  load_success:
    type: boolean
    description: "True if the model loaded without OOM; false otherwise."
```

### `contracts/inference_run.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: InferenceRun
type: object
required:
  - config_id
  - run_index
  - energy_joules
  - latency_ms
  - token_count
  - perplexity
  - measurement_method
properties:
  config_id:
    type: string
    description: "SHA256 hash of the Configuration object."
  run_index:
    type: integer
    description: "0‑based index of the repetition (0‑9)."
  energy_joules:
    type: number
    description: "Net energy consumed by the model (Joules)."
  latency_ms:
    type: number
    description: "Wall‑clock time for the forward pass (milliseconds)."
  token_count:
    type: integer
    description: "Number of tokens processed (fixed at 500)."
  perplexity:
    type: number
    description: "Per‑token perplexity on the prompt."
  measurement_method:
    type: string
    enum: [pyRAPL, powerstat, unavailable]
    description: "Tool that supplied the energy measurement."
  timestamp_iso:
    type: string
    format: date-time
    description: "ISO‑8601 timestamp when the run completed."
```

### `contracts/aggregated.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: AggregatedMetric
type: object
required:
  - config_id
  - mean_energy_per_token
  - std_energy_per_token
  - mean_latency_ms
  - std_latency_ms
  - mean_perplexity
  - std_perplexity
  - dequantization_overhead_flag
  - variance_stability_flag
properties:
  config_id:
    type: string
    description: "Hash of the Configuration object (SHA256)."
  mean_energy_per_token:
    type: number
    description: "Mean energy per token (Joules/token) across repetitions."
  std_energy_per_token:
    type: number
    description: "Standard deviation of energy per token."
  mean_latency_ms:
    type: number
    description: "Mean inference latency (ms)."
  std_latency_ms:
    type: number
    description: "Standard deviation of latency."
  mean_perplexity:
    type: number
    description: "Mean perplexity across runs."
  std_perplexity:
    type: number
    description: "Standard deviation of perplexity."
  dequantization_overhead_flag:
    type: boolean
    description: "True if overhead >10 % relative to FP16 baseline and statistically significant."
  variance_stability_flag:
    type: boolean
    description: "True if std/mean ≤ 0.15 for energy per token."
```

## Data Flow
1. **Configuration** objects are generated once per model‑size/quantization pair (9 total).  
2. **InferenceRun** records are emitted after each of the ten repetitions.  
3. **AggregatedMetric** is computed from the ten `InferenceRun` records per configuration and stored in `data/results/aggregated.csv` (CSV representation of the schema).  

All schemas are version‑controlled; any change triggers a re‑hash of the project state per Constitution Principle V.

---



