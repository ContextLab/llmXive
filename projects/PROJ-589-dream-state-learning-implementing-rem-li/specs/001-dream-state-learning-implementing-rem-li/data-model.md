# Data Model: Dream-State Learning

## Overview
Defines all persistent artifacts produced by the experiment, each validated against a JSON Schema in `contracts/`. All files are immutable once written; new derivations receive fresh filenames and corresponding hashes.

## Data Flow
1. **Raw Ingestion** – GLUE parquet files (`data/raw/`) fetched via `datasets.load_dataset`.  
2. **Pre‑processing** – No modification of raw files; masked pseudo‑samples generated on‑the‑fly during training and logged to `data/processed/dream_samples/`.  
3. **Training Artifacts** – Checkpoints (`checkpoints/`) and per‑step logs (`logs/`).  
4. **Evaluation Results** – JSON files under `data/results/` adhering to `evaluation_result.schema.yaml`.  
5. **Aggregated Experiment Summary** – `data/results/experiment_summary.json` adhering to `experiment_result_schema.schema.yaml` and `statistical_report_schema.yaml`.  
6. **Versioning** – SHA‑256 hashes recorded in `state/projects/PROJ-589-dream-state-learning-implementing-rem-li/artifact_hashes.yaml` using `artifact_hashes.schema.yaml`.

## Schemas (see `contracts/`)

| Schema File | Purpose |
|-------------|---------|
| `dataset.schema.yaml` | Raw GLUE record (id, text, label, split). |
| `dream_sample_schema.schema.yaml` | Pseudo‑sample generated during a dream step (entropy, perplexity, masking). |
| `dream_event.schema.yaml` | Diagnostics of each dream‑step execution (entropy, retries, discard flag). |
| `training_config.schema.yaml` | Hyper‑parameter configuration for a run. |
| `training_result.schema.yaml` | Aggregated run metrics (accuracy, memory, wall‑clock, status). |
| `evaluation_result.schema.yaml` | Single evaluation run output (accuracy, loss, resource usage). |
| `experiment_result_schema.schema.yaml` | Summary per seed & regime (final accuracy, steps, memory). |
| `statistical_report_schema.yaml` | Paired t‑test outcome, effect size, power estimate, notes. |
| `artifact_hashes.schema.yaml` | Content‑hash tracking for reproducibility. |

## Data Hygiene Rules
1. **Immutability** – Raw files never overwritten; derived files receive new names (`*_v{hash}.json`).  
2. **Checksums** – Every file in `data/raw/` has a `.sha256` side‑car; verification occurs at start of each CI run.  
3. **PII** – GLUE is pre‑scrubbed; no additional PII may be introduced.  
4. **Logging** – All wake/dream transitions, entropy, reconstruction error, and memory metrics logged in structured JSON (`logs/`).  
5. **Schema Validation** – `tests/contract/` runs `jsonschema` validation on every artifact before the next pipeline stage.  
6. **Versioning** – After each artifact is written, its SHA‑256 is recorded in `state/projects/PROJ-589-dream-state-learning-implementing-rem-li/artifact_hashes.yaml` using `artifact_hashes.schema.yaml`.  

## Single Source of Truth (SSoT) Mapping
- **Metrics** (accuracy, loss, peak memory, reconstruction error) → `data/results/experiment_summary.json`.  
- **Figures** (training loss curves, reconstruction error vs. accuracy scatter) → `docs/figures/` (generated from the JSON source).  
- **Logs** → `logs/` (referenced by the JSON summary for reproducibility).

---

