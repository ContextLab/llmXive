# Data Model: llmXive follow-up: extending "DelTA"

## Overview

This document defines the data schemas for the project's artifacts. All data is stored in `data/` and validated against the contracts in `contracts/`.

## Entity Definitions

### 1. Raw Dataset (GSM8K Verified)
*   **Source**: HuggingFace `openai/gsm8k` (filtered).
*   **Format**: Parquet.
*   **Location**: `data/raw/gsm8k_verified.parquet`
*   **Schema**:
    *   `id`: string (unique identifier)
    *   `question`: string (the math problem)
    *   `answer`: string (the solution trace)
    *   `solution_length`: integer (number of tokens in solution)
    *   `verified`: boolean (must be True)

### 2. Oracle Output (DelTA Coefficients)
*   **Source**: `generate_oracle.py` (DelTA backprop on Llama-3 model).
*   **Format**: JSON.
*   **Location**: `data/processed/delta_coefficients.json`
*   **Structure**: List of objects, one per example.
    *   `example_id`: string
    *   `model_used`: string (e.g., "Llama-3-8B" or "Llama-3-1B")
    *   `tokens`: List of objects
        *   `token_id`: integer
        *   `token_text`: string
        *   `delta_coefficient`: float (the ground truth value)

### 3. Static Features
*   **Source**: `extract_features.py`.
*   **Format**: Parquet.
*   **Location**: `data/processed/static_features.parquet`
*   **Schema**:
    *   `example_id`: string
    *   `token_id`: integer
    *   `ngram_1_count`: float (normalized count of 1-grams in window)
    *   `ngram_2_count`: float (normalized count of 2-grams in window)
    *   `ngram_3_count`: float (normalized count of 3-grams in window)
    *   `pos_tag`: string (one-hot encoded in vector)
    *   `semantic_similarity`: float (cosine similarity to reference set using MiniLM)
    *   `feature_vector`: List[float] (dense vector for model input)

### 4. Model Predictions
*   **Source**: `predict.py`.
*   **Format**: JSON.
*   **Location**: `data/processed/predictions.json`
*   **Structure**:
    *   `example_id`: string
    *   `predictions`: List of objects
        *   `token_id`: integer
        *   `predicted_delta`: float
        *   `true_delta`: float (for evaluation)

### 5. Metrics Report
*   **Source**: `eval/metrics.py`.
*   **Format**: JSON.
*   **Location**: `data/processed/metrics_report.json`
*   **Schema**:
    *   `spearman_correlation`: float
    *   `p_value`: float
    *   `feature_importance`: Dict (feature_name -> score)
    *   `result_classification`: string ("signal_predictable" | "signal_emergent" | "poor_proxies")

## Data Flow

1.  `gsm8k_verified.parquet` -> `generate_oracle.py` -> `delta_coefficients.json`
2.  `gsm8k_verified.parquet` -> `extract_features.py` -> `static_features.parquet`
3.  `static_features.parquet` + `mlp_model.pt` -> `predict.py` -> `predictions.json`
4.  `predictions.json` -> `metrics.py` -> `metrics_report.json`

## Constraints

*   **No NaNs**: All float fields must be valid numbers.
*   **Variance Check**: The `delta_coefficient` column must have variance > 1e-9 (Runtime check, not schema constraint).
*   **Completeness**: Every token in the input must have a corresponding coefficient and feature vector.
