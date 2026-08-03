# API Reference

This document lists the public interfaces for the llmXive pipeline modules.

## `code/config.py`

**Public Names**: `ensure_directories`, `load_state`, `save_state`

- `ensure_directories()`: Creates all required data and state directories.
- `load_state()`: Loads the project state from the YAML file.
- `save_state(state: dict)`: Saves the project state to the YAML file.

## `code/generators/workflow_generator.py`

**Public Names**: `calculate_sha256`, `generate_workflow`, `validate_workflow_structure`, `generate_ground_truth_batch`, `verify_ground_truth_hashes`

- `calculate_sha256(file_path: str) -> str`: Calculates SHA256 hash of a file.
- `generate_workflow(seed: int, workflow_id: int) -> Dict`: Generates a single workflow.
- `validate_workflow_structure(workflow: Dict) -> bool`: Validates against schema.
- `generate_ground_truth_batch(count: int, seed: int) -> List`: Generates a batch of workflows.
- `verify_ground_truth_hashes() -> bool`: Verifies all ground truth files against stored hashes.

## `code/executors/`

### `base_executor.py`
**Public Names**: `ExecutionResult`, `BaseExecutor`
- `BaseExecutor`: Abstract base class for execution logic.

### `event_log_executor.py`
**Public Names**: `EventLogExecutor`
- `EventLogExecutor`: Executes workflows using fragmented event logging.

### `session_first_executor.py`
**Public Names**: `SessionFirstExecutor`
- `SessionFirstExecutor`: Executes workflows using atomic session-first recording.

## `code/simulators/corruption_injector.py`

**Public Names**: `CorruptionInjector`, `main`

- `CorruptionInjector`: Class responsible for injecting corruption into logs.
- `main()`: Entry point for running the injector.

## `code/reconstructors/reconstruction_engine.py`

**Public Names**: `ReconstructionEngine` (implied)
- Parses corrupted logs and reconstructs state.

## `code/analyzers/`

### `metrics_calculator.py`
**Public Names**: `MetricsCalculator` (implied)
- Calculates Total Resilience, Fidelity, and Latency.

### `statistical_test.py`
**Public Names**: `cochran_q_test`, `mcnemar_test`, `paired_t_test` (implied)
- Performs statistical comparisons.

## `code/utils/checksum_manager.py`

**Public Names**: `calculate_sha256`, `scan_directory_for_files`, `update_artifact_hashes`

- `scan_directory_for_files(directory: str) -> List[str]`: Lists files in a directory.
- `update_artifact_hashes()`: Updates the project state with current file hashes.
