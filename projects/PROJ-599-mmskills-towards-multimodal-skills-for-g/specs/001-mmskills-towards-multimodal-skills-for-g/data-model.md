# Data Model: MMSkills Reproduction & Validation

## 1. Overview
This document defines the data structures used for skill packages, agent actions, and evaluation metrics. These structures are validated against the schemas defined in `contracts/`.

## 2. Skill Package Structure

A **Skill Package** is a directory containing the procedural knowledge for a specific task.

### 2.1. Directory Layout
```text
skills_library/<domain>/<skill_name>/
├── plan.json
├── state_cards.json
├── runtime_state_cards.json
├── grounding_audit.json
├── IMAGE_REFERENCE_LIST.md
└── Images/
    ├── step_01.png
    ├── step_02.png
    └── ...
```

### 2.2. Data Definitions

#### `plan.json`
Defines the sequence of steps for the agent to execute.
*   **Fields**:
    *   `skill_id`: Unique identifier for the skill.
    *   `description`: Natural language description of the task.
    *   `steps`: List of step objects.
        *   `step_id`: Integer index.
        *   `action_type`: e.g., "click", "type", "scroll".
        *   `parameters`: Dictionary of action parameters (e.g., `{"coordinate": [x, y]}`).
        *   `expected_image`: Filename of the expected state image.

#### `state_cards.json`
Contains the initial state and expected intermediate states.
*   **Fields**:
    *   `initial_state`: Description of the starting environment.
    *   `expected_states`: List of expected states after each step.

#### `IMAGE_REFERENCE_LIST.md`
A text file listing all image files referenced in the skill package.
*   **Format**: One filename per line (e.g., `Images/step_01.png`).

## 3. Agent Action

An **Agent Action** is the output of the agent for a single step.

*   **Structure**:
    ```json
    {
      "action": "click",
      "coordinate": [100, 200],
      "step_id": 1,
      "timestamp": "2024-05-21T12:00:00Z"
    }
    ```

## 4. Evaluation Metrics

The **Evaluation Metric** record is generated for each task execution.

*   **Structure**:
    *   `task_id`: String, unique identifier for the task.
    *   `status`: Enum ["success", "fail", "timeout", "error", "partial_success"].
        *   `success`: All steps executed without critical errors.
        *   `fail`: Critical logic error occurred.
        *   `timeout`: Task exceeded 1800s limit.
        *   `error`: Runtime exception occurred.
        *   `partial_success`: Task completed but with non-critical errors (e.g., missing images logged in `asset_error_count`).
    *   `duration_seconds`: Float, time taken to complete the task.
    *   `peak_memory_mb`: Float, peak RSS memory usage in MB (measured via `psutil`). **Required for SC-004**.
    *   `asset_error_count`: Integer, number of missing or corrupted image files detected for this task (0 if none). **Required for SC-005**.
    *   `error_message`: String, error details if status is not "success" or "partial_success".
    *   `skill_id`: String, the skill package used.

**Mapping to Requirements**:
*   **Graceful Degradation (FR-007)**: If an asset is missing, the system logs a warning, increments `asset_error_count`, and marks the *step* as "ERROR". The *task* status is set to `partial_success` (if the task continues) or `success` (if the missing asset is non-critical), ensuring the task does not crash. This mapping ensures the high-level strategy aligns with the detailed data model.
*   **Timeout (FR-005)**: If a task exceeds 1800s, `status` is set to "timeout".

## 5. Data Flow

1.  **Load**: `loader.py` reads `plan.json` and `IMAGE_REFERENCE_LIST.md`.
2.  **Validate**: `loader.py` checks file existence and JSON schema. **If missing, increments `asset_error_count`**.
3.  **Execute**: `agent.py` processes steps and generates `Agent Action`.
4.  **Profile**: `utils.py` records `peak_memory_mb` using `psutil`.
5.  **Log**: `evaluator.py` records `Evaluation Metric` to `metrics_summary.csv`.