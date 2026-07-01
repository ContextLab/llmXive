# Data Model: Agents' Last Exam Reproduction

## 1. Overview

This document defines the data structures used for task execution artifacts and the final validation report. The data model is derived from the `ale_run` output specifications and the requirements of the `validation_report.md`. 

**Critical Transformation Step**: The raw output from `ale_run` (which may be unstructured or in a proprietary format) must be **parsed and normalized** into the standardized `Task Execution Artifact` schema defined below before any validation or reporting occurs.

## 2. Entity Definitions

### 2.1 Task Execution Artifact
Generated for each executed task. Contains the trajectory of actions and a summary of the outcome. This artifact is the result of parsing raw `ale_run` output and normalizing it to the defined schema.

**Source**: `ale_run` CLI output (parsed and normalized to match this schema).

**Fields**:
-   `task_id`: Unique identifier for the task (e.g., `ar_full_300`).
-   `status`: Execution outcome (`SUCCESS`, `FAILED`, `TIMEOUT`, `MISSING_API_KEY`, `SANDBOX_ERROR`).
-   `start_time`: ISO 8601 timestamp of execution start.
-   `end_time`: ISO 8601 timestamp of execution end.
-   `duration_seconds`: Total execution time.
-   `trajectory`: Array of steps (action, observation, response).
-   `evaluation_result`: Pass/Fail status from the task's internal evaluator (if available).
-   `error_message`: Details if the status is not `SUCCESS`.

### 2.2 Validation Report
Aggregated summary of all executed tasks and comparison to paper claims.

**Source**: `generate-report.sh` aggregation logic (after schema validation).

**Fields**:
-   `report_date`: ISO 8601 date.
-   `tasks_executed`: List of `task_id` strings.
-   `total_tasks`: Count of executed tasks.
-   `passed_count`: Count of tasks with `SUCCESS` and `evaluation_result` = `PASS`.
-   `failed_count`: Count of tasks with `FAILED` or `evaluation_result` = `FAIL`.
-   `timeout_count`: Count of tasks that timed out.
-   `pass_rate`: Calculated percentage (passed / total). *Note: With N=1, this is either 0.0 or 1.0, not a statistical rate.*
-   `paper_claim_pass_rate`: The value stated in the paper (string or number).
-   `comparison_statement`: Text describing the alignment or discrepancy, explicitly noting the N=1 limitation.
-   `limitations`: Text describing sample size and constraints.

## 3. Data Flow

1.  **Input**: `ale_run` CLI arguments (task ID, agent config).
2.  **Process**: `ale_run` executes task, writes raw output to `artifacts/<task_id>/`.
3.  **Normalization**: A parser script reads the raw output and transforms it into the `Task Execution Artifact` JSON structure defined in this document.
4.  **Validation**: The normalized JSON is validated against `task_artifact.schema.yaml`. If invalid, the process halts.
5.  **Aggregation**: `generate-report.sh` reads all valid `summary.json` files, aggregates counts, and calculates `pass_rate`.
6.  **Output**: `validation_report.md` (Markdown) and `validation_report.json` (machine-readable).

## 4. Constraints

-   **Timestamps**: Must be ISO 8601 format.
-   **Status Values**: Must be one of the enumerated set (`SUCCESS`, `FAILED`, etc.).
-   **File Paths**: Artifacts must be stored in `artifacts/<task_id>/`.
-   **Schema Compliance**: All artifacts must strictly conform to `task_artifact.schema.yaml` before being included in the report.