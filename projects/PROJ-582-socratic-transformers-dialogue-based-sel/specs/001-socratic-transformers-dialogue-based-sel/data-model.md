# Data Model: Socratic Transformers

## Overview

This document defines the data schemas for the Socratic Transformers project. All data artifacts must conform to these schemas to ensure reproducibility and contract validation.

## Artifact Flow

1. **Raw Data**: Downloaded from HuggingFace (GSM8K, MATH).
2. **Generated Dialogue**: Produced by the Critic and Generator models.
3. **Training Data**: Aggregated datasets for the three conditions.
4. **Evaluation Results**: Accuracy metrics and statistical test outputs.

## Schemas

### 1. Raw Dataset Schema (GSM8K/MATH)

**Source**: `data/raw/gsm8k.parquet`, `data/raw/math.parquet`

| Field | Type | Description |
|-------|------|-------------|
| `question` | string | The original problem statement. |
| `answer` | string | The ground truth solution (or `solution` for MATH). |
| `id` | string | Unique identifier for the sample. |

### 2. Dialogue Tuple Schema (Generated)

**Source**: `data/derived/dialogues.parquet`

| Field | Type | Description |
|-------|------|-------------|
| `question` | string | Original question. |
| `initial_answer` | string | Model's first attempt (potentially erroneous). |
| `critique` | string | Adversarial critique identifying errors. |
| `revised_answer` | string | Model's revised answer after critique. |
| `condition` | string | "selection" (adversarial) or "ablation" (neutral placeholder). |
| `quality_passed` | boolean | True if passed the regeneration loop quality gate. |
| `retry_count` | integer | Number of regeneration attempts (0 if passed first try). |

### 3. Evaluation Result Schema

**Source**: `data/results/metrics.csv`

| Field | Type | Description |
|-------|------|-------------|
| `condition` | string | "selection", "ablation", or "static". |
| `dataset` | string | "gsm8k" or "math". |
| `accuracy` | float | Proportion of correct answers. |
| `n_samples` | integer | Number of samples evaluated. |
| `std_err` | float | Standard error of the mean. |

### 4. Statistical Test Output Schema

**Source**: `data/results/stats.json`

| Field | Type | Description |
|-------|------|-------------|
| `comparison` | string | e.g., "selection_vs_ablation". |
| `t_statistic` | float | T-statistic value. |
| `p_value` | float | Raw p-value. |
| `p_value_corrected` | float | Bonferroni-corrected p-value. |
| `significant` | boolean | True if `p_value_corrected` < 0.05. |

## Data Hygiene Rules

- **Checksums**: All files in `data/raw/` and `data/derived/` must be checksummed (SHA-256) and recorded in `state/artifact_hashes.yaml`.
- **Immutability**: Raw data is never modified. Derived data is written to new files with versioned names.
- **PII**: No Personally Identifiable Information is allowed. Datasets are public and anonymized by nature.
