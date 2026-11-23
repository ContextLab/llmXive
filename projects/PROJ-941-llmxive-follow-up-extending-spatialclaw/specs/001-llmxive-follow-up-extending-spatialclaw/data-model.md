# Data Model: llmXive follow-up: extending "SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning"

## Overview
This document defines the data structures for the restricted agent experiment. All data flows from the `loader` (synthetic proxy) through the `kernel` to the `metrics` collector, and finally to statistical analysis.

## Core Entities

### TaskInstance
Represents a single spatial reasoning query.
- **task_id**: `string` (UUID)
- **task_type**: `enum` ["occlusion", "depth", "relative_position"]
- **scene_3d**: `object` (Point cloud or mesh representation, stored as numpy array or structured dict)
- **ground_truth**: `object` (Label, e.g., "object A is behind object B")
- **query_text**: `string` (Natural language prompt)
- **projection_2d**: `object` (Derived 2D representation: bounding boxes, depth histogram)

### ExecutionLog
Records the agent's interaction with the restricted kernel.
- **run_id**: `string`
- **task_id**: `string`
- **agent_type**: `enum` ["2D_restricted", "3D_baseline"]
- **step_id**: `integer`
- **code_executed**: `string`
- **status**: `enum` ["success", "blocked", "error"]
- **error_type**: `string` (e.g., "RestrictedActionError", "ImportError")
- **wall_clock_time_ms**: `float`
- **seed_used**: `integer`
- **timestamp**: `ISO8601`

### PerformanceMetric
Aggregated results for analysis.
- **task_id**: `string`
- **task_type**: `enum`
- **agent_type**: `enum`
- **success_flag**: `boolean`
- **latency_ms**: `float`
- **iteration**: `integer` (1 to n)

### StatisticalResult
Output of the analysis phase.
- **task_type**: `enum`
- **test_statistic**: `float`
- **p_value_raw**: `float`
- **p_value_corrected**: `float` (Bonferroni)
- **significance**: `boolean`
- **sensitivity_data**: `list` (Threshold sweep results)

## Data Flow
1. **Generation**: `loader.py` creates `TaskInstance` objects (synthetic or loaded).
2. **Projection**: `projector.py` converts `scene_3d` to `projection_2d`.
3. **Execution**: `agent_2d.py` and `baseline_3d.py` process tasks, generating `ExecutionLog`.
4. **Aggregation**: `collector.py` merges logs into `PerformanceMetric`.
5. **Analysis**: `stats/tests.py` and `stats/sensitivity.py` produce `StatisticalResult`.

## Storage Format
- **Raw Data**: JSONL or Parquet in `data/raw/`.
- **Logs**: CSV in `results/logs/`.
- **Results**: CSV/JSON in `results/analysis/`.
