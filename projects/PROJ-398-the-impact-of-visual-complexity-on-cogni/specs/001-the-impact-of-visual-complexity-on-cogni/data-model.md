# Data Model: Visual Complexity & Cognitive Load

## Overview

This document defines the data structures for the project, ensuring alignment with the `spec.md` entities and the project's Data Hygiene principles.

## Entities

### 1. BackgroundFrame (Stimulus)

Represents a single background image used as a stimulus.

**Source**: `data/stimuli/` (images) + `data/metadata/stimuli.json` (metrics).

```yaml
# contracts/stimulus_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "BackgroundFrame"
type: object
properties:
  frame_id:
    type: string
    description: "Unique identifier for the stimulus (e.g., 'stim_001.png')"
  entropy:
    type: number
    description: "Shannon entropy of the image (float)"
  color_variance:
    type: number
    description: "Variance of color channels (float)"
  object_count:
    type: integer
    description: "Number of objects detected by YOLOv8n"
  checksum:
    type: string
    description: "SHA-256 checksum of the raw image file (for reproducibility)"
required:
  - frame_id
  - entropy
  - color_variance
  - object_count
  - checksum
```

### 2. HumanRating (Pilot Data)

Represents a human participant's rating of a background image.

**Source**: `data/measurements/pilot_ratings.json`.

```yaml
# contracts/human_rating_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HumanRating"
type: object
properties:
  rating_id:
    type: string
    description: "Unique ID for the rating record"
  participant_id:
    type: string
    description: "Anonymous ID of the pilot participant"
  frame_id:
    type: string
    description: "Reference to BackgroundFrame"
  complexity_score:
    type: integer
    minimum: 1
    maximum: 10
    description: "Human rating of visual complexity (1-10)"
  role:
    type: string
    enum: ["Pilot_Ground_Truth"]
    description: "Explicitly marks this data as pilot ground truth, never to be used as main study outcome."
  timestamp:
    type: string
    format: date-time
    description: "ISO 8601 timestamp of the rating"
required:
  - rating_id
  - participant_id
  - frame_id
  - complexity_score
  - role
  - timestamp
```

### 3. ParticipantSession (Main Study)

Represents a single participant's session in the main study.

**Source**: `data/measurements/main_study_sessions.json`.

```yaml
# contracts/session_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ParticipantSession"
type: object
properties:
  session_id:
    type: string
    description: "Unique session ID"
  participant_id:
    type: string
    description: "Anonymous participant ID"
  baseline_rt_mean:
    type: number
    description: "Mean reaction time (ms) during baseline task"
  baseline_rt_accuracy:
    type: number
    description: "Accuracy percentage during baseline task"
  trials:
    type: array
    items:
      type: object
      properties:
        trial_id:
          type: string
        frame_id:
          type: string
        nasa_tlx_score:
          type: number
          description: "Overall NASA-TLX score"
        rt_mean:
          type: number
          description: "Mean reaction time (ms) for post-task"
        rt_accuracy:
          type: number
          description: "Accuracy percentage for post-task"
        order_index:
          type: integer
          description: "Position in the counterbalanced sequence"
      required:
        - trial_id
        - frame_id
        - nasa_tlx_score
        - rt_mean
        - rt_accuracy
        - order_index
  attention_check_passed:
    type: boolean
    description: "Whether the participant passed attention checks"
required:
  - session_id
  - participant_id
  - baseline_rt_mean
  - baseline_rt_accuracy
  - trials
  - attention_check_passed
```

### 4. AnalysisResult

Represents the output of the statistical model.

**Source**: `data/processed/analysis_results.json`.

```yaml
# contracts/analysis_result_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "AnalysisResult"
type: object
properties:
  model_id:
    type: string
    description: "Identifier for the model run"
  predictors:
    type: array
    items:
      type: string
    description: "List of predictors used (e.g., entropy, variance)"
  fixed_effects:
    type: object
    description: "Fixed effect estimates, p-values, CIs"
    additionalProperties:
      type: object
      properties:
        estimate:
          type: number
        std_err:
          type: number
        p_value:
          type: number
        p_value_adj:
          type: number
          description: "Benjamini-Hochberg adjusted p-value"
        ci_lower:
          type: number
        ci_upper:
          type: number
        vif:
          type: number
          description: "Variance Inflation Factor"
  sensitivity_analysis:
    type: object
    properties:
      alpha_thresholds:
        type: array
        items:
          type: number
        description: "List of alpha values swept (e.g., [0.01, 0.05, 0.1])"
      significant_counts:
        type: array
        items:
          type: integer
        description: "Count of significant predictors at each alpha"
      effect_size_sd:
        type: number
        description: "Standard deviation of effect sizes across thresholds"
  fwer:
    type: number
    description: "Observed Family-Wise Error Rate from null simulation"
required:
  - model_id
  - predictors
  - fixed_effects
  - sensitivity_analysis
  - fwer
```

## Data Flow

1.  **Curate**: `code/stimuli/` (real images) -> `data/stimuli/` (images) + `stimuli_schema.yaml` (metrics).
2.  **Pilot**: `pilot/app.py` -> `human_rating_schema.yaml` (JSON).
3.  **Validate**: `pilot/validate.py` -> Correlation report (text). **Pilot data excluded from main analysis.**
4.  **Main**: `main_study/app.py` -> `session_schema.yaml` (JSON).
5.  **Analyze**: `analysis/lmm.py` + `sensitivity.py` -> `analysis_result_schema.yaml` (JSON).
6.  **Report**: `paper/` generated from `analysis_result_schema.yaml`.
