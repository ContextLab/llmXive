# Data Model: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Entities

### 1. EEG Epoch
Represents a continuous window of EEG data.
*   **subject_id**: Unique identifier for the participant.
*   **condition**: Resting-state or Task.
*   **channels**: List of channel names (e.g., C3, C4).
*   **sampling_rate**: Float (Hz).
*   **data**: 2D array (channels × timepoints).
*   **metadata**: Dictionary containing filter settings, reference type, and bad channel flags.

### 2. tDCS Response
Represents the behavioral outcome for a subject.
*   **subject_id**: Unique identifier (must match EEG).
*   **pre_score**: Float (Baseline motor task score).
*   **post_score**: Float (Post-tDCS motor task score).
*   **response_pct**: Float (Percentage change: `(post - pre) / pre * 100`).
*   **mode**: String (`"Primary"` or `"Fallback"`).

### 3. Feature Vector
Aggregated metrics for one subject.
*   **subject_id**: Unique identifier.
*   **power_features**: Dictionary mapping band (delta, theta, alpha, beta, gamma) to power values.
*   **connectivity_features**: Dictionary mapping channel pairs to PLV/wPLI values.
*   **mode**: String (`"Primary"` or `"Fallback"`).

### 4. Model Output
Results of the regression analysis.
*   **coefficients**: Dictionary mapping features to coefficients.
*   **r_squared**: Float (Adjusted R²).
*   **p_values**: Dictionary mapping features to uncorrected p-values.
*   **fdr_p_values**: Dictionary mapping features to FDR-corrected p-values (Benjamini-Hochberg).
*   **is_valid_inference**: Boolean (False if in Fallback Mode).
*   **permutation_p_value**: Float (Significance of the model vs. null).
*   **positive_control_r2**: Float (R² from the positive control step, if applicable).
*   **stability_variance**: Float (Variance of binary significance outcome across sensitivity sweep).
*   **power_analysis_flag**: String (`"Underpowered"`, `"Adequate"`, `"N/A"`).

## Data Flow

1.  **Raw Data** (PhysioNet/OpenNeuro) → `data/raw/`
2.  **Preprocessing** → `data/processed/epochs.fif` (MNE format)
3.  **Feature Extraction** → `data/processed/features.parquet`
4.  **Modeling** → `data/processed/model_results.json`
5.  **Validation** → `data/reports/sensitivity_analysis.csv`

## Constraints

*   **RAM Limit**: Feature matrices must be stored as `float32` to minimize memory footprint.
*   **Data Integrity**: Raw data files must not be modified. All transformations create new files.
*   **Mode Flag**: Every output artifact must explicitly state the mode (`Primary` or `Fallback`).
*   **Feature Constraint**: Connectivity pairs limited to top 50 by variance to prevent p >> n.