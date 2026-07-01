# Data Model: MobileForge Reproduction

## 1. Overview

This document defines the data structures for the MobileForge reproduction pipeline. All data artifacts are stored as JSON/JSONL files in the `data/` directory. The schemas are designed to be strict to facilitate automated validation in the `contracts/` phase.

## 2. Entity Definitions

### 2.1 Trajectory
A `Trajectory` represents a single interaction session between the agent and the Android environment for a specific task.

*   **ID**: `task_id` (string)
*   **Steps**: List of `Step` objects.
*   **Status**: `final_status` (enum: "success", "failure", "timeout", "error").
*   **Metadata**: `start_time`, `end_time`, `total_steps`.

### 2.2 Step
A `Step` represents a single action-observation pair within a trajectory.

*   **ID**: `step_id` (integer, 0-indexed).
*   **Action**: `action_type` (string, e.g., "tap", "swipe", "input"), `action_params` (dict).
*   **Observation**: `screen_state` (string or base64 placeholder), `error_message` (string, optional).
*   **Outcome**: `outcome` (enum: "success", "failure", "partial").

### 2.3 Feedback Signal
A `FeedbackSignal` is generated for failed steps to guide the next iteration (HiFPO).

*   **Source**: `task_id`, `step_id`.
*   **Error Type**: `error_type` (string, e.g., "wrong_element", "infinite_loop").
*   **Hint**: `hint_text` (string, min length 10).
*   **Context**: `step_context` (string, summary of the step).
*   **Validation**: `validation_rules` (object) documenting heuristic checks (e.g., keyword presence).

### 2.4 Evaluation Metric
Aggregated performance metrics for the run.

*   **Metric**: `pass_k` (float, e.g., Pass@3).
*   **Confidence**: `ci_lower` (float), `ci_upper` (float) (Exact Binomial).
*   **Details**: `total_tasks`, `solved_tasks`.
*   **Note**: Baseline comparison is removed from the schema as it is "Contextual Observation Only".

### 2.5 System Monitoring Log
A `SystemMonitoringLog` records resource usage to ensure compliance with constraints.

*   **Timestamp**: `timestamp` (ISO 8601).
*   **Resource**: `resource_type` (enum: "memory", "cpu").
*   **Value**: `value` (float, e.g., GB for memory, % for CPU).
*   **Status**: `status` (enum: "ok", "warning", "critical").

## 3. Relationships

*   **Trajectory** contains multiple **Steps**.
*   **Feedback Signal** references a specific **Step** within a **Trajectory**.
*   **Evaluation Metric** aggregates results from multiple **Trajectories**.
*   **System Monitoring Log** is independent but associated with the run ID.

## 4. Data Flow

1.  **Input**: `task_ids` (list of strings).
2.  **Process**: `rollout/run.py` -> Generates `trajectories.jsonl`.
3.  **Process**: `curriculum_generator.py` -> Reads `trajectories.jsonl` -> Generates `feedback.jsonl`.
4.  **Process**: `evaluation/run.py` -> Reads `feedback.jsonl` / `trajectories.jsonl` -> Generates `evaluation_results.json`.
5.  **Process**: `monitor.py` -> Writes `monitoring_logs.json`.
6.  **Output**: Final report with `pass_k` and Exact Binomial CI.

## 5. Constraints & Validation Rules

*   **Memory**: Total size of `trajectories.jsonl` for 10 tasks must be <500MB.
*   **Timeout**: No step duration >300s.
*   **Hint Quality**: `hint_text` must be non-empty, length ≥10, and contain at least one actionable verb (e.g., 'tap', 'swipe', 'enter').
*   **Status**: `final_status` must be one of the defined enums.
*   **Schema Conformance**: All artifacts must validate against their respective contracts in `contracts/`.