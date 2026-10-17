# Data Model: Evaluating LLM Fidelity in Commit-to-Documentation Translation

## Overview
The data model defines the canonical JSON/YAML structures used throughout the pipeline. All files are version‑controlled under `data/` and validated against the schemas in `contracts/`.

## Schemas

### 1. CommitPair (`commitpair.schema.yaml`)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `commit_hash` | string | Full 40‑character SHA‑1 hash | pattern: `^[0-9a-f]{40}$` |
| `commit_message` | string | Original commit message (non‑empty) | minLength: 1 |
| `repository_name` | string | One of `pandas`, `requests`, `scikit-learn`, `flask`, `django` | enum |
| `doc_diff` | string | Unified diff of documentation files (`.md`/`.rst`) for that commit | non‑empty |
| `timestamp` | string | ISO‑8601 UTC timestamp of the commit | format: date-time |
| `metadata` | object | Optional provenance fields (e.g., `author`, `url`) | – |

### 2. GeneratedOutput (`generatedoutput.schema.yaml`)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `commit_hash` | string | FK to `CommitPair.commit_hash` | pattern: `^[0-9a-f]{40}$` |
| `model_id` | string | Identifier: `phi3-mini`, `gemma2-2b`, `llama3.2-3b` | enum |
| `generated_text` | string | Full documentation update produced by the LLM | non‑empty |
| `generation_time_s` | number | Wall‑clock seconds spent generating | minimum: 0 |
| `status` | string | `success`, `generation_failed` | enum |
| `log` | string | Optional error or retry log | – |

### 3. EntitySet (`entityset.schema.yaml`)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `sample_id` | string | `{commit_hash}_{model_id}` | – |
| `entities` | array of object | List of extracted entities | – |
| Entity object fields: |
| `text` | string | Raw entity string | – |
| `type` | string | `surface` or `intent` | enum |
| `source` | string | `human` or `generated` | enum |
| `verified` | boolean | For surface entities: true if present in repo codebase (via `git grep` + AST) | – |

### 4. FidelityMetric (`fidelitymetric.schema.yaml`)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `sample_id` | string | FK to `EntitySet.sample_id` | – |
| `model_id` | string | Same as in `GeneratedOutput` | enum |
| `precision_intent` | number | Ratio TP/(TP+FP) for intent | minimum: 0, maximum: 1 |
| `recall_intent` | number | Ratio TP/(TP+FN) for intent | minimum: 0, maximum: 1 |
| `precision_surface` | number | Ratio TP/(TP+FP) for surface | minimum: 0, maximum: 1 |
| `recall_surface` | number | Ratio TP/(TP+FN) for surface | minimum: 0, maximum: 1 |
| `hallucination_rate` | number | Fraction of generated surface entities not found in the repository codebase | minimum: 0, maximum: 1 |
| `timestamp` | string | When the metric was computed (ISO‑8601) | format: date-time |

## Derivation Flow
1. **Raw Extraction** → `CommitPair` CSV → `commitpair.schema.yaml` validation.  
2. **Generation** → `GeneratedOutput` JSON → schema validation.  
3. **Entity Extraction** on both human `doc_diff` and `generated_text` → `EntitySet`. Surface entities are verified via **combined `git grep` and AST parsing** to avoid false‑negative hallucination counts.  
4. **Scoring** compares human vs. generated EntitySets → `FidelityMetric`.  
5. **Aggregation** (`data/processed/fidelity_metrics.csv`) is derived from all `FidelityMetric` rows.

All intermediate files retain the original checksum in `data/metadata.yaml` to satisfy the Data Hygiene principle. The inclusion of `entityset.schema.yaml` in the contract validation step ensures schema consistency across the pipeline.

---



