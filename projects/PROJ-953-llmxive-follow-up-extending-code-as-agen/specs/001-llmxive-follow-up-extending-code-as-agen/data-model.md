# Data Model: llmXive follow-up: extending "Code as Agent Harness"

## Overview

This document defines the data structures used throughout the pipeline, ensuring consistency between ingestion, feature extraction, and modeling. All data is stored in CSV (tabular) or JSON (graph) formats.

## Entities

### 1. TaskArtifact
Represents a single agent task instance.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `task_id` | string | Unique identifier (e.g., `swe-bench-1234`) | Dataset ID |
| `dataset_name` | string | Source dataset (e.g., `swe-bench-verified`) | Metadata |
| `code_diff` | string | The code modification patch | Dataset `patch` |
| `original_code` | string | The baseline code before modification | Dataset context |
| `dynamic_execution_outcome` | string | "Pass", "Fail", or "Timeout/Fail" | Baseline Execution |
| `failure_type` | string | "logic", "environmental", or null | Derived from execution logs |
| `is_unparseable` | boolean | True if `tree-sitter` failed | Feature Extraction |
| `parse_error_msg` | string | Error message if unparseable, else null | Feature Extraction |

### 2. StructuralMetric
Derived features for a `TaskArtifact`.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `task_id` | string | Foreign key to `TaskArtifact` | Link |
| `dependency_depth` | integer | Max depth of the dependency graph | `tree-sitter`/`networkx` |
| `cyclomatic_complexity` | integer | McCabe complexity score | `radon`/`tree-sitter` |
| `semantic_complexity_score` | float | Normalized score based on node types | `tree-sitter` |
| `lines_of_code` | integer | Total lines in the diff | Simple count |
| `node_count` | integer | Total nodes in dependency graph | `networkx` |
| `edge_count` | integer | Total edges in dependency graph | `networkx` |

### 3. ModelOutcome
Results from the predictive modeling phase.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `model_id` | string | Identifier for the model run (e.g., `lr-v1`) | Metadata |
| `threshold` | float | Decision boundary probability | Analysis |
| `predicted_label` | string | "Static_Safe" or "Dynamic_Required" | Model Prediction |
| `actual_label` | string | "Pass" or "Fail" | Ground Truth |
| `is_false_negative` | boolean | True if predicted Safe but actual Fail | Derived |
| `confidence_score` | float | Model probability | Model Output |

## Data Flow

1. **Raw Data** (Parquet) → **Ingestion Script** → `TaskArtifact` (CSV)
2. `TaskArtifact` → **Feature Script** → `StructuralMetric` (CSV) + Graph Files (**JSON**)
3. `TaskArtifact` + `StructuralMetric` → **Training Script** → `ModelOutcome` (CSV) + `Model.pkl`

**Note on Graph Format**: Dependency graphs are serialized as **JSON** (using `networkx`'s `write_graphml_json` or similar) to ensure text-based traceability and avoid pickle ambiguity, satisfying Constitution Principle VII.

## Constraints

- **Immutability**: Raw data files in `data/raw/` are never modified.
- **Checksums**: All files in `data/` must have a corresponding `.sha256` hash file.
- **No PII**: No user-specific identifiers are stored; only dataset IDs.