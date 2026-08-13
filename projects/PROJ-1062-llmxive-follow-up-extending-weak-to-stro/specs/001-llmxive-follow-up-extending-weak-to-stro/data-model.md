# Data Model: Cross-Architecture Distillation

## 1. Overview

This document defines the data schemas, storage formats, and relationships for the `llmXive` cross-architecture distillation experiment. All data is stored in `projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/data/`.

## 2. Data Flow

1.  **Ingestion**: Raw AIME dataset downloaded from HuggingFace.
2.  **Preprocessing**: Prompts and ground-truth tokens extracted; teacher probabilities computed.
3.  **Human Verification**: A subset of problems is manually verified and stored.
4.  **Training**: Intermediate logs (loss, reward) stored per step.
5.  **Evaluation**: Final metrics (log-prob, improvement) stored per problem.
6.  **Aggregation**: Statistical results (p-values, effect sizes) stored.

## 3. Schema Definitions

### 3.1 Raw Dataset (AIME)
- **Source**: HuggingFace `MathArena/aime_2024`.
- **Format**: Parquet / JSONL.
- **Fields**:
  - `problem_id`: Unique identifier.
  - `problem_text`: The math problem string.
  - `solution`: Full solution string (used to extract reasoning steps).

### 3.2 Human Verified Subset
- **Location**: `data/raw/human_verified_subset.jsonl`
- **Schema**:
  - `problem_id`: String.
  - `problem_text`: String.
  - `ground_truth_tokens`: List of integers (Token IDs of the *human-verified* solution).
  - `is_human_verified`: Boolean (Always `true`).
  - `teacher_output_tokens`: List of integers (Token IDs of the teacher's output, for comparison).
  - `notes`: String (Optional notes on correctness/ambiguity).

### 3.3 Processed Training Data
- **Location**: `data/processed/aime_processed.jsonl`
- **Schema**:
  - `problem_id`: String.
  - `prompt`: String (Problem text).
  - `ground_truth_tokens`: List of integers (Token IDs of the solution).
  - `teacher_reward`: List of floats (Computed implicit reward per token).
  - `teacher_baseline_prob`: List of floats (Baseline probability per token).

### 3.4 Training Logs
- **Location**: `data/processed/training_logs/{student_arch}.jsonl`
- **Schema**:
  - `step`: Integer.
  - `loss`: Float.
  - `reward_mean`: Float.
  - `gradient_norm`: Float.
  - `timestamp`: ISO8601.

### 3.5 Evaluation Results
- **Location**: `data/processed/eval_results.jsonl`
- **Schema**:
  - `problem_id`: String.
  - `student_arch`: String (`MoE` or `SSM`).
  - `training_method`: String (`Direct-OPD` or `Baseline`).
  - `log_prob_improvement`: Float (Difference in log-prob of ground truth).
  - `tokens_evaluated`: Integer.
  - `is_human_verified_subset`: Boolean (True if from the 20 human-verified problems).

### 3.6 Statistical Summary
- **Location**: `data/processed/stats_summary.json`
- **Schema**:
  - `architecture`: String.
  - `method`: String.
  - `mean_improvement`: Float.
  - `std_improvement`: Float.
  - `p_value_raw`: Float.
  - `p_value_adjusted`: Float.
  - `significant`: Boolean.
  - `m_des`: Float (Minimum Detectable Effect Size).

## 4. Data Hygiene & Checksums

- **Checksums**: Every file in `data/` will have a SHA-256 checksum recorded in `state/.../artifact_hashes`.
- **Immutability**: Raw data is never modified. Derived data is written to new files.
- **PII**: No PII expected in AIME math problems.

## 5. Contract Validation

The Implementer Agent must validate all output data against the schemas defined in `contracts/`.