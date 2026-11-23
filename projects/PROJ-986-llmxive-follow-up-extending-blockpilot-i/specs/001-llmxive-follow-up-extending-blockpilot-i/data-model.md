# Data Model: llmXive follow-up: extending "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec"

## 1. Entity Definitions

### Sample
A single text instance from a dataset (GSM8K, HumanEval, Dolly-15k) paired with the derived ground-truth optimal block size ($B^*$).

**Fields**:
- `sample_id`: Unique identifier (string)
- `prompt`: Text input (string)
- `domain`: Dataset source (enum: "math", "code", "natural_language")
- `architecture`: Model used for sweep (enum: "qwen3-4b", "llama3-8b")

### FeatureVector
Numeric vector derived from the prefilling phase.

**Fields**:
- `sample_id`: Unique identifier (string)
- `prompt_length`: Integer (number of tokens)
- `mean_attention_entropy`: Float (mean over layers)
- `hidden_state_norm`: Float (L2 norm of final token)
- `vif_scores`: Dict (feature name -> VIF score) - *Optional, for diagnostic*
- `is_decorrelated`: Boolean - *True if VIF > 5 and features were transformed*

### GroundTruth
Result of the exhaustive sweep.

**Fields**:
- `sample_id`: Reference to Sample
- `block_sizes`: List of integers (tested block sizes)
- `acceptance_lengths`: List of floats (acceptance length for each block size)
- `B_star`: Integer (optimal block size)
- `tie_breaker`: String (rule applied if tie)
- `perplexity`: Float (Independent measure of model uncertainty, calculated via a separate greedy pass)

### Prediction
Output of the policy model.

**Fields**:
- `sample_id`: Reference to Sample
- `predicted_B`: Integer (predicted optimal block size)
- `actual_B`: Integer (ground truth $B^*$)
- `accuracy`: Boolean (predicted == actual)
- `model_type`: String (XGBoost, Random Forest, Decision Tree)
- `architecture`: Model used for evaluation
- `domain`: Domain of the sample

### ModelArtifact
Trained policy model.

**Fields**:
- `model_id`: Unique identifier
- `model_type`: String
- `training_domain`: String
- `training_architecture`: String
- `feature_importance`: Dict (feature name → importance score)
- `accuracy_train`: Float
- `accuracy_test`: Float
- `generalization_gap`: Float (test accuracy on divergent domain)
- `vif_threshold`: Float (Threshold used for decorrelation)

## 2. Relationships

- **Sample** → **FeatureVector**: 1:1 (one feature vector per sample)
- **Sample** → **GroundTruth**: 1:1 (one ground truth per sample)
- **FeatureVector** + **GroundTruth** → **Prediction**: 1:N (one prediction per model type)
- **ModelArtifact** → **Prediction**: 1:N (one model generates many predictions)

## 3. Data Flow

1. **Ingest**: Stream `Sample` from dataset.
2. **Sweep**: Generate `GroundTruth` via exhaustive block-size evaluation.
3. **Extract**: Derive `FeatureVector` from prefilling pass.
4. **Collinearity Check**: Calculate VIF. If VIF > 5, apply decorrelation (residualization/PCA) and mark `is_decorrelated=True`.
5. **Train**: Fit `ModelArtifact` on (FeatureVector, GroundTruth.B_star) using **Classification** algorithms.
6. **Evaluate**: Generate `Prediction` on held-out data (including cross-architecture tests).
7. **Aggregate**: Compute metrics (Accuracy, F1, generalization gap, perplexity correlation).

## 4. Storage Strategy

- **Raw Data**: Streamed from HF; not stored permanently.
- **Processed Data**: `data/processed/` (FeatureVector, GroundTruth, Prediction).
- **Models**: `data/models/` (pickle or joblib format).
- **Logs**: `data/logs/` (sweep progress, warnings, errors).

## 5. Data Hygiene

- **Checksums**: Recorded in `state/` for all processed files.
- **Immutability**: Raw data never modified; derivations written to new files.
- **PII**: No PII expected in GSM8K/HumanEval/Dolly-15k; scan enabled for safety.