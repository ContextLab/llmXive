# Data Model: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Overview

This document defines the data structures used to store raw audio metadata, distortion parameters, stress curve results, and derived collapse points. The data model is designed for efficient storage (Parquet) and easy querying for regression analysis.

## 2. Entity Definitions

### 2.1. AudioClip
Represents a single audio file from the source dataset.

| Field | Type | Description |
| :--- | :--- | :--- |
| `clip_id` | string | Unique identifier for the audio clip. |
| `source_dataset` | string | Name of the source dataset (e.g., "librispeech"). |
| `speaker_id` | string | Identifier for the speaker. |
| `duration_sec` | float | Duration of the audio in seconds. |
| `clean_transcript` | string | Ground truth transcript. |
| `audio_path` | string | Relative path to the raw audio file in `data/raw/`. |

### 2.2. DistortionVector
Represents a specific combination of acoustic parameters.

| Field | Type | Description |
| :--- | :--- | :--- |
| `vector_id` | string | Unique ID (e.g., "RT0.5_SNR-10"). |
| `rt60_sec` | float | Reverberation time in seconds. |
| `snr_db` | float | Signal-to-Noise Ratio in dB. |
| `distortion_type` | string | Description (e.g., "Reverb+Noise"). |
| `cumulative_stress_index` | float | CSI = max(0, -SNR_dB) + RT60_sec. Used for ordering. |

### 2.3. StressCurveRecord
A single row in the stress curve, representing one clip under one distortion scenario.

| Field | Type | Description |
| :--- | :--- | :--- |
| `record_id` | string | Unique ID. |
| `clip_id` | string | FK to AudioClip. |
| `vector_id` | string | FK to DistortionVector. |
| `model_name` | string | Name of the ASR model used (e.g., "whisper-tiny"). |
| `asr_hypothesis` | string | Transcribed text from the ASR model. |
| `wer` | float | Word Error Rate. |
| `sss_raw` | float | Raw Semantic Similarity Score (cosine similarity). |
| `sss_normalized` | float | SSS normalized to the clean baseline (0-1 scale). |
| `is_collapsed` | boolean | True if `sss_normalized < 0.5` AND `wer > 2 * baseline_wer`. |

### 2.4. CollapseIntensity
Derived entity representing the failure point for a specific clip/model/scenario.

| Field | Type | Description |
| :--- | :--- | :--- |
| `collapse_id` | string | Unique ID. |
| `clip_id` | string | FK to AudioClip. |
| `model_name` | string | ASR model name. |
| `collapse_vector_id` | string | FK to DistortionVector (the intensity where collapse occurred). |
| `rt60_at_collapse` | float | RT60 value at collapse. |
| `snr_at_collapse` | float | SNR value at collapse. |
| `collapse_threshold` | float | The SSS threshold used (e.g., 0.5). |
| `status` | string | "Found", "Max Tested", or "None". |
| `human_validated_margin` | float | **New**: The Human-Validated Collapse Margin (HVCM) target for regression. |

### 2.5. RegressionInput
Flattened dataset for model training, including interaction terms.

| Field | Type | Description |
| :--- | :--- | :--- |
| `collapse_id` | string | FK to CollapseIntensity. |
| `model_name` | string | ASR model name. |
| `snr` | float | SNR value. |
| `rt60` | float | RT60 value. |
| `snr_sq` | float | SNR². |
| `rt60_sq` | float | RT60². |
| `snr_rt60` | float | Interaction term (SNR × RT60). |
| `target_hvcm` | float | **New**: Target variable (Human-Validated Collapse Margin). |
| `p_value_adjusted` | float | **New**: Adjusted p-value for the interaction term (FR-008). |

### 2.6. OODTestVector
Represents the out-of-distribution holdout set.

| Field | Type | Description |
| :--- | :--- | :--- |
| `ood_id` | string | Unique ID. |
| `clip_id` | string | FK to AudioClip. |
| `model_name` | string | ASR model name. |
| `snr` | float | SNR value (randomly sampled outside training grid). |
| `rt60` | float | RT60 value (randomly sampled outside training grid). |
| `actual_hvcm` | float | The measured HVCM for this OOD point. |

## 3. File Formats & Storage

*   **Raw Data**: Parquet files in `data/raw/`.
*   **Derived Data**: Parquet files in `data/derived/`.
    *   `stress_curves.parquet`: Contains `StressCurveRecord`.
    *   `collapse_points.parquet`: Contains `CollapseIntensity`.
    *   `regression_input.parquet`: Contains `RegressionInput`.
    *   `ood_test.parquet`: Contains `OODTestVector`.
*   **Validation**: `validation_subset.csv` for human-annotated SSS correlation.

## 4. Data Flow

1.  **Ingestion**: `AudioClip` data loaded from source datasets.
2.  **Transformation**: `DistortionVector` applied to `AudioClip` → `StressCurveRecord`.
3.  **Derivation**: `StressCurveRecord` filtered → `CollapseIntensity`.
4.  **Human Annotation**: `StressCurveRecord` (subset) → `human_validated_margin` (HVCM).
5.  **Feature Engineering**: `CollapseIntensity` + `DistortionVector` → `RegressionInput`.
6.  **OOD Generation**: Random sampling → `OODTestVector`.
7.  **Analysis**: `RegressionInput` used for model training and sensitivity analysis.