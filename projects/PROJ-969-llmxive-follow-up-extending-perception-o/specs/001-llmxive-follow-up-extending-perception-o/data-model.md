# Data Model: llmXive follow-up: extending "Perception or Prejudice"

## Overview
All pipeline stages read/write structured artifacts that are validated against JSON schemas stored in `contracts/`. The schemas guarantee reproducibility, single source of truth, and enable automated contract testing.

## Core Schemas

### 1. `video_metadata.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: VideoMetadata
type: object
required: [video_id, video_url, transcript, setting, culture, behavior_tags]
properties:
  video_id:
    type: string
    description: Unique identifier for the video sample.
  video_url:
    type: string
    format: uri
    description: Direct URL to the video file (streamable).
  transcript:
    type: string
    description: Full spoken transcript of the video.
  setting:
    type: string
    description: Situational tag (e.g., "job interview").
  culture:
    type: string
    description: Cultural context (e.g., "East Asian").
  behavior_tags:
    type: array
    items:
      type: string
    description: List of observed behaviors (e.g., ["smiles", "nods"]).
  ambiguous:
    type: boolean
    default: false
    description: True if contradictory behavior tags exist (FR‑011).
```

### 2. `context_profile.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: ContextProfile
type: object
required: [profile_id, setting, culture, norms, scripts]
properties:
  profile_id:
    type: string
    description: Identifier linking to a video metadata entry.
  setting:
    type: string
  culture:
    type: string
  norms:
    type: array
    items:
      type: string
    description: List of social norms relevant to the setting/culture.
  scripts:
    type: array
    items:
      type: string
    description: Short situational scripts (e.g., "maintain eye contact").
```

### 3. `model_output.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: ModelOutput
type: object
required: [model_name, video_id, condition, rating, reasoning, grounding_score, context_cited, valid_json]
properties:
  model_name:
    type: string
  video_id:
    type: string
  condition:
    type: string
    enum: [baseline, context, noise]
  rating:
    type: integer
    minimum: 1
    maximum: 5
  reasoning:
    type: string
  grounding_score:
    type: number
    minimum: 0.0
    maximum: 1.0
  context_cited:
    type: boolean
    description: True if reasoning references at least one phrase from the injected context (IR metric).
  valid_json:
    type: boolean
    description: True if the model output conforms to the expected JSON schema.
```

### 4. `metric_record.schema.yaml` *(contract file)*
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: MetricRecord
type: object
required: [model_name, condition, prejudice_rate, holistic_grounding_rate, integration_failure_rate, n_valid, n_invalid, n_ambiguous]
properties:
  model_name:
    type: string
  condition:
    type: string
    enum: [baseline, context, noise]
  prejudice_rate:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "PR as defined in the spec."
  holistic_grounding_rate:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "HR as defined in the spec."
  integration_failure_rate:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "IR (percentage of outputs that did not cite injected context)."
  n_valid:
    type: integer
    minimum: 0
    description: Number of samples included after excluding invalid JSON or timeouts (FR‑010).
  n_invalid:
    type: integer
    minimum: 0
    description: Number of excluded samples (invalid output).
  n_ambiguous:
    type: integer
    minimum: 0
    description: Number of samples flagged with grounding‑uncertainty (FR‑011).
```

## Data Flow Diagram (conceptual)
```
raw video metadata ──► video_metadata.schema.yaml
               │
               ▼
       knowledge_base.json ──► context_profile.schema.yaml
               │
               ▼
          inference (baseline / context / noise)
               │
               ▼
          model_output.schema.yaml
               │
               ▼
          metrics.py ──► metric_record.schema.yaml
               │
               ▼
          analysis.py → results.md / figures
```

Each stage reads the previous artifact, validates against its schema, and writes the next artifact to `data/derived/`. Contract tests enforce schema compliance before downstream stages run.

---
