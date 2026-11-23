# Data Model: llmXive follow-up: extending "Cosmos 3: Omnimodal World Models for Physical AI"

## 1. Overview

This document defines the data structures, schemas, and relationships for the Cosmos 3 gap analysis pipeline. It ensures that data flows correctly from raw ingestion to symbolic transformation, model training, and error analysis.

## 2. Entity Definitions

### 2.1 Cosmos3_Sample (Raw)
Represents a single instance from the **Bridge** dataset.
- **Fields**:
  - `sample_id`: Unique identifier (string).
  - `text_description`: Natural language description of the scene (string).
  - `video_frames`: List of image paths or base64 encoded frames (list).
  - `action_vector`: Continuous action vector (list of floats, length >= 3, e.g., `[x, y, z]`).
  - `physics_reward`: Ground truth reward from the physics engine (float).

### 2.2 Symbolic_Label (Derived)
The discrete token assigned to a sample based on composite logical rules.
- **Fields**:
  - `sample_id`: Reference to `Cosmos3_Sample`.
  - `symbolic_label`: Enum [`"constraint_satisfied"`, `"constraint_violated"`].
  - `rule_applied`: String describing the rule used (e.g., "L2 norm of first 3 dims > 0.5 AND context match").
  - `vector_norm`: The calculated L2 norm of the first 3 dimensions (float).
  - `context_match`: Boolean indicating if the text description matched safety keywords.
  - `safety_constraint`: Boolean indicating if the composite safety constraint was violated.

### 2.3 Physics_Label (Derived)
The discrete token assigned to a sample based on physics reward.
- **Fields**:
  - `sample_id`: Reference to `Cosmos3_Sample`.
  - `physics_label`: Enum [`"success"`, `"failure"`].
  - `rule_applied`: String describing the rule used (e.g., "physics_reward > 0.5").
  - `physics_reward_value`: The original physics reward value (float).

### 2.4 Proxy_Model_Output (Inference)
The output of the DistilBERT model on a test sample.
- **Fields**:
  - `sample_id`: Reference to `Cosmos3_Sample`.
  - `predicted_label`: Enum [`"constraint_satisfied"`, `"constraint_violated"`, `"success"`, `"failure"`].
  - `confidence`: Probability score (float, 0.0 to 1.0).
  - `true_label`: Ground truth label (Symbolic or Physics).
  - `is_correct`: Boolean.
  - `domain`: Enum [`"symbolic"`, `"physics_cross_domain"`].

### 2.5 Performance_Metric (Aggregate)
Aggregated statistics for the comparative analysis.
- **Fields**:
  - `domain`: Enum [`"symbolic"`, `"physics_cross_domain"`].
  - `accuracy`: Float.
  - `f1_score`: Float.
  - `auc_roc`: Float.
  - `generalization_gap`: Float (AUC_Symbolic - AUC_Physics_CrossDomain).
  - `gap_ci_lower`: Float (Lower bound of 95% CI).
  - `gap_ci_upper`: Float (Upper bound of 95% CI).
  - `significant`: Boolean (True if CI does not include 0).

### 2.6 Error_Case (Analysis)
A misclassified sample categorized for error analysis.
- **Fields**:
  - `sample_id`: Reference to `Cosmos3_Sample`.
  - `failure_mode`: Enum [`"visual_ambiguity"`, `"logical_complexity"`, `"context_mismatch"`].
  - `input_features`: Snapshot of relevant input features (e.g., frame stats, vector norm, context match).
  - `explanation`: Qualitative description of the error.

## 3. Data Flow

1. **Ingestion**: `code/scripts/download_data.py` fetches raw `Cosmos3_Sample` objects and stores them in `code/data/raw/`.
2. **Transformation**: `code/scripts/transform_actions.py` reads raw samples, calculates `vector_norm` and `context_match` (from text), applies the composite rule, and writes `Symbolic_Label` and `Physics_Label` records to `code/data/processed/symbolic_dataset.jsonl`.
3. **Training**: `code/scripts/train_symbolic.py` reads the processed dataset, trains models, and saves artifacts to `code/models/symbolic/`.
4. **Evaluation**: `code/scripts/evaluate.py` loads the Symbolic Model, generates `Proxy_Model_Output` records for both domains, and computes `Performance_Metric` aggregates.
5. **Analysis**: `code/scripts/analyze_errors.py` filters for `is_correct == False`, categorizes them into `Error_Case` records, and generates reports.

## 4. Storage Constraints

- **Raw Data**: Stored in Parquet or JSONL format.
- **Processed Data**: Stored in JSONL for easy streaming.
- **Model Artifacts**: Stored in `pytorch_model.bin` format (Hugging Face).
- **Max Size**: All derived datasets must be sampled or streamed to fit within 7 GB RAM during processing.