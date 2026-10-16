# Data Model: MobileForge Logic Distillation

## Overview
All pipeline artifacts are stored under `outputs/` and validated against JSON‑Schema definitions in `contracts/`. The platform’s contract test suite will automatically verify each file.

## Core Schemas

| Artifact | Path (project‑owned) | Schema |
|----------|----------------------|--------|
| Extraction Dataset (raw & filtered) | `outputs/train_split.parquet`, `outputs/test_split.parquet` | `contracts/dataset.schema.yaml` |
| Extraction Metadata | `outputs/extraction_meta.json` | (no schema enforced; simple JSON) |
| Power‑Analysis Output | `outputs/power_analysis.json` | `contracts/power_analysis.schema.yaml` |
| Training Log / Provenance | `outputs/training_log.json` | (no schema enforced) |
| Evaluation Results | `outputs/evaluation_results.json` | `contracts/evaluation.schema.yaml` |
| Sensitivity Report | `outputs/sensitivity_report.json` | `contracts/evaluation.schema.yaml` (subset) |
| Ablation Report | `outputs/ablation_report.json` | `contracts/evaluation.schema.yaml` (subset) |
| Evaluation Task List | `outputs/eval_tasks.json` | (no dedicated schema; simple list of task IDs) |

## Data Integrity Rules
- **Checksum Verification**: On every run, loaders compute SHA‑256 of raw files in `data/raw/` and compare to `data/checksums.json`. Mismatch → hard failure.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived artifacts receive new filenames under `outputs/`.  
- **No Synthetic Fallbacks**: Loaders raise `FileNotFoundError` if any required artifact is missing.  
- **PII Prohibition**: Schemas forbid fields that could contain personal identifiers.  

---

