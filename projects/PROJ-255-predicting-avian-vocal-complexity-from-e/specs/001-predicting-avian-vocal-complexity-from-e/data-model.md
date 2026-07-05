# Data Model: Predicting Avian Vocal Complexity from Environmental Noise Levels

## Entity Relationship Overview

The data model consists of four core entities: `Recording`, `NoiseProfile`, `VocalMetric`, and `ModelResult`. The flow is:
`Recording` (Raw) → `NoiseProfile` (Mapped) → `VocalMetric` (Extracted) → `ModelResult` (Aggregated).

## Entity Definitions

### 1. Recording
Represents a single audio file from Xeno-canto.
*   **Primary Key**: `recording_id` (string)
*   **Attributes**:
    *   `species_id` (string): Species code (e.g., "turdu1").
    *   `latitude` (float): Decimal degrees.
    *   `longitude` (float): Decimal degrees.
    *   `audio_file_path` (string): Local path to downloaded audio.
    *   `original_filename` (string): Original file name.
    *   `download_status` (string): "success", "failed", "skipped".

### 2. NoiseProfile
Represents the ambient noise context for a location.
*   **Primary Key**: `location_id` (string, derived from lat/long)
*   **Attributes**:
    *   `noise_level_db` (float): Estimated dB(A).
    *   `source_dataset` (string): "GlobalSoundscapes", "Interpolated", "Unknown".
    *   `interpolation_distance_km` (float): Distance to nearest neighbor (if interpolated).
    *   `latitude` (float), `longitude` (float): Coordinates.

### 3. VocalMetric
Extracted features from the audio file.
*   **Primary Key**: `recording_id` (string, FK to Recording)
*   **Attributes**:
    *   `syllable_count` (int): Number of detected syllables.
    *   `duration_seconds` (float): Total duration.
    *   `frequency_bandwidth_hz` (float): Difference between max and min frequency.
    *   `spectral_entropy` (float): Measure of spectral complexity.
    *   `snr_db` (float): Signal-to-Noise Ratio (calculated).
    *   `is_valid` (boolean): True if SNR > 10 dB.

### 4. ModelResult
Aggregated statistical output.
*   **Primary Key**: `metric_name` (string), `model_id` (string)
*   **Attributes**:
    *   `fixed_effect_coefficient` (float): Slope of noise vs. metric.
    *   `p_value` (float): Raw p-value.
    *   `p_value_corrected` (float): FDR/Bonferroni corrected.
    *   `effect_size` (float): Cohen's d.
    *   `random_effect_variance_species` (float).
    *   `random_effect_variance_location` (float).
    *   `r_squared_marginal` (float).
    *   `r_squared_conditional` (float).

## Data Flow & Transformations

1.  **Raw Ingestion**: `data/raw/` contains downloaded audio and a `metadata.csv` from Xeno-canto.
2.  **Noise Mapping**:
    *   Input: `metadata.csv`
    *   Process: Geocode lookup (Global Soundscapes or Interpolation).
    *   Output: `data/interim/noise_mapped.csv`.
3.  **Feature Extraction**:
    *   Input: `data/interim/noise_mapped.csv` + Audio files.
    *   Process: `librosa` extraction + SNR calculation.
    *   Output: `data/interim/vocal_metrics_raw.csv`.
4.  **Filtering**:
    *   Input: `vocal_metrics_raw.csv`.
    *   Process: Filter SNR > 10 dB, species count ≥ 5 per location.
    *   Output: `data/processed/final_dataset.csv`.
    *   Log: `data/processed/filtered_records.csv`.
5.  **Modeling**:
    *   Input: `final_dataset.csv`.
    *   Process: LME fitting, LOSO CV, Sensitivity Sweep.
    *   Output: `data/processed/model_results.csv`, `data/processed/sensitivity_analysis.csv`.

## Constraints & Rules

*   **SNR Threshold**: Records with `snr_db` ≤ 10.0 MUST be excluded from modeling (FR-004).
*   **Species Count**: Species with <5 valid recordings in a location MUST be excluded (FR-004).
*   **Interpolation**: If `source_dataset` == "Interpolated", `interpolation_distance_km` MUST be ≤ 50.0.
*   **Missing Data**: Any `NaN` in `noise_level_db` or `vocal_metrics` MUST be handled by exclusion (listwise deletion) or imputation (only if justified, default is exclusion).
