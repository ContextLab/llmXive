# Data Model: llmXive Follow-up: Input Noise Injection for Latent Separability

## 1. Overview

This document defines the data structures for the experiment, ensuring traceability from raw inputs to statistical results. All data is stored in CSV/JSONL formats for interoperability and checksumming.

## 2. Data Flow

1. **Raw Input**: BigBench JSON/Parquet files (downloaded).
2. **Pairs**: Logical grouping of questions by task type (generated dynamically).
3. **Baseline Vectors**: Latent vectors extracted from unperturbed inputs.
4. **Perturbed Vectors**: Latent vectors extracted from noisy inputs (per $\sigma$).
5. **Validity Logs**: Pass/fail status for each pair at each $\sigma$.
6. **Results**: Aggregated statistical metrics.

## 3. Entity Definitions

### 3.1. QuestionPair
A unique identifier for two distinct questions from the same task type.
- `pair_id`: Unique string (e.g., `task_causal_001`).
- `task_type`: String (e.g., `causal_judgement`).
- `question_a`: String (text).
- `question_b`: String (text).
- `expected_answer_a`: String (ground truth).
- `expected_answer_b`: String (ground truth).

### 3.2. LatentVector
The hidden state vector extracted at the "thought" token.
- `pair_id`: Link to QuestionPair.
- `condition`: "baseline" or "perturbed".
- `sigma`: Float (noise level, 0.00 for baseline).
- `vector`: List of floats (normalized to unit length).
- `token_index`: Integer (index of the "thought" token).

### 3.3. ValidityRecord
Result of validity checks for a pair at a specific $\sigma$.
- `pair_id`: Link to QuestionPair.
- `sigma`: Float.
- `input_drift_score`: Float (SBERT cosine similarity).
- `output_bertscore`: Float.
- `output_perplexity_ratio`: Float.
- `exact_match`: Boolean.
- `is_valid`: Boolean (True if all checks pass).

### 3.4. StatisticalResult
Aggregated results for a task type and $\sigma$.
- `task_type`: String.
- `sigma`: Float.
- `n_baseline`: Integer.
- `n_perturbed`: Integer.
- `n_valid`: Integer (pairs passing validity).
- `mean_similarity_baseline`: Float.
- `mean_similarity_perturbed`: Float.
- `difference`: Float.
- `test_type`: "t-test" or "wilcoxon".
- `p_value`: Float.
- `p_value_corrected`: Float.
- `effect_size`: Float.
- `significance`: "significant" or "not_significant".

## 4. File Specifications

### 4.1. `data/processed/pairs.csv`
- **Format**: CSV
- **Columns**: `pair_id`, `task_type`, `question_a`, `question_b`, `expected_answer_a`, `expected_answer_b`.
- **Checksum**: SHA256 stored in `data/checksums.json`.

### 4.2. `data/processed/latent_vectors.csv`
- **Format**: CSV (with `vector` column as JSON string or separate columns if fixed size).
- **Columns**: `pair_id`, `condition`, `sigma`, `token_index`, `vector_json`.
- **Note**: `vector_json` contains the list of floats.

### 4.3. `data/processed/validity_log.csv`
- **Format**: CSV
- **Columns**: `pair_id`, `sigma`, `input_drift_score`, `output_bertscore`, `output_perplexity_ratio`, `is_valid`.

### 4.4. `data/results/statistical_summary.csv`
- **Format**: CSV
- **Columns**: `task_type`, `sigma`, `n_valid`, `mean_diff`, `p_value`, `p_value_corrected`, `significance`.

## 5. Constraints & Validation

- **Vector Normalization**: All latent vectors MUST be normalized to unit length ($\|v\|_2 = 1$) before storage.
- **Float Precision**: All floats stored with 6 decimal places.
- **Missing Data**: If a pair fails validity, it is excluded from `latent_vectors` for that $\sigma$ and marked in `validity_log`.
- **Consistency**: `pair_id` must be unique across all files.
