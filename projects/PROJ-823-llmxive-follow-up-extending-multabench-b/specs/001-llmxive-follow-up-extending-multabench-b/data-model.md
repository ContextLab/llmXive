# Data Model: llmXive Follow-up Extending MulTaBench

## Overview

This document defines the data structures, schemas, and propagation rules for the llmXive pipeline extending MulTaBench. It establishes the contract between pipeline stages and ensures consistency across embedding generation, projection training, and statistical analysis.

## Core Entities

### Run Identification

**`run_id`**: A unique, deterministic identifier for a complete pipeline execution.
- **Format**: `{project_id}_{timestamp}_{seed_hash}` (e.g., `PROJ-823_20231015_42a1b9c`)
- **Generation**: Created by `code/embeddings/serializer.py::generate_run_id()` using the global `random_seed` and a timestamp.
- **Propagation**: The `run_id` is the primary key for all artifacts. It must be:
 1. Generated once at the start of `run_baseline.py` (US1).
 2. Passed as an argument to all downstream scripts (`run_conditioned.py`, `run_analysis.py`).
 3. Embedded in every output file name and metadata field.
 4. Used to link frozen baselines, conditioned metrics, and correlation results.

### Contract Files

The pipeline enforces schema validation via the following contract definitions:
1. **Frozen Embeddings**: Defined in `contracts/frozen_embedding.schema.yaml` (T009a).
 - Used by `code/embeddings/serializer.py` to validate output before saving.
 - Ensures `run_id`, `dataset_id`, and vector dimensions are consistent.
2. **Tabular Metadata**: Defined in `contracts/tabular_metadata.schema.yaml` (T009b).
 - Used by `code/analysis/metadata_stats.py` to validate input features.
 - Ensures cardinality, missingness, and variance metrics are correctly structured.

## Data Flow & Artifact Specifications

### Phase 1: Embedding Generation (US1)

**Input**: Raw MulTaBench datasets (images, text, tabular).
**Process**: `code/pipelines/run_baseline.py`
**Output**: `data/processed/embeddings_{run_id}.parquet`
**Schema**: Matches `contracts/frozen_embedding.schema.yaml`.
**Key Fields**:
 - `run_id`: Propagated from entry point.
 - `dataset_id`: Identifier of the source dataset.
 - `embedding_vector`: Float32 array (fixed dimension).
 - `metadata`: JSON blob containing source checksums.

### Phase 2: Projection Training (US2)

**Input**: Frozen embeddings (US1) + Tabular metadata stats.
**Process**: `code/pipelines/run_conditioned.py`
**Output**: `data/artifacts/metrics_conditioned_{run_id}.json`
**Schema**: Contains performance metrics (AUC/RMSE) linked to `run_id`.
**Key Fields**:
 - `run_id`: Must match the frozen baseline `run_id`.
 - `dataset_id`: Must correspond to an entry in the frozen embeddings.
 - `metrics`: Dictionary of evaluation results.

### Phase 3: Correlation & Analysis (US3)

**Input**:
 - `data/artifacts/frozen_baseline_aggregated_{run_id}.json` (from T019c)
 - `data/artifacts/gpu_tuned_baselines.csv` (from T032a)
 - `data/processed/metadata_stats_summary.csv` (from T024)
**Process**: `code/pipelines/run_analysis.py`
**Output**: `data/artifacts/correlation_report_{run_id}.json`
**Key Fields**:
 - `run_id`: Unified identifier for the entire analysis.
 - `recovery_ratio`: Calculated metric.
 - `correlations`: Pearson coefficients and p-values.
 - `significance`: FDR-adjusted flags.

## Propagation Rules

1. **Strict Coupling**: All artifacts generated in a single pipeline run MUST share the exact same `run_id`.
2. **Determinism**: Re-running the pipeline with the same `random_seed` and input data must produce the same `run_id` and identical artifact contents (verified via SHA-256).
3. **Validation**: Every script that reads an artifact MUST validate it against the corresponding contract schema (e.g., `frozen_embedding.schema.yaml`) before processing.
4. **Gap Handling**: If `gpu_tuned_baselines.csv` is missing entries for a `dataset_id`, the correlation analysis must flag this in the "Data Availability Gap" report without failing the entire run.

## Schema References

- **Frozen Embedding Schema**: `contracts/frozen_embedding.schema.yaml`
 - Defines structure for `data/processed/embeddings_{run_id}.parquet`
- **Tabular Metadata Schema**: `contracts/tabular_metadata.schema.yaml`
 - Defines structure for `data/processed/metadata_stats_summary.csv`
- **GPU Baseline Schema**: `data/artifacts/gpu_tuned_baselines.csv`
 - Columns: `dataset_id`, `task_type`, `baseline_value`

## Version History

- **v1.0**: Initial model definition, `run_id` propagation rules, and contract references added.