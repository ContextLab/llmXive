# Data Model: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Overview

This document defines the data structures used throughout the pipeline, from raw data ingestion to final analysis results. The model ensures traceability and consistency across preprocessing, feature extraction, and statistical analysis.

## Entities

### 1. Participant

Represents a unique individual in the study.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | `str` | Unique identifier for the participant. | Required, Unique |
| `age` | `int` | Age in years. | Optional (may be missing in public datasets) |
| `gender` | `str` | Gender identity. | Optional |
| `medication_status` | `str` | Current medication status. | Optional |
| `time_of_day` | `str` | Time of data collection (e.g., "morning", "afternoon"). | Optional |

### 2. EEGSegment

Represents a continuous time-locked resting-state recording.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `segment_id` | `str` | Unique identifier for the segment. | Required, Unique |
| `participant_id` | `str` | Foreign key to `Participant`. | Required |
| `status` | `str` | Pre-task or Post-task. | Enum: ["pre", "post", "baseline"] |
| `duration_sec` | `float` | Duration of the segment in seconds. | ≥ 120.0 |
| `sampling_rate` | `float` | Sampling rate in Hz. | Required |
| `channels` | `list[str]` | List of channel names. | Required |
| `data_path` | `str` | Path to the preprocessed data file. | Required |
| `checksum` | `str` | SHA-256 hash of the data file. | Required |

### 3. ComplexityMetric

Represents the calculated complexity value for a specific channel and segment.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `metric_id` | `str` | Unique identifier. | Required, Unique |
| `segment_id` | `str` | Foreign key to `EEGSegment`. | Required |
| `channel` | `str` | Channel name (e.g., "Fz", "Cz"). | Required |
| `metric_type` | `str` | Type of metric. | Enum: ["LZC", "PE"] |
| `value` | `float` | Calculated complexity value. | Required |
| `timestamp` | `datetime` | Time of calculation. | Required |

### 4. FatigueScore

Represents the subjective fatigue rating for a participant at a specific time point.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `score_id` | `str` | Unique identifier. | Required, Unique |
| `participant_id` | `str` | Foreign key to `Participant`. | Required |
| `status` | `str` | Pre-task or Post-task (or "baseline" if single timepoint). | Enum: ["pre", "post", "baseline"] |
| `instrument` | `str` | Instrument used (e.g., "NASA-TLX", "Borg"). | Required |
| `value` | `float` | Fatigue rating. | Required |
| `timestamp` | `datetime` | Time of collection. | Required |

### 5. AnalysisResult

Represents the outcome of the correlation analysis for a specific channel and metric.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `result_id` | `str` | Unique identifier. | Required, Unique |
| `channel` | `str` | Channel name. | Required |
| `metric_type` | `str` | Metric type (LZC or PE). | Enum: ["LZC", "PE"] |
| `correlation_coef` | `float` | Pearson/Spearman coefficient or ANCOVA beta. | [-1, 1] (or unbounded for beta) |
| `p_value_raw` | `float` | Raw p-value. | [0, 1] |
| `p_value_corrected` | `float` | BH-corrected p-value. | [0, 1] |
| `significant_at_05` | `bool` | True if p_corrected < 0.05. | Required |
| `significant_at_01` | `bool` | True if p_corrected < 0.01. | Required |
| `effect_size_ci_lower` | `float` | Lower bound of 95% CI. | Optional |
| `effect_size_ci_upper` | `float` | Upper bound of 95% CI. | Optional |

## Data Flow

1.  **Raw Data**: Downloaded to `data/raw/` (Parquet/CSV/EDF).
2.  **Preprocessed Data**: `data/processed/segments/` (MNE `.fif` or `.npy`).
3.  **Features**: `data/processed/features/complexity_metrics.csv`.
4.  **Fatigue Data**: `data/processed/fatigue/fatigue_scores.csv`.
5.  **Analysis Results**: `data/processed/results/correlation_results.csv`.
6.  **Report**: `docs/report.pdf` generated from `AnalysisResult`.

## Validation Rules

- **Completeness**: All segments must have `duration_sec` ≥ 120.
- **Range**: Fatigue scores must be within the valid range of the instrument (e.g., 0-100 for NASA-TLX).
- **Consistency**: `participant_id` in `FatigueScore` must exist in `Participant`.
- **Artifact Rejection**: Segments with amplitude > ±100 µV are excluded and logged.
- **Data Structure**: The pipeline must detect if only one `status` (e.g., "baseline") exists per participant and adjust the statistical model accordingly.