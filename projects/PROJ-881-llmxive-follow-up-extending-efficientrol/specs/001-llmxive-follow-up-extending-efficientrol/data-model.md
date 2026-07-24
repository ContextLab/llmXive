# Data Model: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Overview

This document defines the data structures used throughout the pipeline, from raw dataset ingestion to final analysis artifacts. All data is stored in JSONL or Parquet formats for efficient streaming and schema validation.

## Key Entities

### 1. TokenSequence
Represents a generated response to a prompt.
- **Fields**:
  - `sequence_id`: Unique identifier (UUID).
  - `task_type`: "GSM8K" or "MiniGrid".
  - `prompt`: The input text.
  - `tokens`: List of token IDs.
  - `validity_labels`: List of booleans (True if token matches ground truth).
  - `ground_truth`: The full ground truth string/sequence.
  - `sequence_length`: Integer length of the sequence.

### 2. EntropyProfile
Represents the internal state of a single token.
- **Fields**:
  - `sequence_id`: Foreign key to TokenSequence.
  - `token_index`: Position in the sequence.
  - `layer_entropies`: Dictionary mapping layer index (int) to entropy value (float).
  - `timestamp`: ISO 8601 timestamp of extraction.

### 3. ValidityLabel
A binary flag derived from the match between generated token and ground truth.
- **Fields**:
  - `sequence_id`: Foreign key.
  - `token_index`: Position.
  - `is_valid`: Boolean.
  - `match_type`: "exact" or "partial" (if applicable).

### 4. RegressionModel
The fitted statistical model.
- **Fields**:
  - `model_id`: Unique identifier.
  - `method`: "GLMM".
  - `coefficients`: Dictionary of fixed and random effects.
  - `metrics`: AUC-ROC, p-values, FDR.
  - `optimal_threshold`: The entropy value minimizing weighted error.

### 5. MemoryBackOffState
Represents the state of a memory back-off retry.
- **Fields**:
  - `original_batch_size`: Integer.
  - `retry_batch_size`: Integer (reduced).
  - `error_type`: "MemoryError".
  - `success`: Boolean.

## Data Flow

1.  **Raw Data**: `datasets.load_dataset()` -> `data/raw/gsm8k.parquet`, `data/raw/minari.parquet`.
2.  **Generated Data**: `generation.py` -> `data/processed/sequences.jsonl`.
3.  **Entropy Data**: `instrument.py` -> `data/processed/entropy_profiles.jsonl` (streamed, appended).
4.  **Merged Data**: `preprocessing.py` -> `data/processed/merged_analysis.parquet`.
5.  **Stratified Data**: `preprocessing.py` -> `data/processed/short_seqs.parquet`, `data/processed/long_seqs.parquet`.
6.  **Results**: `analysis/models.py` -> `artifacts/reports/model_results.json`.

## Schema Validation

All data files must conform to the schemas defined in `contracts/`. The `validators.py` module enforces these schemas at runtime. Memory back-off logic is handled by `preprocessing.py` and logged to `artifacts/logs/memory_backoff.json`, validated against `contracts/memory_backoff.schema.yaml`.
