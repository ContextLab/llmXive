# Data Model: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Overview

This document defines the data structures, schemas, and relationships for the DelTA static approximation pipeline. All data is stored in Parquet (tabular) or JSON (nested/variable length) formats.

## Entity Definitions

### 1. GSM8K Raw Record
The base unit of data from the GSM8K dataset.
- **Source**: `openai/gsm8k` (train split)
- **Format**: Parquet
- **Fields**:
  - `question`: String. The math problem.
  - `answer`: String. The ground truth solution.
  - `example_id`: Integer. Unique identifier (derived from index).
  - `solution_length`: Integer. Number of tokens in the solution (computed).

### 2. Oracle DelTA Coefficient (Flat)
The ground-truth discriminative weight for each token position.
- **Source**: `generate_oracle.py` (Llama-3-1B backprop)
- **Format**: JSON (Flat list of objects)
- **Schema**: `contracts/delta_oracle.schema.yaml`
- **Fields**:
  - `example_id`: Integer. Links to GSM8K record.
  - `token_index`: Integer. Position of the token in the prompt.
  - `token_text`: String. The token string.
  - `delta_coefficient`: Float. The computed DelTA weight.
  - `computation_status`: String. "success" or "failed" (if gradient computation failed).

### 3. Upper Bound Predictions
Predictions from the control model using hidden states.
- **Source**: `generate_upper_bound.py`
- **Format**: JSON
- **Fields**:
  - `example_id`: Integer.
  - `token_index`: Integer.
  - `predicted_coefficient`: Float.
  - `true_coefficient`: Float.

### 4. Static Feature Vector
The input features for the regression model.
- **Source**: `extract_features.py` (MiniLM, spaCy)
- **Format**: Parquet
- **Fields**:
  - `example_id`: Integer.
  - `token_index`: Integer.
  - `ngram_features`: Array[Float]. Flattened n-gram statistics.
  - `pos_features`: Array[Int]. Encoded POS tags.
  - `semantic_similarity`: Float. Cosine similarity to reference patterns.
  - `feature_vector`: Array[Float]. Concatenation of all features (used for training).
  - `delta_coefficient`: Float. Target variable (from Oracle).

### 5. Model Prediction (Static)
Output of the trained Static MLP.
- **Source**: `predict.py`
- **Format**: JSON
- **Fields**:
  - `example_id`: Integer.
  - `token_index`: Integer.
  - `predicted_coefficient`: Float.
  - `true_coefficient`: Float.
  - `error`: Float. Absolute difference.

### 6. Evaluation Metrics
Final results of the pipeline.
- **Source**: `metrics.py`
- **Format**: JSON
- **Fields**:
  - `spearman_correlation`: Float.
  - `kendall_tau`: Float.
  - `spearman_ci_lower`: Float.
  - `spearman_ci_upper`: Float.
  - `p_value`: Float.
  - `upper_bound_spearman`: Float.
  - `upper_bound_ci_lower`: Float.
  - `upper_bound_ci_upper`: Float.
  - `classification`: String. "emergent", "poor_proxies", or "significant".
  - `causal_disclaimer`: String. "Findings are associational only."

## Data Flow

1. **Download**: `GSM8K Raw Record` -> `data/raw/gsm8k_verified.parquet`
2. **Oracle**: `GSM8K Raw Record` -> `data/processed/delta_coefficients.json` (Flat, `delta_oracle.schema.yaml`)
3. **Upper Bound**: `GSM8K Raw Record` + `hidden_states` -> `data/processed/upper_bound_predictions.json`
4. **Features**: `GSM8K Raw Record` + `delta_coefficients.json` -> `data/processed/static_features.parquet`
5. **Train**: `static_features.parquet` -> `data/processed/mlp_model_static.pt`
6. **Predict**: `static_features.parquet` + `mlp_model_static.pt` -> `data/processed/predictions.json`
7. **Eval**: `predictions.json` + `upper_bound_predictions.json` -> `data/processed/metrics.json`

## Constraints & Validation

- **Variance Check**: Oracle coefficients must have variance > 1e-9.
- **Completeness**: Every token in the prompt must have a corresponding feature vector and coefficient.
- **No Leakage**: `feature_vector` (Static Model) must not contain any data from the Llama-3-1B hidden states.
- **Permutation Unit**: Permutation tests must shuffle at the **example** level, not token level.
