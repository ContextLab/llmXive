# Data Model: AdaPlanBench Reproduction & Validation

## Overview

This document defines the data structures used in the AdaPlanBench reproduction. The model is derived from the JSON artifacts expected by the benchmark runner and the internal state of the adaptive planning loop. It includes definitions for Task Instances, Plan Histories, Evaluation Results, and **Agent Configurations**.

## Entity Definitions

### 1. TaskInstance
Represents a single problem from the `domain_metadata`.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `task_id` | `string` | Unique identifier for the task. | Yes |
| `goal` | `string` | The high-level objective the agent must achieve. | Yes |
| `initial_state` | `object` | The starting configuration of the environment. | Yes |
| `hidden_constraints` | `array[string]` | List of constraints not visible to the agent initially. | Yes |
| `domain` | `string` | The domain name (e.g., "housing"). | Yes |

### 2. PlanHistory
A chronological record of the agent's attempts and the environment's feedback.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `step_number` | `integer` | Sequential step in the planning loop. | Yes |
| `agent_plan` | `string` | The plan proposed by the agent at this step. | Yes |
| `feedback` | `string` | The constraint violation feedback from the environment (empty if valid). | Yes |
| `timestamp` | `string` | ISO 8601 timestamp of the step. | Yes |

### 3. EvaluationResult
The final output artifact for a single task, written to `outputs/`.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `task_id` | `string` | Reference to the TaskInstance. | Yes |
| `initial_plan` | `string` | The very first plan generated. | Yes |
| `feedback_history` | `array[object]` | List of all feedback messages received. | Yes |
| `final_plan` | `string` | The last plan generated (success or failure). | Yes |
| `success_status` | `boolean` | `true` if the final plan satisfied all constraints. | Yes |
| `constraints_encountered` | `integer` | Count of unique constraints triggered during the run. | Yes |
| `execution_time_ms` | `integer` | Total time taken for the task. | Yes |
| `error_message` | `string` | Error details if the task failed due to system error (not logic). | No |

### 4. AgentConfiguration
Defines the parameters for the agent used in a specific run. This entity is critical for reproducibility and distinguishes between the Mock and LLM agents.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `agent_type` | `string` | Type of agent: "mock" or "cpu_llm". | Yes |
| `model_name` | `string` | Name of the model (e.g., "TinyLlama/TinyLlama-1.1B-Chat-v1.0"). Only used if `agent_type` is "cpu_llm". | No |
| `temperature` | `float` | Sampling temperature (0.0 for deterministic, >0.0 for stochastic). | Yes |
| `max_tokens` | `integer` | Maximum tokens to generate. | Yes |
| `mock_behavior` | `object` | Configuration for mock agent behavior (e.g., `{"force_violation": true}`). Only used if `agent_type` is "mock". | No |

## Data Flow

1. **Input**: `domain_metadata/housing/final/query_housing_macgyver_resample.json` -> Parsed into `TaskInstance` objects.
2. **Configuration**: `AgentConfiguration` loaded from CLI args or config file.
3. **Processing**: `TaskInstance` + `AgentConfiguration` -> `PlanHistory` (via `runner.py` loop).
4. **Output**: `PlanHistory` + `TaskInstance` -> `EvaluationResult` -> Saved as `outputs/{task_id}.json`.
5. **Aggregation**: All `EvaluationResult` files -> Merged into `outputs/summary.json` containing global metrics.

## Storage Constraints

- **Format**: JSON (UTF-8).
- **Size Limit**: Each `EvaluationResult` is expected to be < 100KB. Total output for 20 tasks < 2MB.
- **Retention**: Artifacts are retained for the duration of the CI job and can be uploaded as build artifacts.