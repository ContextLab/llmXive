# Data Model: AutoResearchClaw Reproduction & Validation

## Overview

This document defines the data structures used by the `AutoResearchClaw` validation harness. The system is stateless between runs (except for the Evolution Log) and relies on file-based storage for configuration, logs, and artifacts. All data models are designed to be lightweight, JSON-serializable, and compatible with constrained RAM environments.

## Core Entities

### 1. ResearchCycle

Represents a single execution of the research loop on a specific topic.

*   **Fields**:
    *   `cycle_id` (string): Unique identifier (UUID).
    *   `topic` (string): The research topic (e.g., "B01: Effect of X on Y").
    *   `status` (enum): `running`, `completed`, `failed`, `timeout`.
    *   `start_time` (datetime): ISO 8601 timestamp.
    *   `end_time` (datetime): ISO 8601 timestamp (optional).
    *   `artifacts` (list of objects): List of generated files (path, type, size).
    *   `error_log` (list of objects): Errors encountered during this cycle.
    *   `hitl_interventions` (list of objects): Records of human feedback injected.

### 2. EvolutionLog

A persistent record of system failures and lessons learned across runs.

*   **Fields**:
    *   `entry_id` (string): Unique identifier.
    *   `timestamp` (datetime): ISO 8601.
    *   `error_type` (string): Categorized error (e.g., `ImportError`, `OOM`, `Timeout`).
    *   `error_trace` (string): Full traceback.
    *   `context` (object): Snapshot of system state (e.g., topic, current step).
    *   `lesson_learned` (string): Description of the fix or strategy change.
    *   `safeguard_applied` (string): The specific code change or configuration that prevented recurrence.

### 3. InterventionEvent

Records a Human-in-the-Loop interaction.

*   **Fields**:
    *   `event_id` (string): Unique identifier.
    *   `trigger_point` (string): The step where intervention occurred (e.g., `hypothesis_generation`).
    *   `feedback_payload` (object): The JSON input from the user.
    *   `system_response` (string): How the system adapted (e.g., "Revised hypothesis to...").
    *   `timestamp` (datetime): ISO 8601.
    *   `adherence_result` (boolean): **NEW** - Did the system follow the instruction? (Plan Adherence Metric).

### 4. MemorySnapshot

A record of memory usage at specific checkpoints.

*   **Fields**:
    *   `timestamp` (datetime): ISO 8601.
    *   `rss_mb` (float): Resident Set Size in MB.
    *   `action_taken` (string): `none`, `sampled_data`, `reduced_batch_size`, `aborted`.
    *   `threshold_mb` (float): The limit that triggered the action (e.g., 6000 MB).

### 5. InjectedFailureRegistry

**NEW**: A pre-defined list of known errors used to validate SC-005 (avoiding circularity).

*   **Fields**:
    *   `registry_id` (string): Unique identifier.
    *   `failure_mode` (string): The specific error type to inject (e.g., `ZeroDivisionError`).
    *   `expected_fix` (string): The expected safeguard/lesson.
    *   `test_run_id` (string): Link to the test run.
    *   `result` (boolean): Did the system avoid the failure?

## File Formats

### `evolution_log.json`

A JSON array of `EvolutionLog` entries.

```json
[
  {
    "entry_id": "ev-001",
    "timestamp": "2025-05-23T10:00:00Z",
    "error_type": "ImportError",
    "error_trace": "ModuleNotFoundError: No module named 'torch'",
    "context": { "topic": "B01", "step": "data_loading" },
    "lesson_learned": "Switched to numpy for matrix operations.",
    "safeguard_applied": "Added fallback to numpy in data_loader.py"
  }
]
```

### `cycle_state.json` (Checkpoint)

A temporary file saved at regular intervals to allow restart after timeout.

```json
{
  "cycle_id": "cycle-123",
  "topic": "B01",
  "current_step": "hypothesis_generation",
  "artifacts_generated": ["draft_hypothesis.md"],
  "memory_snapshot": { "rss_mb": 2500, "action_taken": "none" }
}
```

### `hitl_config.yaml`

Configuration for HITL intervention points.

```yaml
intervention_points:
  - step: "hypothesis_generation"
    trigger: "always"
    feedback_file: "feedback/hypothesis_feedback.json"
  - step: "experimental_design"
    trigger: "on_error"
    feedback_file: "feedback/design_feedback.json"
```

### `injected_failure_registry.json`

A pre-defined list of errors to test SC-005 against.

```json
[
  {
    "registry_id": "reg-001",
    "failure_mode": "ImportError",
    "expected_fix": "Fallback to numpy",
    "test_run_id": "run-456",
    "result": true
  }
]
```

## Data Flow

1.  **Start**: `runner.py` loads `topics.yaml`, `hitl_config.yaml`, and `injected_failure_registry.json`.
2.  **Loop**: For each topic, a `ResearchCycle` object is instantiated.
3.  **Execution**:
    *   `memory_guard.py` monitors RAM. If > 6 GB, it triggers `synthetic_generators` to sample data. It writes to `MemorySnapshot`.
    *   `error_healer.py` wraps code execution. If an error occurs, it logs to `EvolutionLog` and attempts a fix.
    *   `hitl_controller.py` checks for intervention points. If triggered, it pauses and loads feedback from `feedback_file`. It records `adherence_result` in `InterventionEvent`.
    *   `injected_failure_registry` is consulted to validate SC-005 (avoidance of known errors).
4.  **End**: Upon completion or failure, the `ResearchCycle` state is saved to `logs/cycle_<id>.json`.
5.  **Persistence**: `EvolutionLog` is updated with any new lessons learned.