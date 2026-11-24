# Data Model: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Overview
All project artifacts reside under `data/`. Schemas in `contracts/` validate each artifact. Files are immutable after creation; new derivations receive new filenames.

## Entity Schemas

| Entity | File Pattern | Schema |
|--------|--------------|--------|
| Prompt Metadata | `data/processed/prompts.csv` | `contracts/prompt_schema.schema.yaml` |
| Semantic Entropy Scores | `data/processed/entropy_scores.csv` | `contracts/entropy_schema.schema.yaml` |
| Activation Variance Record | `data/processed/activation_stats/*.json` | `contracts/activation_schema.schema.yaml` |
| Rotation Matrix Definition | `data/processed/rotation_matrices/matrix_{i}.npy` + `data/processed/rotation_matrices/metadata_{i}.json` | `contracts/rotation_matrix_schema.schema.yaml` |
| Evaluation Result | `data/processed/results.csv` | `contracts/results_schema.schema.yaml` |
| Clustering Report (router lookup) | `data/processed/clustering_report.json` | `contracts/clustering_report_schema.schema.yaml` |
| Logs | `data/processed/logs/*.json` | (no schema – free‑form logs) |

## Storage Formats
- **CSV**: Human‑readable tables (`prompts.csv`, `entropy_scores.csv`, `results.csv`).  
- **JSON**: Metadata, variance records, clustering report, logs.  
- **NumPy (`.npy`)**: Rotation matrices (dense float32 tensors).  

## Data Hygiene Rules
1. **Immutability** – Raw MS‑COCO parquet files under `data/raw/` never overwritten.  
2. **Checksums** – SHA‑256 of every raw and processed file recorded in `data/checksums.json`.  
3. **Versioning** – After each pipeline run, `data/artifact_hashes.json` is updated with hashes of all new artifacts (project‑owned).  
4. **PII** – Captions contain no personal identifiers; a simple regex filter removes any token matching email/phone patterns.  

## Validation Steps (new)
- **Prompt & Entropy CSV Validation**: Before any analysis, `code/analysis/correlation.py` validates `prompts.csv` and `entropy_scores.csv` against `prompt_schema.schema.yaml` and `entropy_schema.schema.yaml` using `jsonschema`. Failures abort the pipeline.  
- **Rotation Matrix Metadata Validation**: After matrix generation, `code/analysis/clustering.py` validates each `metadata_{i}.json` against `rotation_matrix_schema.schema.yaml`. Invalid metadata triggers a re‑run of the clustering step.