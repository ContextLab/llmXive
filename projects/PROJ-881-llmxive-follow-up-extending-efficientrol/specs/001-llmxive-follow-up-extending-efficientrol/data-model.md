# Data Model: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Overview
This document defines the data structures used to store and process the intermediate states, ground truth labels, and analysis results. The model is designed to be streaming-friendly (to handle memory constraints) and schema-strict (for reproducibility). The key change is the **single-pass** capture of entropy and validity, and the support for **Mixed-Effects Logistic Regression** (GLMM) in the analysis result structure.

## Entity Definitions

### 1. TokenSequence
Represents a single generated response to a prompt.
*   **id**: Unique identifier (UUID).
*   **task_type**: Enum (`gsm8k`, `minigrid`).
*   **prompt**: The input text.
*   **ground_truth**: The expected solution string or action sequence (external source).
*   **generated_tokens**: List of token IDs or strings.
*   **validity_flags**: List of booleans (1/0) corresponding to each token (derived from external ground truth).
*   **sequence_length**: Integer.

### 2. EntropyProfile
Represents the internal state of a single token across all transformer layers.
*   **sequence_id**: Foreign key to `TokenSequence`.
*   **token_index**: Integer (position in sequence).
*   **token_id**: Integer (Vocab ID).
*   **entropy_values**: List of floats (one per layer).
*   **is_valid**: Boolean (derived from external ground truth, not model output).

### 3. RegressionResult
Stores the output of the Mixed-Effects Logistic Regression (GLMM) analysis.
*   **task_type**: Enum.
*   **layer_group**: String (`early`, `mid`, `late`, `all`, or specific layer index).
*   **coefficient**: Float ($\beta_1$).
*   **p_value**: Float (raw).
*   **p_value_corrected**: Float (FDR/Bonferroni corrected).
*   **auc_roc**: Float.
*   **optimal_threshold**: Float.
*   **fpr_at_threshold**: Float.
*   **fnr_at_threshold**: Float.
*   **random_effect_variance**: Float (variance of the random intercept for `sequence_id`).

### 4. SensitivityAnalysis
Stores the results of the threshold sweep.
*   **task_type**: Enum.
*   **threshold**: Float.
*   **accuracy**: Float.
*   **fpr**: Float.
*   **fnr**: Float.
*   **computation_saved_ratio**: Float (estimated based on skipped layers).

## Data Flow
1.  **Single-Pass Generation**: `TokenSequence` and `EntropyProfile` generated simultaneously and written to `data/raw/sequences.jsonl` (with embedded entropy) or separate linked files.
2.  **Analysis**: `RegressionResult` and `SensitivityAnalysis` computed and stored in `data/results/analysis_results.jsonl`.

## Constraints
*   **Sequence Length**: Max tokens within a reasonable limit appropriate for the task.
*   **Batch Size**: Processing batches limited to a size constrained by available RAM.
*   **Data Integrity**: No in-place updates; all derivations append to new files.