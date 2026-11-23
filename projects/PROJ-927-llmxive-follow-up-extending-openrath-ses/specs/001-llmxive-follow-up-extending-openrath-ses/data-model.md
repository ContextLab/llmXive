# Data Model: 001-session-first-reconstruction

## Overview

This document defines the data structures, file formats, and schemas used in the project. All data is stored as JSON for portability and human readability, with strict validation via Pydantic models and YAML schemas.

## Directory Structure

```text
data/
├── raw/
│   └── workflows/           # Ground truth workflow definitions and states
│       └── {workflow_id}_ground_truth.json
├── processed/
│   ├── corrupted_logs/      # Log artifacts with injected corruption
│   │   └── {workflow_id}_{architecture}_{corruption_rate}_logs.json
│   └── reconstruction_results/
│       └── {workflow_id}_{architecture}_result.json
└── results/
    └── aggregated_metrics.json
```

## Entity Definitions

### 1. Workflow Definition (Ground Truth)

**File**: `data/raw/workflows/{workflow_id}_ground_truth.json`  
**Purpose**: Immutable record of the generated workflow, decision tree, and expected final state.

**Schema Fields**:
- `workflow_id`: Unique string identifier (UUID).
- `seed`: Integer seed used for generation.
- `decision_tree`: Nested object describing the logic flow and tool calls.
- `final_state`: Dictionary of the expected final state variables.
- `tool_outputs`: List of expected outputs from each tool call.
- `hash`: SHA256 checksum of the file content.

### 2. Corruption Log

**File**: `data/processed/corruption_logs/{workflow_id}_{arch}_{rate}_logs.json`  
**Purpose**: Records of which log entries were corrupted (modified/deleted) and the resulting log content.

**Schema Fields**:
- `workflow_id`: Reference to the ground truth.
- `architecture`: "event_log" or "session_first".
- `corruption_rate`: Float (e.g., 0.10).
- `corruption_map`: List of objects mapping `log_id` -> `status` ("deleted", "modified", "intact").
- `corrupted_content`: List of modified log entries (if "modified").
- `hash`: SHA256 checksum.

### 3. Reconstruction Result

**File**: `data/processed/reconstruction_results/{workflow_id}_{arch}_result.json`  
**Purpose**: Output of the reconstruction engine, including success status and latency.

**Schema Fields**:
- `workflow_id`: Reference.
- `architecture`: "event_log" or "session_first".
- `status`: "Success", "Partial", or "Unrecoverable".
- `reconstructed_state`: The state rebuilt from logs.
- `latency_seconds`: Float time taken to reconstruct.
- `unrecoverable_reason`: String explanation if status is "Unrecoverable".
- `match_hash`: SHA256 of `reconstructed_state` compared to `final_state`.
- `is_exact_match`: Boolean (True if `match_hash` equals ground truth hash).
- `is_total_resilience_success`: Boolean (True if `status` is "Success", False otherwise).

### 4. Aggregated Metrics

**File**: `data/results/aggregated_metrics.json`  
**Purpose**: Summary statistics for the entire experiment.

**Schema Fields**:
- `experiment_id`: Unique run ID.
- `summary`: Object containing:
  - `total_workflows`: Integer.
  - `success_count`: Integer.
  - `unrecoverable_count`: Integer.
  - `total_resilience_rate`: Float (Success / Total).
  - `recoverable_fidelity_rate`: Float (Success / (Total - Unrecoverable)).
  - `avg_latency`: Float.
- `statistical_test`: Object containing:
  - `test_type`: "Cochran's Q".
  - `p_value`: Float.
  - `corrected_p_value`: Float (if multiple tests).
  - `significance`: Boolean.
  - `post_hoc_tests`: List of pairwise McNemar results with Holm-Bonferroni correction.

## Checksum & Hygiene Protocol

- **Generation**: Every file written to `data/` is immediately checksummed (SHA256).
- **Registration**: The `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml` file is updated with the `artifact_hashes` map:
  ```yaml
  artifact_hashes:
    "data/raw/workflows/abc123_ground_truth.json": "sha256:..."
    "data/processed/corrupted_logs/abc123_event_log_0.10_logs.json": "sha256:..."
  ```
- **Verification**: Before any analysis, the `main.py` script verifies that the current file hashes match the registered ones. Mismatches trigger a re-generation or error.