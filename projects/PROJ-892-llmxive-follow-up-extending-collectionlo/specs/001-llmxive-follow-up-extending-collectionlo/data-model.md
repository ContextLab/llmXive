# Data Model: Quantization Robustness of Multi-Effect LoRA Adapters

## Overview

This document defines the data structures used in the project, including the configuration, generated artifacts, and analysis results. All data is stored in `data/` and `state/` directories.

## Configuration (`config.yaml`)

**Schema**:
```yaml
prompts:
  - "oil painting"
  - "watercolor"
  - "neon"
  - "sketch"
  - "cyberpunk"
  - "impressionism"
  - "pixel art"
  - "charcoal"
  - "3d render"
  - "anime"
seeds:
  - 42
  - 43
  - 44
  - 45
  - 46
model:
  base: "stabilityai/stable-diffusion-1-5"
  adapter: "path/to/collection_lora_adapter.safetensors"
quantization:
  levels: ["fp16", "int8", "int4"]
  backend: "dynamic"
analysis:
  model_type: "bayesian_linear"
  prior_strength: "strong_informative"
  hd_width_threshold: 0.2
```

## Generated Artifacts

### 1. `data/generated/`
- **Files**: `gold_standard_<effect>_<seed>.png`, `reference_<effect>_<seed>.png`, `generated_<effect>_<quant_level>_<seed>.png`, `distractor_<effect>_<seed>.png`
- **Schema**: Standard PNG image.
- **Metadata**: Stored in `state/project.yaml` (hash).

### 2. `data/models/`
- **Files**: `adapter_fp16.safetensors`, `adapter_int8.safetensors`, `adapter_int4.safetensors`
- **Schema**: `safetensors` format.
- **Note**: Quantized adapters may be stored as `safetensors` if `torch.ao` supports serialization, or as a custom binary format if not.

### 3. `data/results.csv` (SINGLE SOURCE OF TRUTH)
**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| effect_id | str | Effect name (e.g., "oil painting") |
| quantization_level | str | "fp16", "int8", "int4" |
| seed | int | Random seed used |
| similarity_score | float | Cosine similarity (CLIP) |
| lpips_distance | float | LPIPS distance to Gold Standard (measures consistency relative to baseline) |
| cesr_score | float | Cross-Effect Similarity Ratio (Normalized: Quantized / FP16) |
| distractor_similarity | float | Cosine similarity to Distractor Reference (Negative Control) |
| subspace_rank | int | Effective rank of the effect's LoRA matrix |

### 4. `data/subspace_ranks.json`
**Schema**:
```json
{
  "oil painting": 16,
  "watercolor": 8,
  ...
}
```

### 5. `data/analysis_results.json` (Intermediate Only)
**Schema**:
```json
{
  "quantization_effect": {
    "int8": {
      "posterior_mean": -0.05,
      "hdi_95": [-0.10, 0.00],
      "width": 0.10
    },
    "int4": {
      "posterior_mean": -0.25,
      "hdi_95": [-0.35, -0.15],
      "width": 0.20
    }
  },
  "rank_correlation": {
    "posterior_mean": -0.8,
    "hdi_95": [-0.95, -0.65],
    "status": "Underpowered" | "Valid" | "Not Testable"
  },
  "power_flag": "Underpowered" | "Sufficient" | "Inconclusive"
}
```
**Note**: This file is for debugging and storage only. All final statistics in the paper MUST be derived from `data/results.csv`.

## State Tracking (`state/project.yaml`)

**Schema**:
```yaml
version: "1.0.0"
updated_at: "2026-07-13T12:00:00Z"
artifact_hashes:
  adapter_fp16: "sha256:..."
  results_csv: "sha256:..."
  analysis_json: "sha256:..."
  config_yaml: "sha256:..."
```
