# Data Model: AI for Auto-Research: Reproduction Artifacts

## Overview
This document defines the data structures for the reproduction pipeline's outputs, logs, and validation reports. The model is designed to be lightweight and compatible with CPU-only processing.

## Entities

### 1. ReproductionRun
Represents a single execution of the pipeline.
- `run_id`: Unique identifier (UUID).
- `start_time`: ISO8601 timestamp.
- `end_time`: ISO8601 timestamp (or null if failed).
- `status`: Enum (`SUCCESS`, `FAILED`, `TIMEOUT`).
- `environment`: Object (`cpu_only`, `ram_used_gb`, `disk_used_gb`, `mock_mode_active`).

### 2. GeneratedArtifact
Represents a file produced by the pipeline.
- `file_path`: Relative path from `output/`.
- `file_type`: Enum (`TEXT`, `IMAGE`, `DATA`, `LOG`).
- `size_bytes`: Integer.
- `is_valid`: Boolean (checked by validation script).
- `fabrication_score`: Float (0.0 to 1.0, where 1.0 is likely fake).

### 3. CostLog
Represents API usage logs.
- `timestamp`: ISO8601.
- `service`: String (e.g., "OpenAI", "Anthropic", "Mock").
- `tokens_used`: Integer.
- `cost_usd`: Float.

### 4. ValidationReport
The final summary of the run.
- `run_id`: Reference to `ReproductionRun`.
- `artifact_count`: Integer.
- `total_cost_usd`: Float or null.
- `fabrication_detected`: Boolean (True if any artifact score > 0.8).
- `methodological_deviations`: List of strings.
- `claim_status`: Object (`cost_claim`: "Verified"/"Unverifiable"/"Failed", `novelty_claim`: "Verified"/"Unverifiable"/"Failed").
- `conclusion`: String (Pass/Fail/Partial).

## Schema Definitions

### Artifact Schema (YAML)
```yaml
# contracts/artifact_schema.yaml
type: object
properties:
  file_path:
    type: string
    description: "Relative path to the artifact"
  file_type:
    type: string
    enum:
      - TEXT
      - IMAGE
      - DATA
      - LOG
  size_bytes:
    type: integer
    minimum: 0
  is_valid:
    type: boolean
  fabrication_score:
    type: number
    minimum: 0.0
    maximum: 1.0
required:
  - file_path
  - file_type
  - size_bytes
  - is_valid
```

### CostLog Schema (YAML)
```yaml
# contracts/cost_log_schema.yaml
type: object
properties:
  timestamp:
    type: string
    format: date-time
  service:
    type: string
  tokens_used:
    type: integer
    minimum: 0
  cost_usd:
    type: number
    minimum: 0.0
required:
  - timestamp
  - service
  - cost_usd
```

### ValidationReport Schema (YAML)
```yaml
# contracts/validation_report_schema.yaml
type: object
properties:
  run_id:
    type: string
    format: uuid
  artifact_count:
    type: integer
    minimum: 0
  total_cost_usd:
    type: ["number", "null"]
    description: "Total cost in USD, or null if not calculable"
  fabrication_detected:
    type: boolean
  methodological_deviations:
    type: array
    items:
      type: string
  claim_status:
    type: object
    properties:
      cost_claim:
        type: string
        enum:
          - VERIFIED
          - UNVERIFIABLE
          - FAILED
      novelty_claim:
        type: string
        enum:
          - VERIFIED
          - UNVERIFIABLE
          - FAILED
  conclusion:
    type: string
    enum:
      - PASS
      - FAIL
      - PARTIAL
required:
  - run_id
  - artifact_count
  - fabrication_detected
  - methodological_deviations
  - claim_status
  - conclusion
```