# API Reference

This document describes the public interfaces of the core modules.

## `code/config.py`

Configuration and state management.

```python
from config import ensure_directories, load_state, save_state, SEED, CORRUPTION_RATE, SWEEP_RATES
```

- `ensure_directories()`: Creates all required `data/`, `code/`, `state/` directories.
- `load_state()`: Loads the project YAML state file.
- `save_state(state: dict)`: Saves the project YAML state file.
- `SEED`: Default random seed (42).
- `CORRUPTION_RATE`: Default corruption probability (0.1).
- `SWEEP_RATES`: List of rates to test `[0.05, 0.10, 0.20]`.

## `code/generators/workflow_generator.py`

Workflow generation and validation.

```python
from generators.workflow_generator import (
 calculate_sha256,
 generate_workflow,
 validate_workflow_structure,
 generate_ground_truth_batch,
 verify_ground_truth_hashes
)
```

- `calculate_sha256(filepath: str) -> str`: Calculates SHA256 hash of a file.
- `generate_workflow(seed: int, workflow_id: int) -> Dict`: Generates a single workflow definition.
- `validate_workflow_structure(workflow: Dict) -> bool`: Validates against the schema.
- `generate_ground_truth_batch(seed: int, count: int) -> List[Dict]`: Generates a batch of workflows and ground truths.
- `verify_ground_truth_hashes()`: Verifies all ground truth files match their recorded hashes.

## `code/executors/base_executor.py`

Abstract base for execution engines.

```python
from executors.base_executor import ExecutionResult, BaseExecutor
```

- `ExecutionResult`: Dataclass containing `success`, `state`, `latency`, `errors`.
- `BaseExecutor`: Abstract class defining `execute(workflow: Dict) -> ExecutionResult`.

## `code/executors/event_log_executor.py`

Event-Log architecture implementation.

```python
from executors.event_log_executor import EventLogExecutor
```

- `EventLogExecutor`: Implements fragmented storage and jitter injection.
- `tool_call(tool_name: str, params: Dict)`: Injects `time.sleep` for jitter.

## `code/executors/session_first_executor.py`

Session-First architecture implementation.

```python
from executors.session_first_executor import SessionFirstExecutor
```

- `SessionFirstExecutor`: Implements atomic state recording.
- `tool_call(tool_name: str, params: Dict)`: Injects `time.sleep` for jitter.

## `code/simulators/corruption_injector.py`

Fault injection logic.

```python
from simulators.corruption_injector import CorruptionInjector, main
```

- `CorruptionInjector`: Class managing corruption logic.
 - `inject_corruption(log_files: List[str], rate: float) -> Dict`: Returns a map of corrupted files.
- `main()`: Entry point for running the injector as a script.

## `code/simulators/corruption_log_manager.py`

Central corruption map management.

```python
from simulators.corruption_log_manager import (
 get_corruption_map_path,
 load_corruption_map,
 save_corruption_map,
 mark_workflow_corrupted,
 is_workflow_corrupted,
 get_corruption_details
)
```

- `mark_workflow_corrupted(workflow_id: str, details: Dict)`: Adds an entry to the map.
- `is_workflow_corrupted(workflow_id: str) -> bool`: Checks status.
- `get_corruption_details(workflow_id: str) -> Dict`: Returns specific corruption data.

## `code/reconstructors/reconstruction_engine.py`

State reconstruction logic.

```python
from reconstructors.reconstruction_engine import ReconstructionEngine
```

- `ReconstructionEngine`: Main class for reconstruction.
- `reconstruct(workflow_id: str, corrupted_logs: Dict) -> Dict`: Returns reconstruction result including `success`, `state`, `latency`.

## `code/analyzers/metrics_calculator.py`

Metric calculation.

```python
from analyzers.metrics_calculator import MetricsCalculator
```

- `MetricsCalculator`: Aggregates results.
- `calculate_total_resilience(results: List[Dict]) -> float`: Success / Total.
- `calculate_recoverable_fidelity(results: List[Dict]) -> float`: Success / Recoverable.
- `calculate_unrecoverable_rate(results: List[Dict]) -> float`: Unrecoverable / Total.

## `code/analyzers/statistical_test.py`

Statistical analysis.

```python
from analyzers.statistical_test import StatisticalTest
```

- `StatisticalTest`: Handles statistical tests.
- `run_cochrans_q(results: Dict)`: Runs Cochran's Q test.
- `run_mcnemar(results: Dict)`: Runs McNemar's test with Holm-Bonferroni.
- `run_latency_test(results: Dict)`: Runs Paired t-test / Wilcoxon.

## `code/main.py`

Orchestration entry point.

```python
from main import main
```

- `main()`: Parses arguments and runs the pipeline.
- Arguments:
 - `--seed`: Random seed.
 - `--count`: Number of workflows.
 - `--resume`: Resume from checkpoint.
 - `--corruption-rate`: Corruption probability.
 - `--sweep`: Run full sweep over `SWEEP_RATES`.
