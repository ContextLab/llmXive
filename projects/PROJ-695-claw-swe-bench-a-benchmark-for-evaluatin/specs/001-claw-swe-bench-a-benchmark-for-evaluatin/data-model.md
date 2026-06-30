# Data Model: Claw-SWE-Bench Reproduction & Validation

## Overview

This document defines the data structures used for ingestion, processing, and output in the Claw-SWE-Bench reproduction pipeline. The model is designed to be lightweight, JSON/Parquet compatible, and strictly typed to facilitate validation against the `contracts/` schemas.

## Core Entities

### 1. Instance (Input)
Represents a single software engineering task from the SWE-bench dataset.

-   `instance_id`: string (Unique identifier, e.g., `django__django-12345`)
-   `repo`: string (Repository path, e.g., `django/django`)
-   `version`: string (Git tag or commit hash)
-   `base_commit`: string (SHA of the commit to patch)
-   `problem_statement`: string (The natural language description of the bug/task)
-   `hints_text`: string (Optional hints provided by the dataset)
-   `created_at`: string (ISO 8601 timestamp)

### 2. EvaluationRun (Context)
Represents a single execution of the benchmark with specific configuration.

-   `run_id`: string (UUID generated at start)
-   `adapter_type`: string (`minimal` or `full`)
-   `model_name`: string (e.g., `glm-5.1`)
-   `dataset_subset`: string (`multilingual` or `verified_lite`)
-   `start_time`: string (ISO 8601)
-   `end_time`: string (ISO 8601, nullable if timeout)
-   `status`: string (`completed`, `timeout`, `error`)

### 3. Result (Output)
Represents the outcome of processing a single instance.

-   `instance_id`: string
-   `run_id`: string
-   `status`: string (`passed`, `failed`, `failed_apply`, `timeout`, `data_missing`, `api_error`)
-   `patch_generated`: boolean
-   `patch_content`: string (Nullable, the generated diff)
-   `execution_log`: string (Nullable, snippet of logs)
-   `tokens_input`: integer
-   `tokens_output`: integer
-   `api_cost_usd`: float
-   `wall_time_seconds`: float

## Data Flow

1.  **Ingestion**: `dataset_loader.py` reads the Parquet file and yields `Instance` objects.
2.  **Processing**: `run_eval.py` wraps instances in an `EvaluationRun` context and processes them.
3.  **Aggregation**: `Result` objects are collected and aggregated into summary JSONs and CSVs.

## Storage Format

-   **Intermediate**: JSON Lines (`.jsonl`) for streaming results during execution.
-   **Final Summary**: JSON (`.json`) for metrics.
-   **Cost Report**: CSV (`.csv`) for cost/rate analysis.
-   **Patches**: Individual `.diff` files in `results/patches/`.
