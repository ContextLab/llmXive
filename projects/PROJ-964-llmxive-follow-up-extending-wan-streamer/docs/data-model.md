# llmXive Data Model Documentation

## Introduction

This document describes the data models, schemas, and contracts used throughout the llmXive automated science pipeline. All data artifacts must conform to the schemas defined in the `contracts/` directory to ensure consistency and reproducibility.

## Data Flow Overview

The pipeline processes data through several stages:

1. **Raw Data Extraction** → `raw_extract.parquet`
2. **Filtering & Labeling** → `filtered.parquet`
3. **Stratified Sampling** → `sampled_dataset.parquet`
4. **Model Training** → `estimator_checkpoint_final.pt`
5. **Hybrid Inference** → `hybrid_output.parquet`
6. **Counterfactual Analysis** → `counterfactual_indices.parquet`

## Schema Definitions

Each stage produces data artifacts that adhere to specific schema contracts. Below are the detailed references to these contracts.

### 1. Raw Extract Schema

**File**: `data/processed/raw_extract.parquet`
**Contract**: [001-raw-extract-schema.json](../contracts/001-raw-extract-schema.json)

**Columns**:
- `timestamp` (float64): Unix timestamp of the event
- `semantic_feature` (list): Semantic feature vector
- `prosodic_feature` (list): Prosodic feature vector
- `latent_delta_magnitude` (float64): Magnitude of latent space change
- `turn_label` (str): Turn-taking label ('interruption', 'pause', 'normal')
- `audio_energy` (float64): Audio energy level in dB

### 2. Filtered Event Schema

**File**: `data/processed/filtered.parquet`
**Contract**: [002-filtered-event-schema.json](../contracts/002-filtered-event-schema.json)

**Columns** (subset of raw extract with additional fields):
- All columns from `raw_extract.parquet`
- `high_priority` (bool): Flag indicating high-priority events based on domain rules
- `uncertainty` (float64): Model uncertainty score (if available)

### 3. Sampled Dataset Schema

**File**: `data/processed/sampled_dataset.parquet`
**Contract**: [003-sampled-dataset-schema.json](../contracts/003-sampled-dataset-schema.json)

**Columns**:
- All columns from `filtered.parquet`
- `sample_weight` (float64): Weight assigned during stratified sampling

### 4. Model Checkpoint Schema

**File**: `data/models/estimator_checkpoint_final.pt`
**Contract**: [006-model-checkpoint-schema.json](../contracts/006-model-checkpoint-schema.json)

**Metadata Fields**:
- `pending_validation` (bool): Validation status
- `calibration_status` (str): 'passed' or 'failed'
- `training_config` (dict): Hyperparameters used
- `performance_metrics` (dict): Validation metrics

### 5. Hybrid Output Schema

**File**: `data/processed/hybrid_output.parquet`
**Contract**: [004-hybrid-output-schema.json](../contracts/004-hybrid-output-schema.json)

**Columns**:
- `frame_id` (int64): Unique frame identifier
- `latency` (float64): Inference latency in milliseconds
- `fid_score` (float64): Fréchet Inception Distance score
- `skip_flag` (bool): Whether the frame was skipped by the hybrid engine
- `predicted_delta` (float64): Predicted latent delta magnitude
- `uncertainty` (float64): Uncertainty score for the prediction

### 6. Counterfactual Indices Schema

**File**: `data/processed/counterfactual_indices.parquet`
**Contract**: [005-counterfactual-indices-schema.json](../contracts/005-counterfactual-indices-schema.json)

**Columns**:
- `frame_id` (int64): Frame identifier for counterfactual intervention

### 7. Power Analysis Schema

**File**: `data/metrics/power_analysis_*.json`
**Contract**: [007-power-analysis-schema.json](../contracts/007-power-analysis-schema.json)

**Fields**:
- `recommended_sample_size` (int): Minimum sample size for desired power
- `expected_variance` (float): Estimated variance from pilot data
- `effect_size` (float): Minimum detectable effect size
- `variance_source` (str): Source of variance estimate ('empirical' or 'literature')

### 8. Threshold Configuration Schema

**File**: `code/config/detection_thresholds.yaml`
**Contract**: [008-threshold-config-schema.json](../contracts/008-threshold-config-schema.json)

**Fields**:
- `audio_energy_threshold` (float): Energy threshold in dB
- `delta_magnitude_threshold` (float): Latent delta threshold
- `uncertainty_threshold` (float): Uncertainty threshold for fallback

## Validation Process

Data artifacts are validated at each pipeline stage using the `code/utils/validators.py` module. Validation checks include:

1. **Schema Compliance**: All required columns present with correct types
2. **Value Ranges**: Numeric values within expected bounds
3. **Completeness**: No null values in required fields
4. **Consistency**: Cross-field constraints satisfied

Example validation command:
```bash
python code/utils/validators.py \
 --input data/processed/sampled_dataset.parquet \
 --contract contracts/003-sampled-dataset-schema.json \
 --output data/logs/validation_report.txt
```

## Contract Files Location

All schema contract definitions are stored in the `contracts/` directory:

```
contracts/
├── 001-raw-extract-schema.json
├── 002-filtered-event-schema.json
├── 003-sampled-dataset-schema.json
├── 004-hybrid-output-schema.json
├── 005-counterfactual-indices-schema.json
├── 006-model-checkpoint-schema.json
├── 007-power-analysis-schema.json
└── 008-threshold-config-schema.json
```

## Updating Schemas

If new data fields are added or existing fields are modified:

1. Update the corresponding contract file in `contracts/`
2. Update the validation logic in `code/utils/validators.py`
3. Update this documentation
4. Run the full validation suite to ensure backward compatibility

## Related Documentation

- [Quickstart Guide](quickstart.md) - Pipeline execution instructions
- [Research Documentation](research.md) - Methodology and theoretical background
- [Task List](../tasks.md) - Implementation status and dependencies