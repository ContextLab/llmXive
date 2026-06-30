# Data Model: NatureBench Abstraction Distance Analysis

## Entities

### 1. Task
Represents a single unit of work from the dataset (NatureBench or SWE-bench).
- **task_id**: Unique identifier (string).
- **method_description**: Text description of the scientific method (string).
- **ground_truth_sota**: Numerical SOTA value (float).
- **domain_cluster**: Category of the task (string, e.g., "Genomics", "Physics").
- **raw_data_file**: Path to the original file in `data/raw/`.
- **gold_standard_methods**: List of function names from the ground truth (list of strings).

### 2. ExecutionResult
Outcome of an agent run on a Task.
- **task_id**: Foreign key to Task.
- **agent_name**: Name of the agent used (string).
- **status**: "Success", "Timeout", "Error" (string).
- **failure_category**: One of "Syntax Error", "Wrong Method Choice", "Data Mismatch", "Timeout", or "None" (string).
- **numerical_output**: The output value generated (float, nullable).
- **relative_error_gap**: $|output - ground\_truth| / ground\_truth$ (float, nullable).
- **log_path**: Path to the execution log (string).
- **methods_used**: List of function names used by the agent (list of strings).

### 3. AbstractionScore
System-rated metric for a Task.
- **task_id**: Foreign key to Task.
- **score**: Integer 1–5 (integer).
- **novelty_index**: Calculated novelty score (float).
- **stdlib_percentage**: Percentage of standard library calls (float).
- **justification**: Text explaining the score (string).
- **expert_validated**: Boolean indicating if this score was part of the expert validation set (boolean).

### 4. ExpertRating
Rating provided by a domain expert for validation.
- **task_id**: Foreign key to Task.
- **expert_id**: Unique identifier for the expert (string).
- **score**: Integer 1–5 (integer).
- **justification**: Text explaining the score (string).
- **alpha_contribution**: Contribution to Krippendorff's Alpha (float).

## Relationships
- **Task** 1-to-Many **ExecutionResult** (per agent run).
- **Task** 1-to-1 **AbstractionScore**.
- **Task** 1-to-Many **ExpertRating**.
- **Task** 1-to-1 **Gold Standard Method List** (derived from ground truth).

## Data Flow
1.  **Ingest**: `data/raw/dataset.json` -> `Task` entities.
2.  **Gold Standard**: `Task` -> `gold_standard_methods` (extracted from ground truth).
3.  **Process**: `Task` + `Agent` -> `ExecutionResult`.
4.  **Score**: `Task` + `Gold Standard` -> `AbstractionScore`.
5.  **Validate**: `Task` + `Expert` -> `ExpertRating`.
6.  **Analyze**: Join `ExecutionResult` and `AbstractionScore` on `task_id` -> Statistical Output.

## Storage Format
- **Raw Data**: JSON/Parquet in `data/raw/`.
- **Processed Data**: JSON/CSV in `data/processed/`.
- **Schemas**: Validated against `contracts/*.schema.yaml`.