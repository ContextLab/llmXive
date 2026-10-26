# Data Model: MobileForge Logic Distillation

## Overview
All pipeline artifacts reside under `outputs/` and are validated against JSON‑Schema definitions located in `contracts/`. The platform’s contract test suite automatically checks each file.

## Core Schemas

| Artifact | Path (project‑owned) | Schema |
|----------|----------------------|--------|
| Extraction Dataset (train & test splits) | `outputs/train_split.parquet`, `outputs/test_split.parquet` | `contracts/dataset.schema.yaml` |
| Extraction Metadata | `outputs/extraction_meta.json` | *(no schema – free‑form JSON) |
| Power‑Analysis Output | `outputs/power_analysis.json` | `contracts/power_analysis.schema.yaml` |
| Training Log | `outputs/training_log.json` | *(no schema – free‑form) |
| Evaluation Results (SSoT) | `outputs/evaluation_results.json` | `contracts/evaluation.schema.yaml` |
| Evaluation Task List | `outputs/eval_tasks.json` | *(simple list of task IDs; no dedicated schema) |

## Data Integrity Rules
- **Checksum Verification**: Loaders compute SHA‑256 of each raw file in `data/raw/` and compare against entries in `data/checksums.json`. Mismatch → hard failure.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived artifacts receive new filenames under `outputs/`.  
- **No Synthetic Fallbacks**: Loaders raise `FileNotFoundError` if any required artifact is missing.  
- **PII Prohibition**: Schemas forbid fields that could contain personal identifiers.

## Single Source of Truth
`outputs/evaluation_results.json` is designated as the **authoritative SSoT** for all figures, tables, and statistical claims produced by this project, satisfying Constitution Principle I.

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-930-llmxive-follow-up-extending-mobileforge/specs/001-llmxive-follow-up-extending-mobileforge/contracts/extraction_dataset.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "ExtractionDataset Schema"
description: "Schema for the filtered MobileForge training dataset containing failed-then-success triples."
type: "object"
properties:
  metadata:
    type: "object"
    properties:
      source_url:
        type: "string"
        description: "Verified URL of the source dataset."
      extraction_timestamp:
        type: "string"
        format: "date-time"
      checksum:
        type: "string"
        description: "SHA-256 checksum of the raw source file."
      record_count:
        type: "integer"
        minimum: 0
        description: "Number of valid triples extracted."
      source_app:
        type: "string"
        description: "App name from metadata."
    # metadata is optional; missing fields will not cause validation failure
  triples:
    type: "array"
    items:
      type: "object"
      required:
        - "ui_state"
        - "corrective_hint"
        - "action"
        - "trajectory_id"
        - "status"
      properties:
        ui_state:
          type: "string"
          minLength: 1
          description: "Text description of the UI state."
        corrective_hint:
          type: "string"
          minLength: 1
          description: "Linguistic hint provided after failure."
        action:
          type: "string"
          description: "Serialized optimal action sequence."
        trajectory_id:
          type: "string"
          description: "Unique ID of the source trajectory."
        status:
          type: "string"
          enum:
            - "failed_then_success"
            - "success"
            - "failed"
            - "initial_success"
          description: "Trajectory status filter."
    description: "List of valid training triples."
required:
  - metadata
  - triples
additionalProperties: false