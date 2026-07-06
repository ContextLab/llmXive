# Data Model: Evaluating Prompting Strategies for Code Generation

## 1. Conceptual Entities

### Task
Represents a single code generation problem from the MBPP dataset.
*   `task_id`: Unique identifier (int).
*   `description`: Natural language problem statement (string).
*   `entry_code`: Setup code required for the test (string).
*   `test_code`: Unit tests to validate the solution (string).
*   `source`: Origin of the task (string, e.g., "mbpp_test").

### Prompt
The constructed input string for the model.
*   `task_id`: Link to Task.
*   `strategy`: One of "zero-shot", "few-shot", "cot".
*   `seed`: Random seed used for generation.
*   `content`: The full text prompt sent to the model.
*   `examples`: (Optional) List of examples used in few-shot/co-t.

### Generation
The output produced by the model.
*   `generation_id`: Unique ID.
*   `prompt_id`: Link to Prompt.
*   `sample_index`: Which of the k samples (0 to k-1).
*   `raw_text`: Full model output.
*   `extracted_code`: The code block extracted via regex (string).
*   `extraction_success`: Boolean (True if code block found).

### ExecutionResult
The outcome of running the generated code.
*   `result_id`: Unique ID.
*   `generation_id`: Link to Generation.
*   `passed`: Boolean (True if all tests passed).
*   `execution_time`: Time taken in seconds (float).
*   `error_type`: One of "timeout", "memory_limit", "runtime_error", "syntax_error", "success".
*   `error_message`: Detailed error log (string).

### StrategyReport
Aggregated results for a specific strategy and seed.
*   `strategy`: Strategy name.
*   `seed`: Seed value.
*   `total_tasks`: Count of tasks evaluated.
*   `pass_at_1`: Float (0.0 to 1.0).
*   `pass_at_10`: Float (0.0 to 1.0).
*   `timeout_rate`: Float.
*   `parsing_success_rate`: Float.
*   `peak_ram_gb`: Float.
*   `total_runtime_sec`: Float.

## 2. Data Flow

1.  **Input**: MBPP Dataset (HuggingFace).
2.  **Process**:
    *   Filter to tasks.
    *   Loop: Strategy -> Seed -> Task -> Generate k samples -> Execute -> Record.
3.  **Output**: JSON files containing `ExecutionResult` records.
4.  **Aggregation**: `StrategyReport` generated from JSON files.
5.  **Analysis**: McNemar's test results appended to `StrategyReport`.

## 3. Storage Format

*   **Raw Results**: `data/results/{strategy}_{seed}.json`
    *   List of `ExecutionResult` objects.
*   **Aggregated Report**: `data/reports/final_report.json`
    *   Dictionary of `StrategyReport` objects + statistical test results.
*   **Logs**: `data/logs/execution.log`
    *   Timestamped resource usage and error logs.

## 4. Constraints & Validations

*   **Task**: `test_code` must be non-empty.
*   **Generation**: `extracted_code` must be valid Python syntax (checked by `ast.parse`).
*   **ExecutionResult**: `execution_time` must be <= 10.0 (unless timeout occurred).
*   **Resource**: Peak RAM must be logged; if > 7.0, flag in report.
