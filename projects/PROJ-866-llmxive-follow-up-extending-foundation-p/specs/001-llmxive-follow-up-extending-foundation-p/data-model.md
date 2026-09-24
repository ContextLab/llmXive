# Data Model: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Overview

This document defines the data structures used in the simulation pipeline. All data is stored in JSON format for intermediate steps and CSV for final results.

## Entities

### 1. Workflow

A directed graph representing a multi-agent task chain.

-   **workflow_id**: Unique string identifier (UUID).
-   **delegation_depth**: Integer (1-10).
-   **policy_complexity**: Integer (1-20).
-   **nodes**: List of `PolicyNode` objects.
-   **edges**: List of `(source, target)` tuples.
-   **is_valid**: Boolean (true if solvable by Oracle; false if impossible even with full context).

### 2. PolicyNode

A single constraint or rule attached to a workflow step.

-   **node_id**: Unique string.
-   **type**: String (e.g., "budget", "sovereignty", "auth").
-   **content**: String (text description of the policy).
-   **dependencies**: List of `node_id`s that must be present for this node to be valid.

### 3. ExecutionLog

A record of a single workflow run.

-   **workflow_id**: Reference to the workflow.
-   **mode**: String ("full_context" or "compressed").
-   **compression_depth**: Integer (0 for full, k for compressed).
-   **token_count**: Integer (calculated via `tiktoken` **cl100k_base**).
-   **context_reduction_pct**: Float (0.0 to 100.0) OR String `"[deferred]"` for edge cases (single-node graph, depth=0).
-   **violations**: List of `Violation` objects.
-   **error_rate**: Float (0.0 to 1.0). Calculated as `Violations / Total Steps Attempted` for valid workflows. Invalid workflows are excluded from the denominator.
-   **timestamp**: ISO 8601 string.

### 4. Violation

A specific policy breach detected during execution.

-   **node_id**: The policy node that was missing or violated.
-   **reason**: String (e.g., "missing_context", "constraint_breach", "deduction_failure").
-   **step_index**: Integer (index in the workflow execution).

### 5. TradeOffCurve

Aggregated results for the regression analysis.

-   **reduction_pct**: Float (binned or interpolated).
-   **error_rate**: Float (mean error rate at this reduction level).
-   **std_dev**: Float.
-   **n_samples**: Integer.
-   **threshold_confidence_lower**: Float (from bootstrapping, 1000 resamples).
-   **threshold_confidence_upper**: Float (from bootstrapping, 1000 resamples).

### 6. RunMetrics

System performance metrics (SC-005).

-   **total_wall_clock_time_seconds**: Float.
-   **start_timestamp**: ISO 8601 string.
-   **end_timestamp**: ISO 8601 string.
-   **total_workflows**: Integer.
-   **total_executions**: Integer.

## Data Flow

1.  **Generation**: `generator.py` produces `data/raw/workflows.json`.
2.  **Execution**: `executor.py` reads `workflows.json`, runs simulations, writes `data/processed/full_context_logs.json` and `data/processed/compressed_context_logs.json`.
3.  **Aggregation**: `analyzer.py` reads processed logs, computes statistics, writes `data/results/tradeoff_curve.csv` and `data/results/threshold_report.json`.
4.  **Metrics**: `analyzer.py` (or CLI) writes `data/results/run_metrics.json`.
5.  **Validation**: All files are checksummed and stored in `state/` with hashes.

## Specific Formatting Requirements

-   **Threshold Rounding**: The `threshold` value in `threshold_report.json` and the `reduction_pct` in `tradeoff_curve.csv` must be **rounded to 2 decimal places**.
-   **Edge Case Marker**: The `context_reduction_pct` field must contain the literal string `"[deferred]"` for single-node graphs or compression depth 0.
-   **SSoT**: `data/results/tradeoff_curve.csv` is the Single Source of Truth for the paper. `analysis_results.json` (if generated) is the intermediate artifact for code logic.
