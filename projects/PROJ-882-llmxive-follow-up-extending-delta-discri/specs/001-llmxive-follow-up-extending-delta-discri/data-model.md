# Data Model: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Overview

This document defines the schema and structure of data artifacts generated and consumed by the pipeline. All data is stored in `data/` directory, with raw data in `data/raw` and processed artifacts in `data/processed`.

## Data Flow

1.  **Input**: GSM8K dataset (Parquet) from HuggingFace.
2.  **Step 1 (Oracle)**: Generate `delta_coefficients.json` (Token-level scores).
3.  **Step 2 (Features)**: Generate `static_features.parquet` (Token-level features).
4.  **Step 3 (Model)**: Train `mlp_model.pt` (PyTorch weights).
5.  **Step 4 (Eval)**: Generate `predictions.json` (Predicted scores + metrics).

## Artifact Definitions

### 1. Raw Data: `data/raw/gsm8k_verified.parquet`
- **Source**: `openai/gsm8k` (HuggingFace).
- **Filter**: `correctness == True`.
- **Schema**:
  - `question`: string
  - `answer`: string
  - `solution`: string (step-by-step reasoning)
  - `id`: string (unique identifier)
  - `solution_length`: integer (character or token count)

### 2. Oracle Output: `data/processed/delta_coefficients.json`
- **Description**: Ground-truth DelTA coefficients for every token in the solution.
- **Format**: JSON Lines (`.jsonl`) or nested JSON.
- **Schema**:
  - `example_id`: string
  - `tokens`: array of objects
    - `token_id`: integer
    - `token_text`: string
    - `delta_coefficient`: float (ground truth)
  - `metadata`: object (model version, seed, variance check result)

### 3. Static Features: `data/processed/static_features.parquet`
- **Description**: Feature vectors for each token, derived from static input.
- **Format**: Parquet (columnar for efficient loading).
- **Schema**:
  - `example_id`: string
  - `token_id`: integer
  - `ngram_features`: array of floats (e.g., [count_unigram, count_bigram, ...])
  - `pos_features`: array of integers (one-hot or embedding of POS tags)
  - `semantic_similarity`: float (cosine similarity to OpenMathInstruct-1 patterns)
  - `context_window`: string (±2 tokens context)
  - `delta_coefficient`: float (target variable, copied from oracle)

### 4. Model Weights: `data/processed/mlp_model.pt`
- **Description**: Trained PyTorch state dict.
- **Format**: Binary `.pt` file.
- **Contents**: `state_dict` of the 2-layer MLP.

### 5. Predictions & Metrics: `data/processed/predictions.json`
- **Description**: Model predictions and evaluation metrics.
- **Schema**:
  - `predictions`: array of objects
    - `example_id`: string
    - `token_id`: integer
    - `true_coefficient`: float
    - `predicted_coefficient`: float
  - `metrics`: object
    - `spearman_correlation`: float
    - `p_value`: float (from example-level permutation test)
    - `feature_importance`: object (map of feature names to importance scores)
    - `classification`: string ('signal is emergent' or 'features are poor proxies')
    - `random_baseline_spearman`: float
    - `uniform_baseline_spearman`: float

## Data Hygiene & Checksums

- **Checksumming**: All files in `data/processed` will be checksummed (SHA-256) and recorded in the project state file.
- **Immutability**: Raw data is never modified. Derived data is written to new files.
- **PII**: No personally identifiable information is expected in GSM8K/OpenMathInstruct-1.
