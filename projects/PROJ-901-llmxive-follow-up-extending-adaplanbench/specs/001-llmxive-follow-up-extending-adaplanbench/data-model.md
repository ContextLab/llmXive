# Data Model: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

## Overview

This document defines the data schemas for the project, ensuring strict adherence to the "Single Source of Truth" (Constitution IV) and "Data Hygiene" (Constitution III) principles. All data artifacts are stored in `data/` and validated against the schemas in `contracts/`.

## Entities

### 1. Task Instance
**Source**: `data/raw/adaplanbench.jsonl` (filtered)  
**Description**: A single household task from AdaPlanBench containing the prompt and progressive constraints.

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique identifier for the task. |
| `raw_prompt` | string | The initial task description. |
| `progressive_constraints` | list[string] | List of constraints revealed over time. |
| `constraint_count` | integer | Number of constraints in `progressive_constraints`. |
| `ground_truth_solution` | string | (Optional) The correct solution path. |

### 2. Execution Trace
**Source**: `data/processed/execution_traces.csv`  
**Description**: Aggregated results of agent execution (Dual-Track and Monolithic) for a specific task.

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Reference to Task Instance. |
| `architecture` | string | "dual_track" or "monolithic". |
| `constraint_count` | integer | Number of constraints active. |
| `initial_violation_detected` | boolean | True if the SLM initially generated a violation (before any correction). For Monolithic, this is the final state. |
| `final_adherence` | boolean | True if the final output (post-correction for Dual-Track) adhered to constraints. |
| `violation_type` | string | "explicit", "implicit_unverified", "false_negative", "none". |
| `final_plan` | string | The final generated plan (after corrections if dual-track). |
| `success` | boolean | True if the plan adhered to all explicit constraints. |

### 3. Constraint Log
**Source**: `data/processed/dual_track_logs.json`  
**Description**: Detailed log of constraint checks and revisions during Dual-Track execution.

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Reference to Task Instance. |
| `step` | integer | Step number in the execution loop. |
| `proposed_action` | string | Action proposed by the SLM. |
| `active_constraints` | list[string] | Constraints active at this step. |
| `violation_status` | string | "pass", "violation", "implicit_unverified". |
| `correction_applied` | boolean | True if the resolver forced a revision. |
| `revised_action` | string | (Optional) The revised action. |

### 4. Resource Log
**Source**: `data/processed/resource_logs.json`  
**Description**: CPU and RAM usage metrics during execution.

| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | string | ISO 8601 timestamp. |
| `task_id` | string | Current task being executed (or null). |
| `cpu_percent` | float | CPU usage percentage. |
| `ram_gb` | float | RAM usage in GB. |
| `threshold_exceeded` | boolean | True if limits (2 vCPU, 7GB) were breached. |
| `limit_breach_details` | string | Specific details of the breach (e.g., "RAM: 7.1GB"). |

### 5. Human Annotation Sample
**Source**: `data/annotations/annotation_sample.csv`  
**Description**: Subset of tasks manually annotated for validation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Reference to Task Instance. |
| `raw_prompt` | string | Task prompt. |
| `constraint_list` | string | JSON string of constraints. |
| `human_violation_label` | string | "yes", "no", "ambiguous". |
| `annotator_id` | string | ID of the human annotator. |

## Data Flow

1. **Fetch**: `loader.py` downloads AdaPlanBench (or generates proxy) -> `data/raw/`.
2. **Filter**: `loader.py` filters for `constraint_count >= 5` -> `data/processed/filtered_tasks.csv`.
3. **Execute**: `runner.py` generates `dual_track_logs.json` and `monolithic_logs.json`.
4. **Merge**: `analysis/glmm.py` merges logs -> `data/processed/execution_traces.csv`.
5. **Annotate**: `annotator.py` samples -> `data/annotations/annotation_sample.csv`.
6. **Analyze**: `analysis/glmm.py` produces `statistical_results.json`.
