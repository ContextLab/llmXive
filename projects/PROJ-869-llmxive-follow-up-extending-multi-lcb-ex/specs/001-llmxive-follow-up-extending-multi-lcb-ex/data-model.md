# Data Model: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## 1. Entity Definitions

### EvaluationTask
Represents a single algorithmic problem selected for the study.
-   **task_id**: Unique identifier (string).
-   **problem_statement**: Text of the problem description.
-   **target_language**: Language to generate code for (e.g., "rust", "kotlin").
-   **difficulty**: Enum {Easy, Medium, Hard}.
-   **topic**: Enum {DP, Graphs, Math, Strings, etc.}.
-   **python_solution**: Ground-truth Python code (used for anchor extraction).
-   **test_cases**: List of test case objects (input, expected_output).
-   **blind_fail_count**: Integer (0-3) indicating how many times the blind run failed (using fixed seed/temperature) during the filter phase.
-   **selected**: Boolean (True if task passed the stochasticity filter).

### PartialLogicTrace
Represents the extracted algorithmic scaffold.
-   **task_id**: Foreign key to EvaluationTask.
-   **anchor_steps**: List of strings (pseudo-code ONLY, representing the first 3 steps).
-   **extraction_method**: String (e.g., "AST-Based").
-   **status**: Enum {Success, Failed}.

### GenerationResult
Represents the output of the LLM for a specific condition.
-   **task_id**: Foreign key to EvaluationTask.
-   **condition**: Enum {blind, guided}.
-   **generated_code**: String (the model's output).
-   **execution_status**: Enum {Pass, Fail, Timeout, CompileError, RuntimeError}.
-   **error_type**: Enum {None, Syntax, Library, Runtime, Logic Transfer}.
-   **execution_time_ms**: Float (duration of sandbox execution).
-   **timeout_triggered**: Boolean.

### StatisticalReport
Aggregates the final results.
-   **total_tasks**: Integer.
-   **blind_pass_count**: Integer.
-   **guided_pass_count**: Integer.
-   **mcnemar_p_value**: Float.
-   **bootstrap_ci**: Map {lower, upper}.
-   **significance**: Boolean (True if p < 0.05).
-   **error_distribution**: Map<ErrorType, Count>.
-   **stability_rate**: Float (Sandbox Stability Rate).

## 2. Data Flow Diagram

```mermaid
graph TD
    A[Raw Multi-LCB Parquet] -->|Stream & Filter| B(Filtered Task List)
    B -->|Extract| C[Partial Logic Trace (Pseudo-code)]
    B -->|Re-verify Blind (Seed 42)| D[Blind Generation Results]
    C -->|Inject Anchor| E[Guided Generation Results]
    D -->|Execute| F[Sandbox Execution Logs]
    E -->|Execute| F
    F -->|Classify| G[Error Categorized Results]
    G -->|Pair & Test| H[Statistical Report]
```

## 3. Storage & Hygiene

-   **Raw Data**: `data/raw/lcb_test.parquet` (Checksum: SHA-256 stored in `state/`).
-   **Derived Data**:
    -   `data/processed/filtered_tasks.json` (List of selected tasks, checksummed).
    -   `data/processed/anchors.json` (List of extracted traces).
    -   `results/blind_results.json`, `results/guided_results.json`.
-   **No In-Place Modification**: Raw parquet is never edited. All transformations produce new files.
-   **PII Scan**: All text fields (problem statements, code) scanned for PII before commit.

## 4. Schema Constraints

-   **Uniqueness**: `task_id` must be unique across all results.
-   **Completeness**: `execution_status` must be populated for every `GenerationResult`.
-   **Consistency**: `error_type` must be "None" if `execution_status` is "Pass".
-   **Validation**: All JSON outputs must conform to the schemas in `contracts/`.
