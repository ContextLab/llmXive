# Data Model: Socratic Transformers (PROJ-582)

## Overview

This document defines the data schemas for the Socratic Transformers project. All data artifacts must conform to these schemas to ensure reproducibility and integrity.

## Raw Data

### GSM8K Test Set
- **Source**: `openai/gsm8k` (split: `test`)
- **Format**: Parquet
- **Fields**:
    - `question`: string (The math problem)
    - `answer`: string (The ground truth solution)

### MATH-500 Test Set
- **Source**: `HuggingFaceH4/MATH-500` (split: `test`)
- **Format**: JSONL
- **Fields**:
    - `problem`: string (The math problem)
    - `solution`: string (The ground truth solution)

## Processed Data (Generated Tuples)

### Static Tuples (Condition C)
- **File**: `data/processed/static.parquet`
- **Schema**:
    - `id`: string (Unique identifier)
    - `question`: string
    - `answer`: string
    - `source_dataset`: string ("gsm8k" or "math")

### Dialogue Tuples (Condition A - Selection)
- **File**: `data/processed/dialogue.parquet`
- **Schema**: **SSoT**: `dialogue_tuple.schema.yaml`
    - `sample_id`: string (Unique UUID)
    - `condition`: string ("socratic")
    - `question`: string
    - `initial_answer`: string (Model-generated)
    - `critique`: string (Adversarial critique identifying errors)
    - `revised_answer`: string (Model-generated revision)
    - `critique_quality_score`: float (0.0-1.0, from validation step)
    - `is_degenerate`: boolean
    - `is_verified`: boolean
    - `metadata`: object (seed, threshold, model_version)

### Ablation Tuples (Condition B - Neutral)
- **File**: `data/processed/ablation.parquet`
- **Schema**: **SSoT**: `dialogue_tuple.schema.yaml`
    - `sample_id`: string (Unique UUID)
    - `condition`: string ("ablation")
    - `question`: string
    - `initial_answer`: string
    - `critique`: string (Semantically coherent neutral text)
    - `revised_answer`: string
    - `critique_quality_score`: float (0.0-1.0)
    - `is_degenerate`: boolean
    - `is_verified`: boolean
    - `metadata`: object

## Results Data

### Evaluation Results
- **File**: `data/results.csv`
- **Schema**: **SSoT**: `evaluation_result.schema.yaml`
    - `run_id`: string (Unique UUID)
    - `condition`: string ("selection", "ablation", "static")
    - `seed`: int
    - `benchmark`: string ("gsm8k_test", "math_test")
    - `accuracy`: float
    - `total_samples`: int
    - `correct_samples`: int
    - `runtime_seconds`: float

### Statistical Analysis
- **File**: `data/analysis.json`
- **Schema**: **SSoT**: `stats_schema.schema.yaml`
    - `comparison`: string (e.g., "selection_vs_ablation")
    - `t_statistic`: float
    - `p_value`: float
    - `p_value_corrected`: float
    - `significant`: boolean (after Bonferroni correction)

## Data Hygiene Rules

1.  **Checksums**: All raw files in `data/raw/` must have a corresponding `.sha256` file.
2.  **Immutability**: Raw files are never modified. Derived files are written to new paths.
3.  **Validation**: `verify_datasets.py` must run before any training step to ensure schema compliance (Principle III).
4.  **PII**: No personally identifiable information is allowed. All data is synthetic or public benchmark data.