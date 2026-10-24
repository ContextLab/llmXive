# Data Model: Evaluating LLM Fidelity in Commit-to-Documentation Translation

## Overview
All pipeline artifacts are defined as JSON/YAML objects that must conform to the consolidated schema in `contracts/project.schema.yaml`. Each definition corresponds to a concrete file or directory under `data/`.

## Consolidated Schema (`contracts/project.schema.yaml`)
The root schema is an empty object; the useful definitions reside under `$defs`. The four primary definitions are:

1. **CommitPair** – raw input rows (`data/raw/commit_pairs.csv`).  
2. **GeneratedOutput** – LLM‑generated documentation (`data/generated/<model_id>/<commit_hash>.txt` plus accompanying JSON metadata).  
3. **EntitySet** – extracted entities from human and generated texts (`data/intermediate/*_entities/*.json`).  
4. **FidelityMetric** – per‑sample precision/recall/hallucination scores (`data/processed/fidelity_metrics.csv`).  

All definitions are reproduced verbatim in `contracts/project.schema.yaml` (see the contract file).

## Derivation Flow
1. **Raw Extraction** → `CommitPair` CSV → validated against `CommitPair`.  
2. **Gold Annotation** → `data/gold/annotations.csv` (human intent entities) – not a separate schema but must align with `CommitPair` and `EntitySet`.  
3. **Generation** → `GeneratedOutput` JSON files → validated against `GeneratedOutput`.  
4. **Entity Extraction** → `EntitySet` JSON per sample → validated against `EntitySet`.  
5. **Scoring** → `FidelityMetric` rows → validated against `FidelityMetric`.  

Each transformation writes a new file; the original source file remains unchanged (Constitution III). Checksums of all files are recorded in `data/metadata.yaml`.

## File‑Level Mapping
| Directory | File Pattern | Schema Definition |
|-----------|--------------|-------------------|
| `data/raw/` | `commit_pairs.csv` | `CommitPair` (row‑wise) |
| `data/generated/` | `<model_id>/<commit_hash>.txt` + `<model_id>/<commit_hash>.json` | `GeneratedOutput` |
| `data/intermediate/surface_entities/` | `<commit_hash>_<model_id>.json` | `EntitySet` (surface) |
| `data/intermediate/intent_entities/` | `<commit_hash>_<model_id>.json` | `EntitySet` (intent) |
| `data/processed/` | `fidelity_metrics.csv` | `FidelityMetric` (row‑wise) |
| `data/gold/` | `annotations.csv` | *implicit* alignment with `CommitPair` and `EntitySet` |
| `data/metadata.yaml` | – | No schema; records SHA‑256 checksums for every file in `data/`. |

All files are UTF‑8 encoded, newline‑normalized (`\n`), and include a header row where applicable.

### FidelityMetric Extension
The `FidelityMetric` schema now includes **two hallucination rate fields**:
- `hallucination_rate` (surface entities)
- `intent_hallucination_rate` (intent entities)

Both are numeric values in [0, 1] and are computed during the scoring phase.

---

