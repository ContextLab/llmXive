# Data Model: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Entities & Relationships

### AudioClip
*   **ID**: Unique identifier (UUID or hash).
*   **Source**: Dataset name (e.g., "ami", "commonvoice").
*   **Path**: Local file path to raw audio.
*   **Speaker_ID**: Identifier for speaker stratification.
*   **Duration**: Length in seconds.
*   **Transcript**: Ground truth text.

### DistortionVector
*   **ID**: Composite key (AudioClip_ID + SNR + RT60).
*   **SNR**: Signal-to-Noise Ratio in dB (float).
*   **RT60**: Reverberation time in seconds (float).
*   **Scenario_Index**: Integer (1-54).

### StressCurve
*   **AudioClip_ID**: FK to AudioClip.
*   **DistortionVector_ID**: FK to DistortionVector.
*   **Model_Name**: ASR model used (e.g., "whisper-tiny").
*   **SSS**: Semantic Similarity Score (float, 0.0-1.0).
*   **WER**: Word Error Rate (float, 0.0-1.0+).
*   **Composite_Score**: Weighted average of SSS and Phoneme Edit Distance.
*   **Hypothesis**: ASR output text.
*   **Reference**: Ground truth text.
*   **Curve_Type**: String ("sigmoid", "linear").
*   **Max_Derivative**: Float (maximum negative derivative of SSS).

### CollapseIntensity
*   **AudioClip_ID**: FK.
*   **Model_Name**: ASR model.
*   **Collapse_Step**: The index of the distortion vector where collapse occurred.
*   **Collapse_Intensity**: The interpolated intensity value (float).
*   **Reason**: "Inflection", "Threshold", "None".
*   **Sensitivity_Flag**: Boolean (true if sensitivity analysis varied this point).
*   **Curve_Type**: String ("sigmoid", "linear").

### CriticalInteractionVector
*   **Model_Name**: ASR model.
*   **Coefficients**: JSON blob of regression coefficients (SNR, RT60, Interaction).
*   **R2**: Model fit score.
*   **SHAP_Importance**: JSON blob of feature importances.
*   **FDR_Corrected**: Boolean.

## 2. Data Flow

1.  **Raw**: `data/raw/` (Downloaded Parquet files from HF).
2.  **Interim**: `data/interim/` (Stratified sample, generated distorted audio files `.wav`).
3.  **Derived**: `data/derived/` (Aggregated stress curves, collapse points, regression results).
    *   `stress_curves.parquet`
    *   `collapse_points.parquet` (Generated in Phase 2, T022)
    *   `regression_results.json`

## 3. Constraints

*   **Parquet**: All derived data must be stored in Parquet for efficient columnar access.
*   **Immutability**: Raw files are never modified.
*   **Checksums**: All files in `data/raw` and `data/derived` must have a `.sha256` sidecar file.
*   **Versioning**: `code/utils/versioning.py` must update `state/` YAML files with hashes of all derived files.
