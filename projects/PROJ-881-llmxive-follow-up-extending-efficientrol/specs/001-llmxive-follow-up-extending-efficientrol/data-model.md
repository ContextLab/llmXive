# Data Model: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Entities & Relationships

### 1. TokenSequence
Represents a generated response to a prompt.
- **Attributes**:
  - `sequence_id`: Unique identifier (UUID).
  - `task_type`: "gsm8k" or "minigrid".
  - `prompt_id`: Reference to the input prompt.
  - `tokens`: List of token IDs.
  - `ground_truth`: The reference solution string/sequence.
  - `validity_labels`: List of booleans (0/1) corresponding to each token.
- **Relationship**: One `TokenSequence` contains many `EntropyProfile` entries.

### 2. TokenAlignment
Represents the mapping between generated tokens and ground truth.
- **Attributes**:
  - `alignment_id`: Unique identifier.
  - `sequence_id`: Foreign key to `TokenSequence`.
  - `token_index`: Position in the sequence.
  - `alignment_status`: "match", "mismatch", "divergence".
  - `validity_label`: Derived from alignment status (1 for match, 0 for mismatch/divergence).
- **Relationship**: One `TokenAlignment` belongs to one `TokenSequence`.

### 3. EntropyProfile
Represents the internal state of a single token at a specific layer.
- **Attributes**:
  - `profile_id`: Unique identifier.
  - `sequence_id`: Foreign key to `TokenSequence`.
  - `token_index`: Position in the sequence (0-indexed).
  - `layer_id`: Transformer layer index (0 to N).
  - `entropy_value`: Calculated Shannon entropy (float).
  - `validity_label`: Inherited from `TokenSequence` (denormalized for analysis).
- **Relationship**: One `EntropyProfile` belongs to one `TokenSequence`.

### 4. RegressionModel
Stores the results of the statistical analysis.
- **Attributes**:
  - `model_id`: Unique identifier.
  - `task_type`: "gsm8k", "minigrid", or "pooled".
  - `coefficients`: JSON object mapping predictors to coefficients.
  - `intercept`: Float.
  - `auc_roc`: Float (0.0 to 1.0).
  - `p_values`: JSON object mapping predictors to p-values.
  - `fdr_corrected_p_values`: JSON object.
  - `optimal_threshold`: Float.
  - `fpr`: Float.
  - `fnr`: Float.
  - `random_effect_variance`: Float (variance of random intercept).

## Data Flow

1. **Raw Data**: Downloaded Parquet/HDF5 files -> `data/raw/`.
2. **Processed Data**:
   - `data/processed/ground_truth_labels.jsonl`: Token-level validity (via Semantic Alignment).
   - `data/processed/entropy_profiles.jsonl`: Layer-level entropy (via single-sequence streaming).
   - `data/processed/merged_analysis.jsonl`: Joined data for regression.
3. **Results**:
   - `data/results/regression_results.json`: Model coefficients and metrics.
   - `data/results/sensitivity_analysis.json`: Threshold sweep results.
   - `data/results/fdr_report.json`: Corrected p-values.
   - `data/results/decay_analysis.json`: Stratified results by sequence length.

## Storage Strategy

- **Format**: JSONL for intermediate data (streaming-friendly), JSON for final results.
- **Checksums**: All files in `data/raw/` and `data/processed/` are checksummed (SHA-256) and recorded in `state/...yaml`.
- **Versioning**: Derived files include `derived_from` metadata pointing to the source file hash.