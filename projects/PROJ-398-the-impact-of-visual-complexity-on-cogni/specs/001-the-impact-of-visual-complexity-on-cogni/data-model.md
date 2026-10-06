# Data Model: Visual Complexity ↔ Cognitive Load Study

## Overview
The data model defines the JSON schemas and CSV structures used throughout the pipeline. All schemas live under `contracts/` and are validated with `jsonschema` during CI.

## Schemas

### `contracts/background_frame.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "BackgroundFrame"
type: object
properties:
  frame_id:
    type: string
    description: "Unique identifier for the background image (e.g., bg_001)."
  entropy:
    type: number
    description: "Shannon entropy of the grayscale image."
  color_variance:
    type: number
    description: "Mean variance across the RGB channels."
  object_count:
    type: integer
    minimum: 0
    description: "Number of objects detected by YOLOv8n; zero if none."
required:
  - frame_id
  - entropy
  - color_variance
  - object_count
additionalProperties: false
```

### `contracts/human_rating.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HumanRating"
type: object
properties:
  image_id:
    type: string
    description: "Identifier matching a BackgroundFrame."
  participant_id:
    type: string
    description: "Anonymous participant code."
  complexity_score:
    type: number
    minimum: 1
    maximum: 10
    description: "Self‑reported visual complexity (1‑10)."
required:
  - image_id
  - participant_id
  - complexity_score
additionalProperties: false
```

### `contracts/participant_session.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ParticipantSession"
type: object
properties:
  participant_id:
    type: string
  session_id:
    type: string
  baseline_rt:
    type: number
    description: "Mean reaction time (ms) on baseline task."
  familiarity_score:
    type: number
    minimum: 1
    maximum: 10
    description: "Pre‑experiment self‑reported familiarity with meeting content (1‑10)."
  trials:
    type: array
    items:
      type: object
      properties:
        clip_id:
          type: string
        background_frame_id:
          type: string
        task_difficulty:
          type: string
          enum: [low, medium, high]
        nasa_tlx_score:
          type: number
          minimum: 0
          maximum: 100
        post_rt:
          type: number
          description: "Mean RT (ms) after the clip."
        rt_valid:
          type: boolean
          description: "True if TLX and RT present; False otherwise."
      required:
        - clip_id
        - background_frame_id
        - task_difficulty
        - nasa_tlx_score
        - post_rt
        - rt_valid
    description: "One entry per experimental trial."
required:
  - participant_id
  - session_id
  - baseline_rt
  - familiarity_score
  - trials
additionalProperties: false
```

### `contracts/analysis_result.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "AnalysisResult"
type: object
properties:
  model_name:
    type: string
    description: "Identifier of the statistical model (e.g., lmm_full)."
  fixed_effects:
    type: array
    items:
      type: object
      properties:
        predictor:
          type: string
        estimate:
          type: number
        conf_low:
          type: number
        conf_high:
          type: number
        p_value:
          type: number
        p_adj:
          type: number
        effect_size:
          type: number
          description: "Cohen's d or standardized beta."
      required:
        - predictor
        - estimate
        - conf_low
        - conf_high
        - p_value
        - p_adj
        - effect_size
  vif:
    type: object
    additionalProperties:
      type: number
    description: "VIF per fixed effect."
  fwer_observed:
    type: number
    description: "Family‑wise error rate from null simulations (target α = 0.05)."
  sensitivity:
    type: array
    items:
      type: object
      properties:
        alpha:
          type: number
        significant_predictors:
          type: integer
        effect_size_sd:
          type: number
      required:
        - alpha
        - significant_predictors
        - effect_size_sd
required:
  - model_name
  - fixed_effects
  - vif
  - fwer_observed
  - sensitivity
additionalProperties: false
```

## CSV Formats
| File | Description | Primary Key |
|------|-------------|-------------|
| `data/stimuli/metadata/frames.csv` | `frame_id, entropy, color_variance, object_count` | `frame_id` |
| `data/measurements/pilot_ratings.csv` | `image_id, participant_id, complexity_score` | composite |
| `data/processed/metrics.csv` | Merges background frames with pilot correlations. | `frame_id` |
| `data/derived/individual_metric_correlations.csv` | `metric, pearson_r, p_value` | `metric` |
| `data/derived/rt_measurements.json` | JSON list of baseline and post‑clip RT per participant. | — |
| `data/derived/analysis_results.json` | Serialized `AnalysisResult` object. | — |

All files are checksum‑verified; SHA‑256 hashes stored in `data/metadata/dataset_manifest.json`.

## Validation Notes
- Pilot rating records (`data/measurements/pilot_ratings.csv`) are validated against `contracts/human_rating.schema.yaml`.  
- The final analysis output (`data/derived/analysis_results.json`) is validated against `contracts/analysis_result.schema.yaml` via the CI test `tests/contract/test_schemas.py`.  

--- 