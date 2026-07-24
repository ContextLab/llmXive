# Data Model: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Entity Definitions

### 1. TokenSequence
Represents a generated response to a prompt.
- **prompt_id**: Unique identifier for the input prompt.
- **task_type**: Enum (`gsm8k`, `minigrid`).
- **tokens**: List of integer token IDs.
- **validity_flags**: List of booleans (True if token matches **external dataset ground truth**).
- **ground_truth**: The full external ground-truth string or token sequence from the dataset.

### 2. EntropyProfile
Represents the internal state of a single token at a specific layer.
- **prompt_id**: Foreign key to `TokenSequence`.
- **token_index**: Integer index of the token in the sequence.
- **layer_index**: Integer index of the transformer layer.
- **entropy_value**: Float ($-\sum p \log p$).
- **probability_distribution**: List of floats (optional, for debugging).

### 3. ValidityLabel
Binary flag indicating token correctness.
- **prompt_id**: Foreign key.
- **token_index**: Integer index.
- **is_valid**: Boolean (matches **external dataset ground truth**).

### 4. RegressionModel
Fitted statistical model results.
- **model_id**: Unique identifier.
- **task_type**: Enum.
- **fixed_effects**: Dict of coefficients (e.g., `{"entropy": 0.45}`).
- **random_effects_variance**: Dict of variance components (if GLMM).
- **clustered_se**: Float (if Clustered SE model).
- **auc_roc**: Float.
- **p_value**: Float.
- **fdr_corrected**: Boolean.

## Data Flow

1.  **Ingestion**: Raw datasets (GSM8K, MiniGrid) downloaded to `data/raw/`.
2.  **Generation**: `generation.py` produces `TokenSequence` with `validity_flags` (matched against **external dataset ground truth**).
3.  **Instrumentation**: `entropy_calc.py` extracts `EntropyProfile` for each token. Input: raw logits. Output: entropy values (softmax applied internally, probabilities clamped to $1e-9$).
4.  **Merging**: `preprocessing.py` merges `TokenSequence` and `EntropyProfile` into `data/processed/merged_data.parquet`. **Merge Key**: `prompt_id` and `token_index` (Inner Join).
5.  **Analysis**: `glmm_fit.py` reads merged data, fits GLMM (or Clustered SE fallback), outputs `RegressionModel` metrics to `data/processed/results.json`.

## Constraints & Validation

- **Entropy Calculation**: Must handle $p=0$ by clamping to $1e-9$ before log. Input is raw logits; softmax is applied internally.
- **Batching**: All processing must occur in batches of 50 tokens to respect 7GB RAM.
- **Uniqueness**: `prompt_id` + `token_index` + `layer_index` must be unique.
- **Missing Data**: Any missing entropy values result in row exclusion with a log warning.
- **Schema Adherence**: All data files must adhere to `dataset.schema.yaml`, `entropy_profile.schema.yaml`, and `analysis_result.schema.yaml`.
- **Validity Label Return**: The validity labeling function must return a structured record containing the original data, the validity flag, and a standardized log entry object (if applicable).
