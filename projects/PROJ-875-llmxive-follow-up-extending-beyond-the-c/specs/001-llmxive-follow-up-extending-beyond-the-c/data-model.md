# Data Model: llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

## Overview

This document defines the data structures used for state representation, agent interaction, and metric calculation. All data is derived from the RNG-Bench 3D Maze environment.

## Entities

### 1. GameInstance
Represents a specific maze configuration.
*   **Attributes**:
    *   `seed`: Integer (random seed).
    *   `dimensions`: Tuple (width, height, depth).
    *   `item_locations`: List of dicts (e.g., `{"type": "key", "pos": [x,y,z]}`).

### 2. StateSnapshot
The composite object passed to the agent at each step.
*   **Attributes**:
    *   `timestamp`: Integer (step index).
    *   `ascii_grid`: String (the visual grid rendered as text).
    *   `event_log`: List[JSON] (history of events).
    *   `ground_truth`: Dict (internal state variables, e.g., `{"key_location": [x,y,z], "door_open": False}`).
    *   `visible_items`: List[Dict] (items currently visible in `ascii_grid` or Visual frame, used for **masking**).

### 3. AgentResponse
The output from the LLM.
*   **Attributes**:
    *   `action`: String (e.g., "move_up").
    *   `mental_map`: String (the agent's internal description of the state).
    *   `mental_map_json`: Dict (parsed version of `mental_map` for structured comparison).

### 4. BaselineResponse
The output from the Baseline MLLM (Visual).
*   **Attributes**:
    *   `action`: String.
    *   `raw_output`: String (unstructured text or visual reasoning).
    *   `mental_map_json`: Dict (parsed version via `baseline_adapter.py` for structured comparison).

### 5. MetricResult
The final output of the scoring module.
*   **Attributes**:
    *   `run_id`: String (unique identifier).
    *   `step`: Integer.
    *   `memory_gap`: Float (calculated score).
    *   `components`: Dict (breakdown of structured diff and penalties).
    *   `is_valid`: Boolean.
    *   `masked_ground_truth`: Dict (the ground truth state **after** removing `visible_items`).
    *   `masking_validated`: Boolean (True if `validate_masking()` passed).

## Data Flow

1.  **Generator**: `GameInstance` -> `StateSnapshot` (ASCII + Ground Truth + Visible Items).
2.  **Agent**: `StateSnapshot` -> `AgentResponse`.
3.  **Baseline**: `GameInstance` (Visual) -> `BaselineResponse` (via `baseline_adapter.py`).
4.  **Scorer**:
    *   Input: `AgentResponse` (or `BaselineResponse`), `StateSnapshot.ground_truth`, `StateSnapshot.visible_items`.
    *   **Masking Step**: Filter `ground_truth` to remove items in `visible_items` -> `masked_ground_truth`.
    *   **Validation**: Call `validate_masking()` to ensure visible items are correctly excluded.
    *   **Comparison**: Compare `mental_map_json` against `masked_ground_truth` using Structured Diff + Semantic Similarity.
    *   Output: `MetricResult`.
5.  **Aggregator**: List[`MetricResult`] -> Statistical Summary (Mean, Median, P-value).

## Storage Strategy

*   **Raw Data**: `data/raw/` contains the seed definitions (JSON).
*   **Processed Data**: `data/processed/` contains:
    *   `runs/{run_id}/ascii_log.txt`: The full ASCII history.
    *   `runs/{run_id}/agent_log.json`: The full agent response history.
    *   `runs/{run_id}/baseline_log.json`: The full baseline response history (if applicable).
    *   `runs/{run_id}/scores.json`: The calculated Memory Gap scores.
*   **Checksums**: All files in `data/processed/` are checksummed (SHA-256) upon creation via `utils/checksum.py`.

## Validation Contracts

### `validate_masking()`
*   **Input**: `ground_truth`, `visible_items`, `masked_ground_truth`.
*   **Logic**: Assert that `masked_ground_truth` contains no items present in `visible_items`.
*   **Output**: Boolean (True if valid).
*   **Enforcement**: `scorer.py` must call this function before calculating the score. If it returns False, the run is marked invalid.