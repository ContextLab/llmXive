# Architecture Documentation: llmXive Pipeline

## System Overview

The llmXive pipeline implements a scientific research framework for comparing two architectural approaches to managing agent runtime state:

1. **Event-Log Architecture (Baseline)**: Traditional approach with asynchronous, fragmented storage
2. **Session-First Architecture (Experimental)**: Modern approach with atomic, single-object state recording

## Component Architecture

### 1. Workflow Generator (`code/generators/`)

**Responsibilities**:
- Generate deterministic multi-agent debugging workflows
- Create ground truth states with complete decision trees
- Validate workflow structure against schema
- Calculate and verify SHA256 hashes

**Key Classes**:
- `generate_workflow()`: Creates a single workflow with tool outputs and decision trees
- `generate_ground_truth_batch()`: Generates multiple workflows with checkpointing
- `validate_workflow_structure()`: Validates against JSON schema
- `verify_ground_truth_hashes()`: Ensures integrity of stored ground truth

**Data Flow**:
```
Random Seed → Workflow Definition → Ground Truth JSON → SHA256 Hash
```

### 2. Executors (`code/executors/`)

**Base Executor** (`base_executor.py`):
- Abstract base class defining the execution interface
- Handles common execution logic and error handling
- Defines `ExecutionResult` dataclass

**Event-Log Executor** (`event_log_executor.py`):
- Implements asynchronous, fragmented storage
- Stores transcripts, snapshots, and outputs as separate files
- Injects stochastic network jitter in `tool_call()` method
- Records jitter duration for metric distinction

**Session-First Executor** (`session_first_executor.py`):
- Implements atomic, single-object state recording
- Uses write-to-temp-then-rename pattern for data integrity
- Injects stochastic network jitter in `tool_call()` method
- Records jitter duration for metric distinction

**Execution Flow**:
```
Workflow Definition → Executor → Architecture-Specific Storage → Logs/States
```

### 3. Corruption Simulator (`code/simulators/`)

**Corruption Injector** (`corruption_injector.py`):
- Randomly selects and modifies/deletes log entries
- Configurable corruption rate (default: 0.1)
- Creates central corruption map (`data/processed/corruption_map.json`)
- Validates corruption against schema before writing

**Corruption Log Manager** (`corruption_log_manager.py`):
- Centralized management of corruption state
- Functions: `mark_workflow_corrupted`, `is_workflow_corrupted`, `get_corruption_details`
- Single source of truth for corruption status

**Corruption Flow**:
```
Clean Logs → Corruption Injector → Corrupted Logs + Corruption Map
```

### 4. Reconstruction Engine (`code/reconstructors/`)

**Reconstruction Engine** (`reconstruction_engine.py`):
- Parses corrupted logs to rebuild state and decision trees
- Handles unrecoverable workflows gracefully
- Calculates success/failure status

**Reconstruction Flow**:
```
Corrupted Logs → Parser → Reconstructed State → Comparison with Ground Truth
```

### 5. Analyzer (`code/analyzers/`)

**Metrics Calculator** (`metrics_calculator.py`):
- Calculates Total Resilience (Success/Total)
- Calculates Recoverable State Fidelity (Success/Recoverable)
- Calculates Unrecoverable Rate (Unrecoverable/Total)
- Measures Replay Latency
- Aggregates results into `aggregated_metrics.json`

**Statistical Tests** (`statistical_test.py`):
- **Cochran's Q Test**: Primary test for 2x2x3 design (Architecture × Outcome × Corruption Rate)
- **McNemar's Test**: Post-hoc pairwise comparisons with Holm-Bonferroni correction
- **Paired t-test/Wilcoxon**: Latency comparison between architectures
- **Fallback Logic**: Monte Carlo simulation for small N contingency tables

**Analysis Flow**:
```
Reconstruction Results → Metrics Calculation → Statistical Tests → Final Report
```

### 6. Orchestration (`code/main.py`)

**Responsibilities**:
- CLI argument parsing
- Checkpoint management (save/load state)
- Pipeline execution flow
- Sweep logic for corruption rates
- Timeout handling

**Execution Flow**:
```
CLI Args → Load Checkpoint → Generate → Execute → Corrupt → Reconstruct → Analyze → Save Results
```

## Data Models

### Workflow Definition
```json
{
 "workflow_id": "uuid",
 "seed": 42,
 "agents": [...],
 "tools": [...],
 "decision_tree": {
 "nodes": [...],
 "edges": [...]
 },
 "ground_truth": {
 "final_state": {...},
 "snapshots": [...]
 }
}
```

### Corruption Map
```json
{
 "workflow_id": {
 "is_corrupted": true,
 "corrupted_entries": [...],
 "corruption_type": "deletion|modification",
 "timestamp": "ISO8601"
 }
}
```

### Reconstruction Result
```json
{
 "workflow_id": "uuid",
 "success": true,
 "reconstructed_state": {...},
 "fidelity_score": 0.95,
 "latency_ms": 150,
 "unrecoverable": false
}
```

### Aggregated Metrics
```json
{
 "total_workflows": 500,
 "total_resilience": 0.85,
 "recoverable_fidelity": 0.92,
 "unrecoverable_rate": 0.15,
 "cochran_q_p_value": 0.03,
 "mcnemar_results": [...],
 "latency_comparison": {...}
}
```

## Design Principles

### 1. Determinism
- All random number generators seeded explicitly
- Reproducible results with same seed
- Checkpointing for long-running processes

### 2. Data Integrity
- SHA256 hashes for all artifacts
- Write-to-temp-then-rename pattern
- Central corruption map as single source of truth

### 3. Modularity
- Independent user stories
- Clear separation of concerns
- Testable components

### 4. Statistical Rigor
- Primary metric: Total Resilience
- Secondary metrics: Fidelity, Unrecoverable Rate
- Appropriate statistical tests with corrections

### 5. Performance
- Batched processing for large datasets
- Streaming for memory efficiency
- Optimized for < 6h runtime, < 4GB RAM

## Error Handling

### Unrecoverable Workflows
- Detected via corruption map and decision tree analysis
- Excluded from fidelity calculations
- Flagged as failures in total resilience

### Network Jitter
- Recorded separately from reconstruction overhead
- Injected only in `tool_call()` methods
- Distinguishable in metrics

### Small Sample Sizes
- Fallback to Monte Carlo simulation
- Configurable repetition count
- Honest reporting of limitations

## Extension Points

### New Architectures
- Implement `BaseExecutor` interface
- Add architecture-specific storage logic
- Register in main pipeline

### New Metrics
- Extend `metrics_calculator.py`
- Add to `aggregated_metrics.json` schema
- Update statistical tests if needed

### New Corruption Types
- Extend `corruption_injector.py`
- Update corruption map schema
- Adjust detection logic in reconstruction

## Security Considerations

- No external network calls (all data generated locally)
- Read-only ground truth files (immutability checks)
- Checksum verification for all artifacts
- Isolated execution environments

## Performance Characteristics

### Time Complexity
- Workflow Generation: O(n) where n = workflow count
- Execution: O(n × m) where m = steps per workflow
- Reconstruction: O(n × m)
- Analysis: O(n)

### Space Complexity
- Ground Truth: O(n × s) where s = state size
- Logs: O(n × m × l) where l = log entry size
- Results: O(n)

### Optimization Strategies
- Streaming for large datasets
- Batched processing
- Parallel execution (where applicable)
- Memory-efficient data structures
