# Data Model: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Overview

This document defines the data structures, schemas, and flow for the Dream-State Learning project. It ensures that all data artifacts are versioned, checksummed, and traceable to the code that produced them (Constitution Principle IV).

## Data Flow Diagram

1.  **Ingestion**: Raw datasets (GLUE/SuperGLUE) are downloaded via `datasets.load_dataset` and cached locally.
2.  **Preprocessing**: Text is tokenized; train/val/test splits are created.
3.  **Training (Wake)**: Real data batches are fed to the model; gradients are computed.
4.  **Training (Dream)**: Model generates pseudo-samples; tokens are masked; reconstruction loss is computed.
5.  **Evaluation**: Models are tested on held-out few-shot subsets.
6.  **Aggregation**: Results (accuracy, loss, time, memory) are aggregated into a final report.

## Core Entities

### 1. `TrainingRun`
Represents a single execution of the training loop (either Wake/Dream or Baseline).
- **Attributes**:
  - `run_id`: UUID (unique identifier).
  - `seed`: Integer (random seed).
  - `type`: Enum (`wake_dream`, `baseline`).
  - `config`: JSON (hyperparameters: temp, ratio, steps).
  - `start_time`: ISO8601 timestamp.
  - `end_time`: ISO8601 timestamp.
  - `peak_memory_gb`: Float (max RSS observed).
  - `status`: Enum (`success`, `oom_abort`, `timeout`).

### 2. `Checkpoint`
Saved model state at specific intervals.
- **Attributes**:
  - `checkpoint_id`: String (e.g., `run_id_step_100`).
  - `step`: Integer (training step).
  - `loss`: Float (current loss).
  - `path`: String (relative path to file).
  - `hash`: String (SHA-256 of file content).

### 3. `EvaluationResult`
Outcome of a few-shot evaluation.
- **Attributes**:
  - `run_id`: UUID (link to TrainingRun).
  - `task`: String (e.g., `mrpc`, `axb`).
  - `accuracy`: Float.
  - `samples`: Integer (number of test samples).
  - `effect_size`: Float (Cohen's d, if applicable).

### 4. `DreamEvent`
Log entry for a dream phase occurrence.
- **Attributes**:
  - `step`: Integer.
  - `entropy_mean`: Float (average entropy of generated tokens).
  - `retry_count`: Integer (number of retries due to low entropy).
  - `discarded`: Boolean (true if batch was discarded after max retries).

## File Formats

### Training Logs (`logs/training.log`)
JSON-lines format for easy parsing.
```json
{"timestamp": "2026-06-30T12:00:00Z", "level": "INFO", "run_id": "uuid-123", "phase": "wake", "step": 10, "loss": 0.45}
{"timestamp": "2026-06-30T12:00:05Z", "level": "INFO", "run_id": "uuid-123", "phase": "dream", "step": 11, "entropy_mean": 0.8, "retry_count": 0}
```

### Results CSV (`data/results.csv`)
Aggregated results for statistical analysis.
```csv
run_id,seed,type,task,accuracy,peak_memory_gb,wall_clock_seconds
uuid-1,0,wake_dream,mrpc,0.85,5.2,3600
uuid-2,0,baseline,mrpc,0.82,5.1,3550
```

## Data Hygiene Rules

1.  **Checksums**: Every file in `data/raw/` must have a corresponding `.sha256` file.
2.  **Immutability**: Raw data files are never modified. Derived data (e.g., tokenized splits) are written to `data/processed/` with new filenames.
3.  **PII Scan**: All text data is scanned for PII before processing. Any file containing PII is rejected and logged.