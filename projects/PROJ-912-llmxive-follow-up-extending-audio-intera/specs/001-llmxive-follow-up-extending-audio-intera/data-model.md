# Data Model: Audio Interaction Model Extension

## 1. Overview
This document defines the data structures used in the `llmXive` audio compression robustness study. The model supports streaming ingestion, compression configuration, inference metrics, and analysis results.

## 2. Core Entities

### 2.1 `StudentModel`
Represents a compressed variant of the teacher model.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `model_id` | `str` | Unique identifier (e.g., "wav2vec-int4-pruned-0.2") | Generated |
| `teacher_id` | `str` | ID of the teacher model | Config |
| `bit_width` | `int` | Quantization level (32, 8, 4) | Config |
| `pruning_ratio` | `float` | Fraction of parameters pruned (0.0 - 1.0) | Config |
| `param_count` | `int` | Total parameters after compression | Derived |
| `checkpoint_path` | `str` | Path to saved weights | Generated |
| `compression_method` | `str` | "quantization", "pruning", "distillation" | Config |

### 2.2 `SubtleCueSample`
Represents a filtered audio sample from the testbed.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `sample_id` | `str` | Unique identifier (e.g., "esc50-glass-001") | Dataset |
| `class_label` | `str` | Ground truth class (e.g., "glass breaking") | Dataset |
| `dataset_source` | `str` | "esc50" or "urban_sound_8k" | Dataset |
| `file_path` | `str` | Path to audio file (streamed) | Dataset |
| `spectral_centroid` | `float` | Dominant frequency in Hz (derived) | Derived |
| `spectral_flux` | `float` | Spectral flux (transient indicator) | Derived |
| `snr_db` | `float` | Signal-to-Noise Ratio in dB | Derived |
| `is_subtle` | `bool` | True if meets composite subtle criteria | Derived |
| `duration_sec` | `float` | Duration in seconds | Dataset |

### 2.3 `RobustnessMetric`
Stores the evaluation results for a specific model on the testbed.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `run_id` | `str` | Unique run identifier | Generated |
| `model_id` | `str` | FK to `StudentModel` | Input |
| `auc_score` | `float` | Area Under the Curve | Derived |
| `inference_latency_ms` | `float` | Avg inference time per sample | Measured |
| `peak_ram_gb` | `float` | Peak RAM usage during inference | Measured |
| `threshold` | `float` | Decision threshold used | Input |
| `fpr_rate` | `float` | False Positive Rate | Derived |
| `fnr_rate` | `float` | False Negative Rate | Derived |
| `oom_occurred` | `bool` | Whether OOM error occurred | Measured |
| `param_reduction_pct` | `float` | Percentage of parameters removed (for normalization) | Derived |

### 2.4 `AblationConfig`
Defines the architectural modifications for ablation studies.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `config_id` | `str` | Unique identifier | Generated |
| `freeze_attention_heads` | `bool` | Whether to freeze early attention | Config |
| `prune_ffn_layers` | `bool` | Whether to prune late FFN | Config |
| `layers_pruned` | `list[int]` | Indices of pruned layers | Config |
| `compression_level` | `str` | Fixed compression level for this config (e.g., "INT8") | Config |

## 3. Data Flow

1. **Ingestion**: `ESC-50` & `UrbanSound8K` datasets streamed -> Split (90/10) -> Calibrate on [deferred] -> Filter [deferred] to `SubtleCueSample` list (Subtle + Control).
2. **Compression**: `TeacherModel` -> `StudentModel` variants (via `compress.py`).
3. **Inference**: `StudentModel` + `SubtleCueSample` -> `RobustnessMetric` records.
4. **Analysis**: `RobustnessMetric` -> `RobustnessCurve` (AUC vs. Compression) & `SensitivityReport` (Threshold sweep) & `AblationReport` (Normalized by param reduction).

## 4. Storage Schema

- **Raw Data**: Streamed from Hugging Face (no local storage).
- **Processed Data**: Filtered subsets stored in `data/processed/` with checksums.
- **Checkpoints**: `StudentModel` weights stored in `models/checkpoints/`.
- **Results**: `RobustnessMetric` records stored in `results/metrics.csv` (JSONL for flexibility).

## 5. Constraints

- **Memory**: All data structures must fit in ≤7GB RAM. Streaming is mandatory for large datasets.
- **Immutability**: Raw data files are never modified; derivations create new files.
- **Checksums**: All processed files must have SHA-256 checksums recorded in `state/...yaml`.
