# Data Model: llmXive Harness Extension

This document defines the data flow, schema definitions, and artifact relationships for the llmXive automated science pipeline. It serves as the central reference for the `contracts/` schemas and the `data/` directory structure.

## 1. Data Flow Overview

The pipeline processes software engineering tasks through three main phases: Ingestion, Feature Extraction, and Modeling.

1. **Ingestion (US1)**: Raw tasks are fetched from HuggingFace (SWE-bench, AgentBench), parsed, and stored as Parquet files. Ground truth is generated via dynamic execution.
2. **Feature Extraction (US2)**: Code artifacts are parsed using `tree-sitter` to generate dependency graphs and calculate structural metrics.
3. **Modeling (US3)**: Features and ground truth are combined to train predictive models and determine decision boundaries.

### High-Level Flow

```mermaid
graph TD
 A[Raw Datasets: SWE-bench/AgentBench] -->|HuggingFace API| B(ingest.py)
 B --> C[data/raw/*.parquet]
 C -->|Baseline Execution| D[baseline_runner.py]
 D --> E[data/processed/raw_outcomes.json]
 E -->|Merge| F[generate_ground_truth.py]
 F --> G[data/processed/ground_truth.csv]
 G -->|Filter Unparseable| H(extract_features.py)
 H --> I[data/graphs/{task_id}.json]
 H --> J[data/processed/features.csv]
 J --> K[train_model.py]
 K --> L[models/*.pkl]
 K --> M[data/processed/threshold_sweep.json]
 K --> N[data/processed/model_report.json]
```

## 2. Directory Structure & Artifacts

The project adheres to the following directory conventions:

- `data/raw/`: Raw ingested data (Parquet) and logs.
- `data/processed/`: Cleaned, merged, and feature-engineered data (CSV, JSON).
- `data/graphs/`: Serialized dependency graphs (JSON).
- `data/logs/`: Execution logs, sampling justifications, and audit reports.
- `models/`: Trained model artifacts (Pickle).
- `contracts/`: YAML schemas for validation.
- `state/`: Pipeline execution state (YAML).

## 3. Schema Definitions

All data artifacts must conform to the schemas defined in `contracts/`. These schemas are enforced via `jsonschema` or custom validators in the scripts.

### 3.1 Structural Metric Schema

**File**: `contracts/structural_metric.schema.yaml`

Defines the structure of feature records. Key constraint: `semantic_complexity_score` is optional; if missing, fallback metrics (`lines_of_code`) must be present.

```yaml
type: object
properties:
 task_id:
 type: string
 code_diff:
 type: string
 dependency_depth:
 type: integer
 minimum: 0
 cyclomatic_complexity:
 type: integer
 minimum: 1
 semantic_complexity_score:
 type: number
 minimum: 0
 description: "Optional. Computed only if semantic nodes are present."
 lines_of_code:
 type: integer
 minimum: 0
 description: "Required fallback metric when semantic nodes are missing."
 status:
 type: string
 enum: ["Success", "Unparseable"]
required:
 - task_id
 - code_diff
 - dependency_depth
 - cyclomatic_complexity
 - status
# Conditional logic enforced by validator:
# if 'semantic_complexity_score' is missing, 'lines_of_code' must exist.
```

### 3.2 Task Artifact Schema

**File**: `contracts/task_artifact.schema.yaml`

Defines the structure of raw ingested tasks before ground truth generation.

```yaml
type: object
properties:
 task_id:
 type: string
 source:
 type: string
 enum: ["swe_bench", "agent_bench"]
 original_code:
 type: string
 code_diff:
 type: string
 instruction:
 type: string
 instance_id:
 type: string
required:
 - task_id
 - source
 - code_diff
 - instruction
```

### 3.3 Model Outcome Schema

**File**: `contracts/model_outcome.schema.yaml`

Defines the structure of model reports and threshold sweeps.

```yaml
type: object
properties:
 model_type:
 type: string
 enum: ["logistic_regression", "random_forest"]
 threshold:
 type: number
 minimum: 0.0
 maximum: 1.0
 fnr:
 type: number
 minimum: 0.0
 maximum: 1.0
 framing:
 type: string
 enum: ["associational"]
 description: "Must be 'associational' to avoid causal claims."
 safety_flag:
 type: boolean
 description: "True if FNR > 0.1% (unsafe)."
 correlation_coefficient:
 type: number
 description: "Correlation between structural features and execution necessity."
required:
 - model_type
 - threshold
 - fnr
 - framing
 - safety_flag
```

## 4. Artifact Relationships

### 4.1 Ground Truth Generation

- **Input**: `data/raw/swe_bench_subset.parquet`, `data/raw/agentbench_subset.parquet`
- **Process**: `scripts/baseline_runner.py` executes tests in isolated environments.
- **Intermediate**: `data/processed/raw_outcomes.json` (Execution results: Pass/Fail/Timeout).
- **Output**: `data/processed/ground_truth.csv`
 - Columns: `task_id`, `code_diff`, `status`, `dynamic_execution_outcome`.
 - Logic: Merges raw ingestion data with baseline outcomes. Handles "Unparseable" tasks by marking them in `status`.

### 4.2 Feature Extraction

- **Input**: `data/processed/ground_truth.csv`
- **Process**: `scripts/extract_features.py` parses code using `tree-sitter`.
- **Intermediate**: In-memory AST/Dependency Graphs.
- **Outputs**:
 1. `data/graphs/{task_id}.json`: Serialized graph structure.
 2. `data/processed/features.csv`: Merged metrics (depth, complexity, LOC).
 - *Constraint*: Tasks with `status="Unparseable"` are filtered out before metric calculation.

### 4.3 Modeling & Reporting

- **Input**: `data/processed/features.csv`
- **Process**: `scripts/train_model.py` trains models and performs sensitivity analysis.
- **Outputs**:
 1. `models/logistic_regression.pkl`, `models/random_forest.pkl`
 2. `data/processed/threshold_sweep.json`: FNR for thresholds {0.01, 0.05, 0.1}.
 3. `data/processed/model_report.json`: Final report including `framing: "associational"` and safety flags.

## 5. Validation Rules

1. **Schema Enforcement**: All CSV/JSON outputs must pass validation against their respective `contracts/*.schema.yaml` before being written to disk.
2. **Fallback Logic**: If `semantic_complexity_score` is null/missing in a record, `lines_of_code` must be non-null. This is verified by `test_structural_metric_fallback_logic` (T005a).
3. **Data Integrity**: `task_id` must be unique across `ground_truth.csv` and `features.csv`.
4. **Associational Framing**: `model_report.json` must explicitly set `framing` to `"associational"`. Any causal language triggers a validation error (T044a/T044b).

## 6. Execution Constraints

- **CPU Only**: All dynamic execution and model training must run on CPU.
- **Real Data**: No synthetic data generation. If data fetch fails, the script must raise an exception.
- **Streaming**: Large datasets must be streamed or sampled explicitly (N=500 pilot) to fit memory constraints.
- **Timeouts**: Execution timeouts must be recorded as "Timeout" outcomes, not skipped.