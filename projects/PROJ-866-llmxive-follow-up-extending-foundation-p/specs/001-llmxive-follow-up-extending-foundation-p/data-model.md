# Data Model: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Overview

This document defines the data structures used in the simulation. All data is stored in JSON/CSV formats in `data/` and validated against YAML schemas in `contracts/`.

## Entities

### 1. Workflow
A directed graph representing a multi-agent task chain.
- **ID**: Unique string (UUID).
- **Depth**: Integer (1-20).
- **Complexity**: Integer (1-10).
- **Nodes**: List of nodes (Agent, Action, Policy).
- **Edges**: List of directed edges.
- **Metadata**: Seed used, generation timestamp.

### 2. ExecutionLog
Record of a single workflow run.
- **WorkflowID**: Reference to Workflow.
- **Mode**: "full" or "compressed".
- **CompressionDepth**: Integer (only for compressed mode).
- **TokenCount**: Integer (calculated via `tiktoken`).
- **ActualReductionPercent**: Float (0.0 to 1.0) - calculated as `(Full_Tokens - Compressed_Tokens) / Full_Tokens`.
- **Violations**: List of policy violation details.
- **ViolationCount**: Integer.
- **Timestamp**: ISO 8601.

### 3. AnalysisResult
Aggregated statistical output.
- **CompressionRatios**: Array of floats (observed reduction percentages).
- **ErrorRates**: Array of floats (observed error rates at those ratios).
- **RegressionCoefficients**: Dictionary of model parameters (from Logistic Regression).
- **Threshold**: Float (context reduction % at [deferred] error).
- **ConfidenceInterval**: [Lower, Upper].
- **Covariates**: List of controlled variables (Depth, Complexity).

## File Structure

```text
data/
├── raw/
│   └── workflows.json          # Generated synthetic workflows
├── processed/
│   ├── full_context_logs.json  # Baseline execution logs
│   └── compressed_context_logs.json # Compressed execution logs
└── results/
    └── tradeoff_analysis.json  # Final regression and threshold
```

## Schema Definitions

See `contracts/` for detailed YAML schemas.

- `contracts/workflow.schema.yaml`: Validates `data/raw/workflows.json`.
- `contracts/execution_log.schema.yaml`: Validates `data/processed/*.json`.
- `contracts/analysis_results.schema.yaml`: Validates `data/results/*.json`.

## Data Flow

1. **Generate**: `synthetic_workflow.py` -> `data/raw/workflows.json`.
2. **Execute Full**: `full_context.py` -> `data/processed/full_context_logs.json`.
3. **Execute Compressed**: `compressed_context.py` (loop over depths) -> `data/processed/compressed_context_logs.json`.
4. **Analyze**: `tradeoff_model.py` reads logs -> calculates **ActualReductionPercent** per workflow -> runs Logistic Regression -> `data/results/tradeoff_analysis.json`.
5. **Report**: Paper draws from `data/results/tradeoff_analysis.json`.

## Constraints

- **Immutability**: Raw data (`workflows.json`) is never modified.
- **Checksums**: All files in `data/` are checksummed in `state/`.
- **No PII**: Synthetic data contains no real identities.