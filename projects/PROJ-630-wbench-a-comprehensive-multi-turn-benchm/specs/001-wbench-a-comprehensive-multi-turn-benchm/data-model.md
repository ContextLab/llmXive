# Data Model: Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

## 1. Overview

This document defines the data structures for the WBench evaluation pipeline. It covers the input dataset schema, the internal processing objects, and the output leaderboard schema.

## 2. Input Data Model (WBench Dataset)

The input is a Parquet file containing test cases.

### Schema: `wbench_test_case`

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `case_id` | string | Unique identifier for the test case. | WBench Parquet |
| `prompt` | string | The initial text prompt for the video generation. | WBench Parquet |
| `interaction_sequence` | list[dict] | Sequence of user interactions (action, timestamp). | WBench Parquet |
| `video_path` | string | Path to the generated video (must exist; if missing, case is skipped). | WBench Parquet |
| `ground_truth` | dict | Expected outcomes for adherence metrics. | WBench Parquet |
| `metadata` | dict | Additional context (model used, settings). | WBench Parquet |

**Notes**:
- If `video_path` is missing or the file does not exist, the pipeline will **skip** the case. No dummy frames are generated.
- `interaction_sequence` must be a list of dictionaries with keys `action` and `timestamp`.
- **Validation**: Phase 0 will verify the presence of `interaction_sequence` and `ground_truth` columns. If missing, the pipeline halts.

## 3. Internal Processing Model

### Schema: `metric_result`

| Field | Type | Description |
|-------|------|-------------|
| `case_id` | string | Reference to the input case. |
| `metric_name` | string | Name of the sub-metric (e.g., "motion_smoothness"). |
| `score` | float | Numerical score (0.0 - 1.0). |
| `status` | string | "success", "failed", "skipped", "N/A". |
| `error_message` | string | Optional error details if status != "success". |

### Schema: `aggregated_case`

| Field | Type | Description |
|-------|------|-------------|
| `case_id` | string | Unique identifier. |
| `video_quality_score` | float | Mean of video quality sub-metrics. |
| `setting_adherence_score` | float | Mean of setting adherence sub-metrics. |
| `interaction_adherence_score` | float | Mean of interaction adherence sub-metrics. |
| `consistency_score` | float | Mean of consistency sub-metrics. |
| `physics_compliance_score` | float | Mean of physics compliance sub-metrics. |
| `overall_score` | float | Weighted average of all dimensions. |
| `status` | string | "completed", "partial", "failed", "skipped". |

## 4. Output Data Model (Leaderboard)

The final output is a CSV file matching the structure of the paper's `assets/leaderboard_9models_full.csv`.

### Schema: `leaderboard`

| Field | Type | Description |
|-------|------|-------------|
| `model_name` | string | Name of the model being evaluated (or "reproduction" for this run). |
| `video_quality` | float | Mean score for video quality dimension. |
| `setting_adherence` | float | Mean score for setting adherence dimension. |
| `interaction_adherence` | float | Mean score for interaction adherence dimension. |
| `consistency` | float | Mean score for consistency dimension. |
| `physics_compliance` | float | Mean score for physics compliance dimension. |
| `total_cases` | int | Number of cases processed. |
| `success_rate` | float | Percentage of cases with non-null scores. |
| `variance_notes` | string | Optional notes on deviations from the original paper (e.g., "Frame sampling used", "Subset evaluation"). |

## 5. Data Flow

1. **Load**: Read `first_person.parquet` into `wbench_test_case` objects.
2. **Validate**: Check for required columns (`interaction_sequence`, `video_path`).
3. **Process**: For each case with valid video data, compute `metric_result` objects. Skip cases with missing video.
4. **Aggregate**: Group `metric_result` by `case_id` to form `aggregated_case`.
5. **Finalize**: Compute global means to form the `leaderboard` row.
6. **Export**: Write `final_results.csv`.