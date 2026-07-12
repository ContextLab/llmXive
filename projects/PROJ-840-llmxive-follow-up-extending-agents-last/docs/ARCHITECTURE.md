# llmXive Automated Science Pipeline - Architecture Documentation

## System Overview

The llmXive Automated Science Pipeline is designed to analyze agent performance on the Agents' Last Exam (ALE) benchmark, classify failure modes, implement interventions, and provide statistically rigorous results.

## Design Principles

1. **Reproducibility**: All experiments use deterministic seed pinning and verification.
2. **Modularity**: Each user story is implemented as an independent, testable component.
3. **Scalability**: The pipeline can handle large-scale experiments with parallel execution.
4. **Transparency**: Comprehensive logging and detailed reporting of all processes.
5. **Compliance**: Adheres to FR-001 through FR-009 specifications.

## Component Architecture

### 1. Data Generation Layer

**Module**: `code/data/generator.py`

**Responsibilities**:
- Generate synthetic ALE execution traces with known ground truth
- Create task descriptions and step states
- Ensure strict pairing between tasks and seeds

**Key Functions**:
- `generate_task_description()`: Creates synthetic task descriptions
- `generate_step_state()`: Generates step-by-step state information
- `generate_trace()`: Combines descriptions and states into complete traces
- `main()`: Entry point for trace generation

**Data Flow**:
```
Seed Verification → Task Generation → State Generation → Trace Assembly → JSON Output
```

### 2. Classification Layer

**Modules**:
- `code/classification/parser.py`: Log parsing
- `code/classification/heuristics.py`: State normalization
- `code/classification/goal_validator.py`: Task goal validation
- `code/classification/state_validator.py`: State reconstruction validation
- `code/classification/semantic_classifier.py`: Failure mode classification

**Workflow**:
1. **Parsing**: Extract environment state and agent actions from ALE logs
2. **Normalization**: Apply deterministic normalization (1e-6 tolerance)
3. **Validation**: Check state reconstruction accuracy against golden subset
4. **Classification**: Use local LLM to classify failures as "State Persistence Error" or "Reasoning Deficit"

**FR Compliance**:
- FR-001: Normalization with 1e-6 tolerance
- FR-002: Deterministic seed pinning
- FR-007: Regex-based template matcher for goal validation
- FR-008: Seed verification throughout
- FR-009: State reconstruction accuracy threshold (≥95%)

### 3. Intervention Layer

**Modules**:
- `code/intervention/wrapper.py`: Context checkpointing wrapper
- `code/intervention/runner.py`: CPU-only task execution

**Functionality**:
- **Checkpointing**: Regenerate state summaries at configurable intervals (N)
- **Compression**: Two methods - truncation and abstraction
- **Execution**: Run tasks with and without intervention

**Key Features**:
- Configurable checkpoint interval
- Token count estimation
- Memory monitoring and timeout handling
- CPU-only inference with Q4_K_M quantization

### 4. Analysis Layer

**Modules**:
- `code/analysis/stats.py`: Statistical significance testing
- `code/analysis/sensitivity.py`: Sensitivity analysis
- `code/analysis/report_generator.py`: Report generation

**Statistical Methods**:
- **McNemar's Test**: Primary test for paired binary outcomes (FR-005)
- **Bonferroni Correction**: Multiple-comparison correction
- **FDR Correction**: Alternative correction method
- **Sensitivity Analysis**: Test N=1, N=3, N=5 (FR-006)

**Report Components**:
- Pass rates (baseline vs. intervention)
- P-values from McNemar's test
- Sensitivity analysis results
- Classification metrics

### 5. Utility Layer

**Modules**:
- `code/utils/config.py`: Configuration management
- `code/utils/seeds.py`: Seed pinning and verification
- `code/utils/logging_config.py`: Logging infrastructure

**Capabilities**:
- YAML-based configuration loading
- Deterministic seed generation and verification
- Memory usage monitoring
- Timeout tracking
- Structured logging

## Data Flow

```
┌─────────────────┐
│ Configuration │
│ (YAML Schema) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Seed Generation │
│ & Verification │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Data Generation │
│ (Synthetic) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Classification │
│ Pipeline │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Intervention │
│ Experiments │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Statistical │
│ Analysis │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Report │
│ Generation │
└─────────────────┘
```

## Configuration Schema

The pipeline uses a hierarchical YAML configuration:

```yaml
model_config:
 model_path: string
 quantization: string (Q4_K_M, etc.)
 max_tokens: integer
 temperature: float

checkpoint_config:
 interval: integer
 compression_method: string (truncation, abstraction)
 max_context_tokens: integer

logging_config:
 level: string
 output_file: string

data_paths:
 raw_data_dir: string
 processed_data_dir: string
 output_dir: string
```

## Error Handling

The pipeline implements robust error handling:

1. **Validation Errors**: Configuration validation before execution
2. **State Gates**: T013b halts pipeline if reconstruction accuracy < 95%
3. **Memory Limits**: Runtime monitoring with timeout handling
4. **Seed Verification**: Fails if pairing verification fails
5. **Logging**: Comprehensive error logging with stack traces

## Performance Considerations

- **Memory**: Target ≤7GB RAM usage
- **Time**: Maximum 6-hour execution per task
- **CPU**: Optimized for CPU-only inference
- **Parallelism**: Independent tasks can run in parallel

## Testing Strategy

1. **Unit Tests**: Individual function correctness
2. **Integration Tests**: End-to-end workflow validation
3. **Contract Tests**: API compliance verification
4. **Golden Set Tests**: Classification accuracy validation
5. **Sensitivity Tests**: Parameter variation analysis

## Deployment

The pipeline is designed for:
- Local development and testing
- Batch execution on compute clusters
- CI/CD integration for automated validation

## Future Enhancements

- Support for GPU acceleration
- Additional failure mode categories
- Extended sensitivity analysis
- Real-time monitoring dashboard
- Automated hyperparameter tuning

## References

- FR-001: Normalization tolerance specification
- FR-002: Deterministic seed pinning
- FR-003: Checkpoint interval configuration
- FR-004: CPU-only execution
- FR-005: McNemar's test requirement
- FR-006: Sensitivity analysis intervals
- FR-007: Regex-based goal validation
- FR-008: Seed verification
- FR-009: State reconstruction accuracy threshold
