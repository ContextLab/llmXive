# Data Model: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## Overview

This document defines the data structures used throughout the pipeline, from raw dataset ingestion to final statistical reporting. All data is stored in `data/` and processed via scripts in `code/`.

## Entities

### 1. RawTask
Represents a single entry from the Multi-LCB dataset.
*   `task_id` (str): Unique identifier.
*   `problem_statement` (str): Natural language description.
*   `python_solution` (str): Ground-truth Python code (source for Logic Anchor).
*   `target_language` (str): e.g., "rust", "kotlin".
*   `target_solution` (str): Ground-truth code in target language (for verification).
*   `test_cases` (list[dict]): Input/output pairs for sandbox execution.
*   `difficulty` (str): "Easy", "Medium", "Hard".
*   `topic` (str): e.g., "DP", "Graphs", "Math".

### 2. LogicAnchor
Derived from `RawTask.python_solution`.
*   `task_id` (str): Link to source task.
*   `steps` (list[str]): List of 3 distinct algorithmic steps (pseudo-code or Python).
*   `extraction_method` (str): "AST", "Manual", "Fallback".
*   `status` (str): "Success", "Failed".

### 3. GenerationResult
Output of the inference and execution pipeline.
*   `task_id` (str): Link to source task.
*   `condition` (str): "blind" or "guided".
*   `model_output` (str): Generated code string.
*   `execution_status` (str): "Pass", "Fail", "Timeout", "CompileError".
*   `error_type` (str): "Syntax", "Library", "Runtime", "LogicTransfer", "None".
*   `anchor_verification` (bool): True if generated code implements all 3 anchor steps (only checked for "Pass" cases to detect Logic Transfer).
*   `latency_ms` (int): Time taken for generation + execution.

### 4. StatisticalReport
Aggregated results.
*   `total_tasks` (int): Number of tasks in final set.
*   `pass_rate_blind` (float): Pass@1 for blind condition.
*   `pass_rate_guided` (float): Pass@1 for guided condition.
*   `improvement` (float): `pass_rate_guided - pass_rate_blind`.
*   `p_value` (float): Result of McNemar's test.
*   `significance` (bool): True if p < 0.05.
*   `error_distribution` (dict): Counts of each `error_type` in guided condition.
*   `stratification_stats` (dict): Pass rates per Difficulty/Topic.

## Data Flow

1.  **Ingestion**: `datasets.load_dataset(...)` -> `RawTask` objects (stored as `data/raw/lcb.parquet`).
2.  **Filtering**: `RawTask` -> `FilteredTask` (n=200, stratified).
3.  **Anchor Extraction**: `FilteredTask` -> `LogicAnchor` (stored as `data/processed/anchors.jsonl`).
4.  **Inference & Execution**: `FilteredTask` + `LogicAnchor` -> `GenerationResult` (stored as `data/results/generations.csv`).
5.  **Analysis**: `GenerationResult` -> `StatisticalReport` (stored as `data/results/stats.yaml`).

## Assumptions & Constraints

*   **Storage**: All intermediate files are text-based (JSONL, CSV, YAML) to minimize size and ensure reproducibility.
*   **Memory**: `RawTask` is loaded in chunks; `GenerationResult` is appended incrementally to CSV to avoid memory spikes.
*   **Checksums**: `data/raw/` files are checksummed upon download. `data/processed/` and `data/results/` are checksummed upon generation.
