# Data Model: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## 1. Entity Definitions

### Episode
A single interaction instance from the GateMem dataset.
- **Fields**:
  - `episode_id`: Unique identifier (string).
  - `domain`: Context domain (enum: "medical", "office", "education", "household").
  - `user_role`: Role of the user (string).
  - `intent`: User intent classification (string).
  - `query`: User query text (string).
  - `memory_state`: Current memory context (string).
  - `leak_target`: Ground truth label for leakage (boolean: True if leak allowed, False if blocked).
  - `deletion_request`: Boolean indicating if a deletion request is present.
  - `deletion_log`: History of deletion requests (list of strings).
  - `ground_truth_success`: Boolean indicating if the task was successful (from human annotation).

### EvaluationResult
The output of running a pipeline (Gatekeeper or Baseline) on an episode.
- **Fields**:
  - `episode_id`: Reference to the input episode.
  - `pipeline_type`: "gatekeeper", "retrieval_only", or "long_context".
  - `allowed`: Boolean indicating if the pipeline allowed the query.
  - `generated_response`: LLM output (string).
  - `task_success`: Boolean indicating if the generated response achieved the task (calculated).
  - `latency_ms`: Wall-clock time in milliseconds.
  - `peak_ram_mb`: Peak memory usage in MB.

### MetricAggregation
Aggregated metrics for a specific pipeline and domain.
- **Fields**:
  - `pipeline_type`: "gatekeeper" or "baseline".
  - `domain`: Domain name.
  - `access_control_score`: Float (0.0 to 1.0).
  - `utility_score`: Float (0.0 to 1.0).
  - `forgetting_score`: Float (0.0 to 1.0).
  - `conditional_utility`: Float (0.0 to 1.0).
  - `overall_success_rate`: Float (0.0 to 1.0).
  - `avg_latency_ms`: Float.
  - `avg_peak_ram_mb`: Float.

## 2. Data Flow

1. **Ingestion**: `data_loader.py` fetches GateMem JSONL, validates schema, and writes to `data/raw/`.
2. **Validation**: **Variable Presence Check** ensures all required variables (outcome, predictors, covariates) are present.
3. **Processing**: `pipeline.py` and `baselines/*.py` process episodes, generating `EvaluationResult` objects.
4. **Aggregation**: `metrics/*.py` calculate scores (including Conditional Utility) and write to `data/processed/metrics.json`.
5. **Analysis**: `stats/comparison.py` performs McNemar's Test and GLMM, writing statistical results to `data/processed/stats_results.json`.
6. **Sampling**: `cli/run_evaluation.py` generates `data/samples/failure_cases.json` (stratified by domain).
7. **Reporting**: `cli/generate_report.py` aggregates all results into `data/processed/final_report.json`.

## 3. Schema Contracts

All data files MUST conform to the schemas defined in `specs/.../contracts/` (Canonical Source).
- `specs/.../contracts/gatemem_episode.schema.yaml`: Validates raw input data.
- `specs/.../contracts/evaluation_result.schema.yaml`: Validates pipeline outputs.
- `specs/.../contracts/metrics.schema.yaml`: Validates aggregated results.
- `src/contracts/`: Generated artifact (Copied from `specs/.../contracts/` during build).

*Note: See `specs/.../contracts/` directory for full YAML schema definitions.*