# Data Model: Heterogeneous Scientific Foundation Model Collaboration Benchmark

## Entities

### Dataset

Represents a public scientific dataset with associated metadata.

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| dataset_id | string | Unique identifier | Primary key |
| name | string | Human-readable name | Required |
| modality | enum | time-series, tabular, text | Required |
| source_url | string | Verified download URL | Required (if available) |
| size_mb | float | Dataset size in MB | Required |
| checksum | string | SHA-256 hash | Required (Constitution III) |
| variables | array | List of feature names | Required |
| label_column | string | Ground-truth label field | Required |
| verified | boolean | Source verified by Reference-Validator | Required |

### Task

Represents a multi-modal prediction problem linking datasets.

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| task_id | string | Unique identifier (e.g., "task-001") | Primary key |
| name | string | Human-readable task name | Required |
| modalities | array | List of modalities (2-3 items) | Required |
| dataset_ids | array | Linked dataset identifiers | Required |
| target_label | string | Prediction target | Required |
| metric_type | enum | classification, regression | Required |
| primary_metric | string | F1 or MAPE | Required |
| enabled | boolean | Whether task is active | Default: true |

### ModalityModel

Encapsulates a pre-trained model for a single modality.

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| model_id | string | Unique identifier | Primary key |
| modality | enum | time-series, tabular, text | Required |
| hf_identifier | string | HuggingFace model path | Required |
| size_mb | float | Model weight size | Required (<1 GB) |
| inference_time_max | float | Max inference time (minutes) | Required (≤5) |
| cpu_compatible | boolean | Runs on CPU-only | Required (true) |
| version | string | Model version hash | Required (Constitution V) |

### Result

Represents evaluation output for a task under a condition.

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| result_id | string | Unique identifier | Primary key |
| task_id | string | Linked task | Required |
| condition | enum | heterogeneous, unified | Required |
| seed | integer | Random seed used | Required (Constitution I) |
| metric_value | float | F1 or MAPE score | Required |
| inference_time | float | Wall-clock time (minutes) | Required (≤5) |
| success | boolean | Task completed successfully | Required |
| error_message | string | Error if failed | Optional |
| timestamp | datetime | Execution timestamp | Required |

### StatisticalSummary

Aggregated results across tasks and seeds.

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| summary_id | string | Unique identifier | Primary key |
| metric_name | string | F1 or MAPE | Required |
| condition_heterogeneous | float | Mean accuracy (Condition A) | Required |
| condition_unified | float | Mean accuracy (Condition B) | Required |
| absolute_diff | float | Percentage difference | Required |
| t_statistic | float | Paired t-test statistic | Required |
| p_value | float | Paired t-test p-value | Required |
| wilcoxon_statistic | float | Wilcoxon statistic | Required (FR-014) |
| wilcoxon_p_value | float | Wilcoxon p-value | Required (FR-014) |
| effect_size | float | Cohen's d | Required (FR-014) |
| ci_lower | float | Bootstrap CI lower bound | Required (FR-007) |
| ci_upper | float | Bootstrap CI upper bound | Required (FR-007) |
| bootstrap_resamples | integer | Number of bootstrap samples | Required (sufficient number) |
| alpha_threshold | float | Significance threshold | Required (0.05) |
| generated_at | datetime | Generation timestamp | Required |

## Relationships

```
Dataset (1) ──< Task (N)
Task (1) ──< Result (N)
ModalityModel (1) ──< Task (N)
Result (N) ──> StatisticalSummary (1)
```

## Data Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Dataset   │───>│    Task     │───>│    Result   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                   │
       │                  │                   ▼
       │                  │          ┌─────────────────┐
       │                  │          │ StatisticalSum  │
       │                  │          └─────────────────┘
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  Checksums  │    │   Contracts │
│ (Constitution│   │   Validation │
│    III)     │    └─────────────┘
└─────────────┘
```

## Schema Files

| Schema | Path | Purpose |
|--------|------|---------|
| dataset.schema.yaml | contracts/dataset.schema.yaml | Validate dataset downloads |
| task.schema.yaml | contracts/task.schema.yaml | Validate task definitions |
| results.schema.yaml | contracts/results.schema.yaml | Validate results output |
| modality_model.schema.yaml | contracts/modality_model.schema.yaml | Validate model configurations |

## Reproducibility Requirements

| Requirement | Implementation |
|-------------|----------------|
| Random seeds | Logged in Result.seed (FR-005) |
| Model versions | Logged in ModalityModel.version (Constitution V) |
| Environment details | Logged in logging.py (FR-005) |
| Data checksums | Recorded in data/checksums.yaml (Constitution III) |
| Content hashes | Stored in state/ artifact_hashes (Constitution V) |
| StatisticalSummary | Persisted to data/statistical_summary.yaml (Constitution IV) |