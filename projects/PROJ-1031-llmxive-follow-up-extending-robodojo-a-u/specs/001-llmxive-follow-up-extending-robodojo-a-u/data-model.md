# Data Model: Extending RoboDojo with Symbolic Abstractions

## Overview
All pipeline artifacts are persisted as Parquet files to guarantee efficient I/O and schema enforcement. Validation is performed via Pydantic models that mirror the JSON‑Schema contracts in `contracts/`.

## Entities

| Entity | Storage Path | Key Fields | Schema |
|--------|--------------|------------|--------|
| **SemanticEmbedding** | `data/interim/semantic_embeddings.parquet` | `task_id`, `frame_id`, `embedding_vector`, `timestamp`, `mapping_accuracy` (optional) | – |
| **SymbolicState** | `data/interim/symbolic_states.parquet` | `state_id`, `task_id`, `predicates`, `affordances`, `connectivity_graph`, `graph_type` | `contracts/symbolic_state.schema.yaml` |
| **ActionSequence** | `data/interim/action_sequences.parquet` | `sequence_id`, `task_id`, `steps`, `planner_type`, `planning_time_ms`, `graph_type` | `contracts/action_sequence.schema.yaml` |
| **ExecutionOutcome** | `data/interim/execution_logs.parquet` | `log_id`, `task_id`, `step_index`, `outcome`, `failure_mode`, `timestamp`, `error_details`, `graph_type` | `contracts/execution_outcome.schema.yaml` |
| **ComputeMetric** | `data/interim/compute_metrics.parquet` | `metric_id`, `task_id`, `phase`, `cpu_usage_pct`, `memory_mb`, `wall_clock_seconds`, `graph_type` | `contracts/compute_metric.schema.yaml` |
| **AblationResult** | `data/interim/ablation_results.parquet` | `ablation_id`, `graph_type`, `success_rate`, `compute_overhead`, `catastrophic_failure_rate` | `contracts/ablation_result.schema.yaml` |

## Data Flow
1. **Raw RoboDojo data** → `data/raw/` (checksummed).  
2. **Embedding generation** → `SemanticEmbedding`.  
3. **Embedding → SymbolicState** (includes ambiguous‑mapping detection).  
4. **SymbolicState → ActionSequence** (planner).  
5. **ActionSequence → ExecutionOutcome** (Oracle & Real executors).  
6. **All phases** → `ComputeMetric`.  
7. **Metrics + Outcomes** → `AblationResult` (analysis).  

## Validation Rules
- **Uniqueness**: `task_id` unique per run; UUIDs for all other IDs.  
- **Referential Integrity**: `state_id` referenced in `ActionSequence` must exist.  
- **Completeness**: `failure_mode` = `"None"` when `outcome` = `"Success"`.  
- **Dimensionality**: `embedding_vector` length = 512.  
- **Graph Type Consistency** across related records.  

---
