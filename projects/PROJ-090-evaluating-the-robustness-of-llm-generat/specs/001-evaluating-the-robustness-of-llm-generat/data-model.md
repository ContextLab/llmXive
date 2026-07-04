# Data Model: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## 1. Entity Relationship Overview

The data model consists of three primary entities: `Task`, `PromptVariant`, and `ExecutionResult`.

*   **Task**: Represents a unique programming problem from HumanEval.
*   **PromptVariant**: Represents a specific version of a prompt (Original or Perturbed) associated with a Task.
*   **ExecutionResult**: Represents the outcome of running the model on a PromptVariant.

## 2. Schema Definitions

### 2.1 Task
Unique identifier for a programming problem.
*   `task_id` (string): Unique ID (e.g., "HumanEval/0").
*   `canonical_prompt` (string): The original prompt text.
*   `canonical_solution` (string): The reference solution code.
*   `test_code` (string): The unit tests to validate the solution.

### 2.2 PromptVariant
A specific text input sent to the model.
*   `variant_id` (string): Unique ID.
*   `task_id` (string): Foreign key to `Task`.
*   `variant_type` (string): Enum: "original", "synonym", "typo", "rephrase".
*   `prompt_text` (string): The actual text content.
*   `similarity_score` (float): Cosine similarity to `canonical_prompt` (for non-originals).
*   `is_primary` (boolean): True if `similarity_score` > 0.95 (or > 0.90 if fallback) and included in primary analysis.
*   `raw_similarity_score` (float): The raw score before filtering (for sensitivity analysis).
*   `selected_rank` (integer): Rank of this candidate among generated candidates (1 = best).

### 2.3 ExecutionResult
The outcome of the inference and execution pipeline.
*   `result_id` (string): Unique ID.
*   `variant_id` (string): Foreign key to `PromptVariant`.
*   `generated_code` (string): The code produced by the model.
*   `execution_status` (string): Enum: "pass", "fail", "timeout", "oom", "error".
*   `error_type` (string): Enum: "syntax", "logic", "hallucination", "timeout", "none" (null if pass).
*   `generation_time_ms` (integer): Time taken to generate code.
*   `execution_time_ms` (integer): Time taken to run tests.
*   `seed` (integer): Random seed used for generation (fixed at 42).
*   `temperature` (float): Temperature used for generation (fixed at 0.0).

## 3. Data Flow

1.  **Ingestion**: `Task` records created from `HumanEval` parquet.
2.  **Perturbation**: `PromptVariant` records created. `similarity_score` calculated. `is_primary` flagged. `selected_rank` recorded.
3.  **Inference**: `ExecutionResult` records created. `generated_code` stored. `temperature` recorded.
4.  **Execution**: `execution_status` and `error_type` updated in `ExecutionResult`.
5.  **Analysis**: Aggregations performed on `ExecutionResult` joined with `PromptVariant` and `Task`.

## 4. File Formats

*   **Raw Inputs**: Parquet (HumanEval).
*   **Intermediate**: JSONL (PromptVariants with raw scores).
*   **Final Output**: CSV (ExecutionResults for analysis).
*   **Logs**: JSON (Error logs, OOM events, timeouts).