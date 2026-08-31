# Data Model: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Overview

This document defines the data structures, file formats, and schemas used throughout the pipeline. All data is stored in local directories under `data/`. Raw data is immutable; derived data is versioned by content hash.

## Directory Structure

```text
data/
├── raw/
│   ├── eeg_restingstate/          # Original EEG files (e.g., .edf, .bdf)
│   └── pvt_fatigue/               # Original PVT/Fatigue files (e.g., .csv, .zip)
├── processed/
│   ├── cleaned_eeg/               # MNE .fif files (filtered, re-referenced)
│   └── artifacts/                 # Logs of rejected channels/epochs
├── analysis/
│   ├── complexity_metrics.csv     # LZC and PE per channel per segment
│   ├── fatigue_scores.csv         # Pre/Post fatigue ratings
│   └── correlation_results.csv    # Final statistical results
└── manifests/
    └── data_manifest.json         # Checksums and source URLs
```

## Entity Definitions

### 1. Raw EEG Segment
- **Type**: `EEGSegment`
- **Description**: A continuous time series of EEG data from a single participant.
- **Attributes**:
    - `participant_id`: Unique identifier (string).
    - `segment_type`: "pre" or "post" (string).
    - `duration_sec`: Length in seconds (float).
    - `channel_count`: Number of electrodes (int).
    - `sampling_rate`: Hz (float).

### 2. Complexity Metric
- **Type**: `ComplexityMetric`
- **Description**: A calculated value representing signal complexity.
- **Attributes**:
    - `participant_id`: (string).
    - `channel`: Electrode name (e.g., "Fz", "Cz").
    - `metric_type`: "LZC" or "PE".
    - `value`: Calculated metric (float).
    - `segment_type`: "pre" or "post".
    - `delta_value`: Difference (Post - Pre).

### 3. Fatigue Score
- **Type**: `FatigueScore`
- **Description**: Subjective or objective fatigue rating.
- **Attributes**:
    - `participant_id`: (string).
    - `score_type`: "Subjective" or "PVT".
    - `pre_score`: Rating before task (float).
    - `post_score`: Rating after task (float).
    - `delta_score`: Difference (Post - Pre).

### 4. Correlation Result
- **Type**: `CorrelationResult`
- **Description**: Statistical output for a specific channel and metric.
- **Attributes**:
    - `channel`: (string).
    - `metric_type`: "LZC" or "PE".
    - `correlation_coefficient`: r value (float).
    - `p_value`: Raw p-value (float).
    - `p_value_bh`: BH-corrected p-value (float).
    - `significant`: Boolean (True if p_bh < 0.05).
    - `vif`: Variance Inflation Factor (float).

## Data Flow

1.  **Download**: Raw files from Hugging Face → `data/raw/`.
2.  **Validate**: Check for paired data → Halt if missing (FR-001).
3.  **Preprocess**: Raw → Filtered/Re-referenced `.fif` → `data/processed/`.
4.  **Extract**: `.fif` → `ComplexityMetric` → `data/analysis/complexity_metrics.csv`.
5.  **Analyze**: `ComplexityMetric` + `FatigueScore` → `CorrelationResult` → `data/analysis/correlation_results.csv`.
6.  **Report**: Generate PDF/HTML from `correlation_results.csv`.
