# Data Model: Evaluating LLM Fidelity in Commit-to-Documentation Translation

## Overview
The data model defines the canonical JSON/YAML structures used throughout the pipeline. All intermediate and final artifacts are version‑controlled under `data/` and validated against the consolidated schema in `contracts/project.schema.yaml`.

## Consolidated Schema (`contracts/project.schema.yaml`)
The single schema contains four definitions (`CommitPair`, `GeneratedOutput`, `EntitySet`, `FidelityMetric`) under `$defs`. Each artifact produced by the pipeline must conform to the appropriate definition; the root of the schema is an empty object because validation is performed against the definitions directly.

### Root Object
```yaml
type: object
additionalProperties: false
```

### Definitions

#### CommitPair
```yaml
CommitPair:
  type: object
  required:
    - commit_hash
    - commit_message
    - repository_name
    - doc_diff
    - timestamp
  properties:
    commit_hash:
      type: string
      pattern: "^[0-9a-f]{40}$"
      description: "Full SHA‑1 hash of the commit."
    commit_message:
      type: string
      minLength: 1
      description: "Original commit message."
    repository_name:
      type: string
      enum: ["pandas", "requests", "scikit-learn", "flask", "django"]
      description: "Name of the source repository."
    doc_diff:
      type: string
      minLength: 1
      description: "Unified diff of documentation files changed in the commit."
    timestamp:
      type: string
      format: date-time
      description: "UTC timestamp of the commit."
    metadata:
      type: object
      description: "Optional provenance information (author, URL, etc.)."
  additionalProperties: false
```

#### GeneratedOutput
```yaml
GeneratedOutput:
  type: object
  required:
    - commit_hash
    - model_id
    - generated_text
    - generation_time_s
    - status
  properties:
    commit_hash:
      type: string
      pattern: "^[0-9a-f]{40}$"
      description: "FK to CommitPair.commit_hash."
    model_id:
      type: string
      enum: ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
      description: "Identifier of the LLM used."
    generated_text:
      type: string
      minLength: 1
      description: "Full documentation update produced by the LLM."
    generation_time_s:
      type: number
      minimum: 0
      description: "Wall‑clock seconds spent generating."
    status:
      type: string
      enum: ["success", "generation_failed"]
      description: "Generation outcome."
    log:
      type: string
      description: "Optional error or retry log."
  additionalProperties: false
```

#### EntitySet
```yaml
EntitySet:
  type: object
  required:
    - sample_id
    - entities
  properties:
    sample_id:
      type: string
      description: "Composite key `{commit_hash}_{model_id}`."
    entities:
      type: array
      items:
        type: object
        required:
          - text
          - type
          - source
          - verified
        properties:
          text:
            type: string
            description: "Raw entity string."
          type:
            type: string
            enum: ["surface", "intent"]
            description: "Entity category."
          source:
            type: string
            enum: ["human", "generated"]
            description: "Origin of the entity."
          verified:
            type: boolean
            description: "True if surface entity found in repo codebase (via git grep + AST)."
        additionalProperties: false
  additionalProperties: false
```

#### FidelityMetric
```yaml
FidelityMetric:
  type: object
  required:
    - sample_id
    - model_id
    - precision_intent
    - recall_intent
    - precision_surface
    - recall_surface
    - hallucination_rate
    - timestamp
  properties:
    sample_id:
      type: string
      description: "Composite key `{commit_hash}_{model_id}`."
    model_id:
      type: string
      enum: ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
      description: "Identifier of the LLM used."
    precision_intent:
      type: number
      minimum: 0
      maximum: 1
      description: "Precision for technical‑intent entities."
    recall_intent:
      type: number
      minimum: 0
      maximum: 1
      description: "Recall for technical‑intent entities."
    precision_surface:
      type: number
      minimum: 0
      maximum: 1
      description: "Precision for surface entities."
    recall_surface:
      type: number
      minimum: 0
      maximum: 1
      description: "Recall for surface entities."
    hallucination_rate:
      type: number
      minimum: 0
      maximum: 1
      description: "Proportion of generated surface entities not found in the repository codebase."
    timestamp:
      type: string
      format: date-time
      description: "When the metric was computed."
  additionalProperties: false
```

## Derivation Flow
1. **Raw Extraction** → `CommitPair` CSV → validated against `CommitPair` definition.  
2. **Human Gold‑Standard Annotation** → `data/gold/annotations.csv` containing `commit_hash` and `intent_entities`; each entry is double‑annotated and κ ≥ 0.6. This file serves as the reference for intent extraction.  
3. **Generation** → `GeneratedOutput` JSON → validated against `GeneratedOutput`.  
4. **Entity Extraction** on both human `doc_diff` and `generated_text` → `EntitySet` JSON; surface entities are verified via combined `git grep` and AST parsing.  
5. **Scoring** compares human vs. generated `EntitySet` → `FidelityMetric` JSON.  
6. **Aggregation** (`data/processed/fidelity_metrics.csv`) is derived from all `FidelityMetric` rows.

All intermediate files retain the original checksum in `data/metadata.yaml` to satisfy the Data Hygiene principle. The inclusion of the four definitions in a single contract file satisfies the requirement for at least one schema while enabling comprehensive validation.

---

