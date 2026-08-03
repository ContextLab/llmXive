# Architecture Documentation

## System Overview

The llmXive pipeline is designed to simulate, execute, and analyze multi-agent workflows under varying conditions of data corruption and network latency. It compares two distinct state management architectures: **Event-Log** and **Session-First**.

## Component Breakdown

### 1. Generators (`code/generators/`)
Responsible for creating synthetic, deterministic workflows.
- **`workflow_generator.py`**:
 - Generates `WorkflowDefinition` objects containing tool calls, decision trees, and expected outputs.
 - Produces `GroundTruth` JSON files containing the immutable final state.
 - Uses `config.SEED` for full reproducibility.
- **`schemas.py`**: Defines Pydantic models for validation.

### 2. Executors (`code/executors/`)
Simulates the runtime environment of the agents.
- **`base_executor.py`**: Abstract base class defining the `execute()` interface.
- **`event_log_executor.py`**:
 - **Pattern**: Asynchronous, fragmented storage.
 - **Behavior**: Writes transcripts, snapshots, and outputs to separate files.
 - **Jitter**: Injects stochastic delays in `tool_call()`.
- **`session_first_executor.py`**:
 - **Pattern**: Atomic, single-object state recording.
 - **Behavior**: Uses write-to-temp-then-rename for atomicity.
 - **Jitter**: Injects stochastic delays in `tool_call()`.

### 3. Simulators (`code/simulators/`)
Introduces faults into the system.
- **`corruption_injector.py`**:
 - Randomly selects log entries to delete or modify based on `CORRUPTION_RATE`.
 - **Exclusion**: Never corrupts files in `data/raw/workflows/`.
 - **Logging**: Records all corruption events in `data/processed/corruption_map.json`.
- **`corruption_log_manager.py`**: Manages the central corruption map (Single Source of Truth).

### 4. Reconstructors (`code/reconstructors/`)
Attempts to rebuild the final state from corrupted traces.
- **`reconstruction_engine.py`**:
 - Parses corrupted logs.
 - Traverses the decision tree to detect missing dependencies.
 - **Unrecoverable Logic**: If a critical node is missing, marks workflow as `Unrecoverable` rather than crashing.

### 5. Analyzers (`code/analyzers/`)
Calculates metrics and performs statistical tests.
- **`metrics_calculator.py`**:
 - Computes **Total Resilience** (Success/Total).
 - Computes **Recoverable State Fidelity** (Success/Recoverable).
 - Computes **Unrecoverable Rate**.
 - Measures **Replay Latency**.
- **`statistical_test.py`**:
 - **Cochran's Q**: Primary test for multi-factor design.
 - **McNemar's Test**: Post-hoc pairwise comparisons.
 - **Latency Test**: Paired t-test / Wilcoxon.

### 6. Orchestration (`code/main.py`)
The central entry point.
- **CLI**: Handles `--seed`, `--count`, `--resume`, `--corruption-rate`, `--sweep`.
- **Flow**:
 1. Load/Save checkpoints for resilience.
 2. Iterate through `SWEEP_RATES`.
 3. Execute Generation -> Simulation -> Reconstruction.
 4. Aggregate results.
 5. Update checksums in the state YAML.

## Data Flow

1. **Generation**: `main.py` -> `workflow_generator.py` -> `data/raw/workflows/`
2. **Simulation**: `corruption_injector.py` -> `executors` -> `data/processed/corrupted_logs/`
3. **Reconstruction**: `reconstruction_engine.py` -> `data/processed/results/`
4. **Analysis**: `metrics_calculator.py` -> `data/processed/results/aggregated_metrics.json`
5. **Hygiene**: `checksum_manager.py` -> `state/projects/...yaml`

## Error Handling Strategy

- **Graceful Degradation**: If a log entry is missing, the reconstruction engine marks the workflow as `Unrecoverable` and records the specific missing dependency. It does **not** raise `FileNotFoundError`.
- **Fail Loudly**: If a real data source cannot be fetched (for external datasets), the loader raises an exception. No synthetic fallbacks are permitted.
- **Checkpointing**: The system supports resuming from the last completed workflow ID if the process is interrupted.
