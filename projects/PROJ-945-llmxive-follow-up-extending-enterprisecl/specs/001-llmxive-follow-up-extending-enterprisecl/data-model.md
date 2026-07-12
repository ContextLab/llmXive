# Data Model: llmXive Follow-up: Extending EnterpriseClawBench

## Overview

This document defines the data structures used for the `EnterpriseClawBench` extension feature. It covers the raw input logs, the extracted feature vectors, the training triplets, and the evaluation results.

## Entities

### 1. ExecutionTrace (Raw Input)
Represents a single log entry from the `EnterpriseClawBench` dataset.

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | string | Unique identifier for the trace. |
| `task_id` | string | Identifier for the associated task. |
| `status` | string | Ground truth label: "success" or "failed". |
| `raw_log` | string | The raw text content of the execution log. |
| `timestamp` | string | ISO 8601 timestamp of the session. |

### 2. FeatureVector (Processed)
The output of the feature extraction pipeline (FR-001).

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | string | Reference to the source trace. |
| `syntax_tree_depth` | integer | Maximum depth of the parsed syntax tree. |
| `token_freq_dist` | object | Map of token type -> frequency count. |
| `pragmatic_markers` | array | List of identified markers (e.g., "error_recovery", "state_transition_error"). |
| `semantic_proxies` | object | Map of semantic features (e.g., `error_code`: "SyntaxError", `failed_func`: "db_query"). |
| `status` | string | "success", "failed", or "neutral" (if ambiguous). |
| `is_correctable` | boolean | Ground truth for "correctability" (derived from **Semantic Outcome Oracle**). |

### 3. CorrectionTriplet (Training Data)
The structured input for the T5-small model (FR-002).

| Field | Type | Description |
| :--- | :--- | :--- |
| `system_prompt` | string | The system prompt used in the session. |
| `failed_structure` | string | Serialized representation of the failed trace's features. |
| `successful_structure` | string | Serialized representation of the corresponding successful trace's features. |
| `label` | string | "correctable" or "unfixable". |

### 4. EvaluationResult (Output)
The result of the Artifact Delivery Score evaluation (FR-004, FR-005).

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Identifier for the task. |
| `baseline_score` | float | Artifact Delivery Score for the baseline configuration. |
| `adapter_score` | float | Artifact Delivery Score for the adapter-enhanced configuration. |
| `intervention_applied` | boolean | Whether the Rule-Based Rewriter was triggered. |
| `latency_ms` | integer | Inference latency in milliseconds. |
| `resource_log` | object | Memory (RSS) and time logs. |

## Relationships

- **1-to-1**: `ExecutionTrace` -> `FeatureVector` (One trace produces one feature vector).
- **1-to-1**: `FeatureVector` (failed) + `FeatureVector` (success) -> `CorrectionTriplet` (Pairing based on `task_id`).
- **1-to-Many**: `Task` -> `EvaluationResult` (One task is evaluated once for baseline and once for adapter).

## Data Flow

1.  **Ingestion**: `ExecutionTrace` loaded from `data/raw/`.
2.  **Extraction**: `FeatureVector` generated (including semantic proxies) and saved to `data/processed/features.json`.
3.  **Pairing**: `CorrectionTriplet` constructed and saved to `data/processed/triplets.json`.
4.  **Training**: Model trained on `triplets.json`.
5.  **Intervention**: Rule-Based Rewriter applied if model predicts "correctable".
6.  **Evaluation**: `EvaluationResult` generated for the 120-task Lite set and saved to `data/processed/results.csv`.
