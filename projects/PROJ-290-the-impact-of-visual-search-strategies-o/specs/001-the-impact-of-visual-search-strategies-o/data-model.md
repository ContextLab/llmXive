# Data Model: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

## Overview

This document defines the data structures, transformations, and schemas required for the pipeline. All data flows from raw downloads to processed features, ensuring traceability and reproducibility.

## Entities

### Participant
- **Attributes**: `participant_id` (str), `processing_strategy_label` (str, optional), `demographic_metadata` (dict), `continuous_fixation_ratio` (float).
- **Purpose**: Represents a research subject with unique ID and derived strategy label (optional) and continuous fixation ratio (primary predictor).
- **Source**: Populated from the dataset identified in `research.md` (Section 'Dataset Strategy').

### Trial
- **Attributes**: `trial_id` (str), `participant_id` (str), `emotion_type` (str), `response_time` (float), `fixation_metrics` (dict).
- **Purpose**: Single experimental observation with emotional context and gaze data.

### FixationMetric
- **Attributes**: `metric_name` (str), `value` (float), `unit` (str), `trial_id` (str), `ROI_mask_reference` (str).
- **Purpose**: Computed eye-tracking feature with ROI context. Can be derived from `roi_annotations` or **Generic ROI Fallback**.

## Data Flow

1. **Raw Data**: Downloaded from HuggingFace; stored in `data/raw/`.
2. **Validation**: Check for critical variables; exclude incomplete records.
3. **Feature Extraction**: Compute fixation metrics; store in `data/processed/features.csv`.
4. **Continuous Ratio Calculation**: Compute `continuous_fixation_ratio` for each participant.
5. **Classification**: Assign strategy labels (optional); store in `data/processed/labels.csv`.
6. **Model Input**: Merge features, labels, and continuous ratio; prepare for LMM.

## Schema Definitions

### Input Schema (Raw Dataset)
- **Required Fields**: `gaze_coordinates`, `response_times`, `emotion_labels`.
- **Optional Fields**: `roi_annotations` (if missing, Generic ROI Fallback is applied).
- **Types**: `gaze_coordinates` (list of tuples), `response_times` (float), `emotion_labels` (str), `roi_annotations` (dict).

### Output Schema (Processed Features)
- **Fields**: `participant_id`, `trial_id`, `emotion_type`, `eye_duration`, `mouth_duration`, `saccade_amplitude`, `dispersion`, `continuous_fixation_ratio`, `processing_strategy_label` (optional).
- **Types**: All numeric fields as float; labels as str.

### Sensitivity Report Schema
- **Fields**: `k_value`, `cluster_composition`, `model_coefficients` (list of floats).
- **Types**: `k_value` (int), `cluster_composition` (dict), `model_coefficients` (list of floats).

## Constraints

- **Data Hygiene**: Raw data never modified; derivations produce new files.
- **PII**: No personally identifiable information in committed data.
- **Checksums**: All files under `data/` checksummed and recorded in `state/`.

## Edge Cases

- **Missing Emotions**: Filter to available emotions; log warning.
- **Incomplete Gaze Data**: Exclude participants with >20% missing coordinates; document exclusion rate.
- **Coordinate Systems**: Normalize automatically; log transformation method.
- **Missing Critical Variables**: Halt execution; log specific error.
- **Missing ROI Annotations**: Apply Generic ROI Fallback (3x3 grid split).