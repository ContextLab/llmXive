# Data Model: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Overview
The project manipulates audio clips, distortion parameters, ASR hypotheses, and derived metrics. All intermediate and final artifacts are stored as Parquet files to enable efficient streaming and reproducibility.

## Core Schemas

### 1. `stress_curves.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Stress Curves"
type: object
properties:
  clip_id:
    type: string
    description: "Unique identifier from the Voices‑in‑the‑Wild‑2M source."
  speaker_id:
    type: string
    description: "Speaker identifier (used for stratification)."
  environment_id:
    type: string
    description: "Recording environment proxy (used for stratification)."
  model_name:
    type: string
    enum: ["whisper-tiny", "distil-whisper", "wav2vec2-base", "custom-model-1", "custom-model-2"]
    description: "ASR model used for inference."
  snr_db:
    type: number
    description: "Signal‑to‑Noise Ratio in decibels."
  rt60_s:
    type: number
    description: "Reverberation time (RT60) in seconds."
  distortion_id:
    type: string
    description: "Composite key e.g., 'snr-10_rt60-0.8'."
  asr_transcript:
    type: string
    description: "ASR hypothesis."
  wer:
    type: number
    description: "Word Error Rate (0 = perfect)."
  sss:
    type: number
    description: "Semantic Similarity Score (cosine similarity, 0‑1)."
  phoneme_edit_distance:
    type: number
    description: "Fallback metric for high‑reverb clips (optional)."
  timestamp:
    type: string
    format: date-time
    description: "Processing timestamp."
required:
  - clip_id
  - speaker_id
  - environment_id
  - model_name
  - snr_db
  - rt60_s
  - distortion_id
  - asr_transcript
  - wer
  - sss
additionalProperties: false
```

### 2. `collapse_points.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Collapse Points"
type: object
properties:
  clip_id:
    type: string
    description: "Identifier of the audio clip."
  model_name:
    type: string
    enum: ["whisper-tiny", "distil-whisper", "wav2vec2-base", "custom-model-1", "custom-model-2"]
    description: "ASR model."
  collapse_intensity:
    type: object
    description: "Distortion vector where collapse occurs (null if none)."
    properties:
      snr_db:
        type: number
        description: "SNR at collapse."
      rt60_s:
        type: number
        description: "RT60 at collapse."
    required:
      - snr_db
      - rt60_s
  collapse_method:
    type: string
    enum: ["threshold_crossing", "inflection_point", "none"]
    description: "Algorithmic source per FR‑021."
  baseline_sss:
    type: number
    description: "SSS on clean‑audio baseline."
  baseline_wer:
    type: number
    description: "WER on clean‑audio baseline."
  detection_params:
    type: object
    description: "Parameters used for the deterministic rule."
    properties:
      sss_threshold_factor:
        type: number
        description: "Factor of baseline SSS (default 0.5)."
      wer_multiplier:
        type: number
        description: "Multiplier of baseline WER (default 2)."
    required:
      - sss_threshold_factor
      - wer_multiplier
required:
  - clip_id
  - model_name
  - collapse_intensity
  - collapse_method
  - baseline_sss
  - baseline_wer
additionalProperties: false
```

### 3. `collapse_point.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Collapse Point (Inflection‑Point Intensity)"
type: object
properties:
  collapse_id:
    type: string
    description: "Unique identifier for the inflection‑point record."
  clip_id:
    type: string
    description: "Foreign key to AudioClip."
  model_name:
    type: string
    description: "ASR model identifier."
  inflection_intensity:
    type: number
    description: "Distortion intensity (e.g., normalized SNR‑RT60 coordinate) at the maximum negative derivative."
  inflection_derivative:
    type: number
    description: "Value of the first derivative at the inflection point."
required:
  - collapse_id
  - clip_id
  - model_name
  - inflection_intensity
  - inflection_derivative
additionalProperties: false
```

### 4. `critical_vector.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Critical Interaction Vector"
type: object
properties:
  vector_id:
    type: string
    description: "Unique identifier for the critical vector."
  model_name:
    type: string
    description: "ASR model identifier."
  snr_coeff:
    type: number
    description: "Coefficient for SNR."
  rt60_coeff:
    type: number
    description: "Coefficient for RT60."
  snr_sq_coeff:
    type: number
    description: "Coefficient for SNR squared."
  rt60_sq_coeff:
    type: number
    description: "Coefficient for RT60 squared."
  interaction_coeff:
    type: number
    description: "Coefficient for the SNR × RT60 interaction term."
  r2_score:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "R‑squared on test set."
  mae:
    type: number
    minimum: 0.0
    description: "Mean Absolute Error."
  p_value_interaction:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "FDR‑corrected p‑value for interaction term."
  shap_interaction_strength:
    type: number
    description: "SHAP interaction strength magnitude."
required:
  - vector_id
  - model_name
  - snr_coeff
  - rt60_coeff
  - snr_sq_coeff
  - rt60_sq_coeff
  - interaction_coeff
  - r2_score
  - mae
  - p_value_interaction
  - shap_interaction_strength
additionalProperties: false
```

### 5. `dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Audio Clip Metadata"
type: object
properties:
  clip_id:
    type: string
    description: "Unique identifier from the source dataset."
  speaker_id:
    type: string
    description: "Speaker identifier."
  environment_id:
    type: string
    description: "Recording environment proxy."
  transcript:
    type: string
    description: "Ground‑truth transcript."
  audio_path:
    type: string
    description: "Relative path to the raw audio file."
required:
  - clip_id
  - speaker_id
  - environment_id
  - transcript
  - audio_path
additionalProperties: false
```

## Data Flow Diagram (logical)

```
Raw ASR parquet --> download.py --> subset.parquet
subset.parquet --> distort.py --> stress_curves.parquet (Schema 1)
stress_curves.parquet --> sss.py (adds sss, wer) --> updated stress_curves.parquet
stress_curves.parquet --> collapse.py --> collapse_points.parquet (Schema 2)
collapse_points.parquet --> collapse_point.py --> collapse_point.parquet (Schema 3)
collapse_point.parquet + stress_curves.parquet --> regression.py --> model_metrics.parquet + critical_vector.parquet (Schema 4)
```

All files are version‑hashed; any change produces a new file name suffix (`_<hash>.parquet`).

---


## Notes on Covariates
The `collapse_points.schema.yaml` includes `baseline_sss` and `baseline_wer`, which are used as **covariates** (not targets) in the regression model to control for clip‑level difficulty, satisfying FR‑127c2986 concern; they improve construct validity.
