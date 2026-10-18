# Data Model: MobileForge Logic Distillation

## Overview
All pipeline artifacts are stored under `outputs/` and validated against JSON‑Schema definitions in `contracts/`. The platform’s contract test suite automatically verifies each file.

## Core Schemas

| Artifact | Path (project‑owned) | Schema |
|----------|----------------------|--------|
| Extraction Dataset (raw & filtered) | `outputs/train_split.parquet`, `outputs/test_split.parquet` | `contracts/dataset.schema.yaml` |
| Extraction Metadata | `outputs/extraction_meta.json` | *(no schema enforced; simple JSON)* |
| Power‑Analysis Output | `outputs/power_analysis.json` | `contracts/power_analysis.schema.yaml` |
| Training Log / Provenance | `outputs/training_log.json` | *(no schema enforced)* |
| Evaluation Results | `outputs/evaluation_results.json` | `contracts/evaluation.schema.yaml` |
| Evaluation Task List | `outputs/eval_tasks.json` | *(simple list of task IDs; no dedicated schema)* |

## Data Integrity Rules
- **Checksum Verification**: Loaders compute SHA‑256 of raw files in `data/raw/` and compare to `data/checksums.json`. Mismatch → hard failure.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived artifacts receive new filenames under `outputs/`.  
- **No Synthetic Fallbacks**: Loaders raise `FileNotFoundError` if any required artifact is missing.  
- **PII Prohibition**: Schemas forbid fields that could contain personal identifiers.  

## Single Source of Truth
The file `outputs/evaluation_results.json` is designated as the **authoritative SSoT** for all figures, tables, and statistical claims produced by this project, satisfying Constitution Principle I.

---



