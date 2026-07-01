# Data Model: Macaron-A2UI Reproduction

## 1. Overview

This document defines the data structures used in the reproduction pipeline. It ensures that the `evaluate_api_model.py` output and the input task data conform to expected schemas, allowing for automated validation.

## 2. Input Data: Task Instances

The input data consists of JSON files containing task instances for the four datasets: `annomi`, `esconv`, `multiwoz`, and `sgd`.

### 2.1 Entity: `TaskInstance`

Represents a single dialogue task to be evaluated.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `task_id` | `string` | Unique identifier for the task. | Yes |
| `dataset` | `string` | Source dataset name (`annomi`, `esconv`, etc.). | Yes |
| `dialogue_history` | `array[string]` | List of dialogue turns. | Yes |
| `target_ui` | `object` | Ground truth UI description (if available). | No |
| `constraints` | `object` | Task-specific constraints. | No |
| `model_name` | `string` | The specific model name to be used for this task (from config). | Yes |

## 3. Output Data: Evaluation Report

The `evaluate_api_model.py` script generates a JSON report containing the evaluation results.

### 3.1 Entity: `EvaluationReport`

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `overall_score` | `number` | The calculated "Overall" accuracy score. (N/A if uncomputable) | Yes |
| `dataset_scores` | `object` | Map of dataset names to their individual scores. | Yes |
| `execution_time` | `number` | Total runtime in seconds. | Yes |
| `task_results` | `array[TaskResult]` | List of results for each evaluated task. | Yes |
| `artifacts` | `array[string]` | Paths to generated PNG images. | Yes |
| `metadata` | `object` | Model version, device, batch size used. | Yes |
| `status` | `string` | `success`, `timeout`, `uncomputable`, `incompatible`. | Yes |
| `model_name` | `string` | The exact model name used. | Yes |

### 3.2 Entity: `TaskResult`

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `task_id` | `string` | Reference to the input task. | Yes |
| `status` | `string` | `success`, `timeout`, `error`. | Yes |
| `ui_generated` | `boolean` | Whether a UI was generated. | Yes |
| `score` | `number` | Task-level score (0.0 - 1.0). | Yes |

## 4. Artifacts

- **PNG Images**: Generated in `render/public/showcase/<model_name>/images/compare/`.
- **Naming Convention**: `<task_id>.png`.