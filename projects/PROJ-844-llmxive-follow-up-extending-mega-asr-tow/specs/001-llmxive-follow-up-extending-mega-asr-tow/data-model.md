# Data Model: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Overview
This document defines the data structures for the stress-testing pipeline, including the input audio metadata, the generated stress curves, the derived collapse points, and the regression results.

## Entities

### AudioClip
Represents a single audio file from the source dataset.
- `clip_id`: Unique identifier (string).
- `source_url`: URL of the original audio file.
- `transcript`: Ground truth transcript (string).
- `speaker_id`: Identifier for the speaker (string).
- `duration_seconds`: Audio duration (float).

### DistortionVector
Represents a specific combination of acoustic parameters.
- `snr_db`: Signal-to-Noise Ratio in decibels (float).
- `rt60_sec`: Reverberation time in seconds (float).
- `distortion_type`: Label (e.g., "Reverb+Noise").
- `scenario_id`: Unique ID for the 54-scenario grid (integer).

### StressCurveRecord
A single data point on a stress curve for a specific clip and distortion.
- `clip_id`: FK to AudioClip.
- `scenario_id`: FK to DistortionVector.
- `model_name`: ASR model used (string).
- `wer`: Word Error Rate (float).
- `sss`: Semantic Similarity Score (float, 0.0–1.0).
- `hypothesis`: ASR output text (string).

### CollapseIntensity
The derived collapse point for a specific clip/model/scenario.
- `clip_id`: FK to AudioClip.
- `model_name`: FK to ASR model.
- `normalized_inflection_coord`: The position of the inflection point within the normalized SNR/RT60 space (float).
- `collapse_type`: "Inflection", "Threshold", or "None".
- `sss_at_collapse`: SSS value at the collapse point.
- `wer_at_collapse`: WER value at the collapse point.
- `fallback_metric`: (Optional) Phoneme-level edit distance if SSS failed (FR-022).
- `sigmoid_slope`: Slope of the fitted sigmoid curve at the inflection point.
- `ausc`: Area Under Stress Curve.

### RegressionInput
The input data for the predictive model, including curve parameters and target variables.
- **Grouping Variables** (Used for Hierarchical Regression, NOT as features):
    - `clip_id`: Unique identifier for the audio clip.
    - `model_name`: Name of the ASR model.
- **Features**:
    - `snr`: SNR value (mean-centered).
    - `rt60`: RT60 value (mean-centered).
    - `snr_sq`: SNR squared.
    - `rt60_sq`: RT60 squared.
    - `snr_rt60`: Interaction term (SNR * RT60).
- **Targets**:
    - `normalized_inflection_coord`: The position of the inflection point in normalized space.
    - `sigmoid_slope`: Slope of the fitted sigmoid curve.
    - `ausc`: Area Under Stress Curve.
    - `p_value_adjusted`: Adjusted p-value for the interaction term (FDR corrected).

### RegressionResult
The output of the predictive model.
- `feature`: Name of the predictor (e.g., "SNR", "RT60", "SNR:RT60").
- `coefficient`: Learned weight (float).
- `p_value`: Statistical significance (float).
- `shap_value_mean`: Mean absolute SHAP value (float).

## File Format
- **Raw Data**: Parquet (streamed from Hugging Face).
- **Derived Data**: Parquet (for efficient columnar access).
- **Config/Results**: JSON.
