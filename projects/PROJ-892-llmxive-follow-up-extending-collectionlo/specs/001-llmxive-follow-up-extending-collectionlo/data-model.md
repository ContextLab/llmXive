# Data Model: Quantization Robustness of Multi-Effect LoRA Adapters

## Overview

Defines the persistent data structures used throughout the pipeline. All files live under `data/` or `state/`. Schemas in `contracts/` enforce validity.

## Entity Definitions

### 1. EffectAdapter
- `effect_id`: string (e.g., `"oil_painting"`).
- `weight_matrix_path`: path to the LoRA weight file (`.safetensors`).
- `subspace_rank`: integer (effective rank from SVD, tolerance = 1e‑5).
- `rank_tolerance`: float (default = 1e‑5).

### 2. ReferenceImage
- `image_path`: path to the generated image.
- `effect_id`: effect identifier (may be `"none"` for LoRA‑free references).
- `prompt`: prompt text.
- `clip_embedding`: list of floats (CLIP image embedding).
- `checksum`: SHA‑256 hash of the image file.

### 3. GenerationResult
- `run_id`: UUID for the generation run.
- `prompt_id`: identifier linking to the prompt in `data/prompts.txt`.
- `quantization_level`: `"FP16"`, `"INT8"`, or `"INT4"`.
- `effect_id`: effect identifier.
- `prompt`: prompt text.
- `image_path`: relative path to the generated image.
- `cosine_similarity`: float (prompt‑text ↔ image CLIP similarity).
- `lpips_distance`: float (pixel‑space distance vs. FP16 baseline).
- `cesr_score`: float (mean similarity to BaselineFP16ReferenceImages of other effects).
- `style_classifier_score`: float (probability that the image matches its intended style, from a lightweight WikiArt classifier).
- `checksum`: SHA‑256 hash of the image file.
- `timestamp`: ISO‑8601 timestamp of generation.

### 4. AnalysisMetric
- `metric_name`: string (e.g., `"bhm_adherence"`).
- `posterior_mean`: float.
- `credible_interval_95`: list `[lower, upper]`.
- `probability_effect`: float (probability that the quantization effect is negative).
- `width`: float (HDI width).
- `status`: `"Valid"` or `"Underpowered"`.

### 5. StateRecord
- `artifact_type`: e.g., `"model"`, `"image"`, `"result"`.
- `path`: relative path.
- `sha256`: hash.
- `updated_at`: ISO‑8601 timestamp.

## File Schemas

### `data/prompts.txt`
Plain text, one line per prompt, formatted as:

```
<effect_id>\t<prompt text>
```

Example:

```
oil_painting	A high‑quality photo of an oil‑painting of a cat wearing a hat.
cyberpunk	A neon‑lit cyberpunk cityscape at night.
...
```

### `data/subspace_ranks.json`
```json
{
  "oil_painting": {"rank": 12, "tolerance": 1e-05},
  "cyberpunk": {"rank": 9, "tolerance": 1e-05},
  "...": {"rank": ..., "tolerance": 1e-05}
}
```

### `data/analysis_results.json`
```json
{
  "bayesian_model": { ... },
  "correlation_analysis": { ... },
  "metadata": {
    "timestamp": "2026-07-14T12:34:56Z",
    "version": "1.0.0"
  }
}
```

### `state/artifact_hashes.yaml`
```yaml
artifacts:
  - path: data/generated_images/fp16/oil_painting.png
    sha256: abc123...
    updated_at: 2026-07-14T10:00:00Z
  - path: data/analysis_results.json
    sha256: def456...
    updated_at: 2026-07-14T12:00:00Z
```

All JSON/YAML files are written atomically and flushed to disk immediately after creation to satisfy FR‑010 and FR‑013.