# Data Model: llmXive follow-up: extending "AutoResearchClaw"

## 1. Entity Relationship Overview

The data model supports a linear pipeline: **Raw Data** -> **Derived Traces** -> **Annotated Cases** -> **Rule Library** -> **Execution Logs** -> **Aggregated Metrics**.

### Key Entities
1.  **FailureCase**: A single error event derived from a reasoning trace, with structural annotation.
2.  **DistilledRule**: A heuristic derived from a failure case.
3.  **PivotAttempt**: A record of an execution attempt (Rule Engine or Baseline).
4.  **MetricAggregation**: Summary statistics for the statistical model.

## 2. Schema Definitions

### 2.1 FailureCase
Represents a single error event derived from the dataset's reasoning traces.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `case_id` | String | Unique identifier (UUID) | PK |
| `topic` | String | The research topic (e.g., "math", "coding") | Not Null |
| `raw_reasoning_trace` | String | The original reasoning trace from the dataset | Not Null |
| `derived_error_log` | String | The error log derived from the trace (e.g., extracted "SyntaxError") | Not Null |
| `structural_feature` | Enum | `Syntactic`, `Logical`, `Semantic`, `Missing`, `Unstructured` | Not Null |
| `ground_truth_action` | String | The correct pivot action (from dataset) | Not Null |
| `source_dataset` | String | URL or ID of the source dataset | Not Null |

### 2.2 DistilledRule
A rule generated from a failure case.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `rule_id` | String | Unique identifier | PK |
| `condition_pattern` | String | Regex or string match condition | Not Null |
| `pivot_action` | String | The action to execute | Not Null |
| `derived_from_case_id` | String | Reference to `FailureCase.case_id` | FK |
| `confidence_score` | Float | Model confidence (0.0-1.0) | [0.0, 1.0] |
| `category` | Enum | Same as `structural_feature` | Not Null |

### 2.3 PivotAttempt
A record of a single execution attempt.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `attempt_id` | String | Unique identifier | PK |
| `case_id` | String | Reference to `FailureCase.case_id` | FK |
| `method` | Enum | `RuleEngine`, `Baseline` | Not Null |
| `time_to_pivot` | Float | Time in seconds | > 0 |
| `success` | Boolean | Did the pivot succeed? | Not Null |
| `error_type` | Enum | `Coverage Gap`, `Distillation Error`, `None` | Not Null |
| `timestamp` | DateTime | Execution time | Not Null |

## 3. Data Flow & Transformations

1.  **Ingestion**: `raw.parquet` -> `failure_case.csv` (filtered, sampled, `derived_error_log` extracted from `reasoning`).
2.  **Annotation**: `failure_case.csv` -> `annotated_cases.csv` (adds `structural_feature`). **Validated against `contracts/failure_case.schema.yaml`**.
3.  **Distillation**: `annotated_cases.csv` -> `rules_library.json`. **Validated against `contracts/distilled_rule.schema.yaml`**.
4.  **Execution**: `annotated_cases.csv` + `rules_library.json` -> `pivot_attempts.csv` (Rule Engine logs merged with Baseline logs).
5.  **Analysis**: `pivot_attempts.csv` -> `metrics_summary.csv` (for regression).

## 4. Constraints & Validation

- **Uniqueness**: `case_id` and `rule_id` must be unique.
- **Referential Integrity**: `PivotAttempt.case_id` must exist in `FailureCase`.
- **Enum Validation**: `structural_feature` and `method` must match the defined sets.
- **Data Hygiene**: All derived files must be checksummed; raw files are immutable. **Schema Validation**: All derived files must pass validation against their respective `contracts/*.schema.yaml` files before being written to disk.