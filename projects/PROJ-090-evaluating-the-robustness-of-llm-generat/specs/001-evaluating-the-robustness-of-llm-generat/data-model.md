# Data Model: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Overview

This document defines the data schema and flow for the robustness evaluation pipeline. All data is stored in JSON/Parquet formats to ensure reproducibility and machine readability.

## Entities

### 1. Task
A single programming problem from HumanEval.
- `task_id`: Unique identifier (e.g., "HumanEval/0").
- `prompt`: Original prompt string.
- `canonical_solution`: Reference solution (unused for inference, used for validation).
- `test`: Test suite string.
- `entry_point`: Function name to call.

### 2. PerturbationCandidate
A generated variant of a task prompt.
- `task_id`: Foreign key to Task.
- `perturbation_type`: One of `synonym`, `typo`, `rephrase`.
- `perturbed_prompt`: The modified text.
- `similarity_score`: Float (0.0–1.0) from semantic validator.
- `is_valid`: Boolean (True if score > 0.95).
- `seed`: Random seed used for generation (for reproducibility).

### 3. InferenceResult
The outcome of running the model on a prompt.
- `task_id`: Foreign key.
- `prompt_type`: `original` or `perturbed`.
- `perturbation_type`: Null for original, otherwise the type.
- `generated_code`: The code string output by the model.
- `generation_time`: Seconds.
- `pass`: Boolean (True if tests pass).
- `error_type`: One of `syntax`, `logic`, `timeout`, `oom`, `none`.
- `confidence_score`: Float (model's internal confidence, if available).
- `execution_environment`: String (`CPU` or `GPU`). **New**: Added to track hardware confound.

### 4. AnalysisResult
Aggregated metrics for the final report.
- `metric_name`: e.g., "pass@1_original", "pass@1_synonym".
- `value`: Float.
- `n_samples`: Integer.
- `statistic`: e.g., "p_value", "odds_ratio", "variance_component".

## Data Flow

1.  **Raw Data**: `data/raw/humaneval.parquet` (Downloaded from HF).
2.  **Perturbation Raw**: `data/processed/perturbation_candidates_raw.json` (All generated candidates with scores).
3.  **Perturbation Filtered**: `data/processed/perturbation_candidates.json` (Candidates with score > 0.95).
4.  **Inference Logs**: `data/processed/inference_logs.json` (Model outputs and execution results).
5.  **Mixed Effects Results**: `data/processed/mixed_effects_results.json` (Variance components and coefficients).
6.  **Final Results**: `data/processed/results.csv` (Aggregated statistics for analysis).

## Constraints

- **Immutability**: Raw data files are never modified. Derivations create new files.
- **Checksums**: All files in `data/raw/` must have a corresponding SHA-256 hash recorded in `state/`.
- **PII**: No Personally Identifiable Information is present in HumanEval or generated code.