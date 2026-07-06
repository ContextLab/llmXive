# Data Model: Neural Correlates of Error Monitoring

## 1. Conceptual Model

The data model consists of three primary entities:
1.  **Participant**: Unique subject in the study.
2.  **Error Event**: A specific instance of navigation deviation, characterized by time, magnitude, and associated EEG.
3.  **EEG Epoch**: The time-locked neural signal segment extracted for an error event.

### Relationships
*   1 Participant -> N Error Events
*   1 Error Event -> 1 EEG Epoch (aggregated across channels)

## 2. Physical Schema

### 2.1 Raw Data (External)
*   **Format**: CSV or Parquet (as per dataset).
*   **Structure**:
    *   `participant_id` (int)
    *   `timestamp` (float)
    *   `channel_name` (str)
    *   `amplitude` (float)
    *   `error_event_id` (int, optional)
    *   `error_magnitude` (float, degrees)

### 2.2 Processed Data (Internal)
*   **File**: `data/processed/epochs_summary.parquet`
*   **Schema**:
    *   `participant_id`: Integer, PK
    *   `event_id`: Integer, PK
    *   `error_magnitude_deg`: Float (Predictor)
    *   `mfn_mean_amplitude_fcz`: Float (Outcome - Mean in 200-400ms)
    *   `mfn_mean_amplitude_cz`: Float (Outcome)
    *   `mfn_mean_amplitude_fz`: Float (Outcome)
    *   `n_artifacts_removed`: Integer
    *   `included_in_analysis`: Boolean

### 2.3 Output Data (Results)
*   **File**: `results/models/primary_model_summary.json`
*   **Schema**:
    *   `model_type`: String ("LMM" or "GAM")
    *   `coefficients`: Object (fixed effects)
    *   `random_effects_variance`: Float
    *   `p_value_error_magnitude`: Float
    *   `r_squared`: Float
    *   `vif_scores`: Object
    *   `bonferroni_adjusted_p`: Float
    *   `aic_score`: Float
    *   `bic_score`: Float

### 2.4 Sensitivity Analysis Output (New Artifact for SC-002)
*   **File**: `results/diagnostics/sensitivity_summary.json`
*   **Schema**:
    *   `thresholds`: List of integers (5, 10, 15, 20)
    *   `results`: List of objects, each containing:
        *   `threshold`: Integer
        *   `n_events`: Integer
        *   `correlation_coefficient`: Float
        *   `p_value`: Float
        *   `bonferroni_adjusted_p`: Float
        *   `significant`: Boolean
    *   `stability_summary`: String (e.g., "Significant at 3/4 thresholds")

## 3. Data Flow

1.  **Ingest**: `download.py` fetches raw data -> `data/raw/`.
2.  **Preprocess**: `preprocess.py` reads raw -> applies filters/ICA -> extracts epochs -> calculates angular deviation -> writes `data/processed/epochs_summary.parquet`.
3.  **Analyze**: `analysis.py` reads `epochs_summary.parquet` -> fits models -> performs sensitivity sweep -> checks diagnostics -> writes `results/`.
4.  **Visualize**: `viz.py` reads `results/` -> writes `results/figures/`.

## 4. Constraints & Validation

*   **Error Magnitude**: Must be >= 0.
*   **MFN Amplitude**: Expected negative values (microvolts).
*   **Missing Data**: Rows with missing `error_magnitude` or `mfn_mean_amplitude` are dropped and logged.
*   **Participant Exclusion**: Participants with < 10 valid error events are excluded from the LMM.
*   **Feasibility**: Runtime and memory usage must be logged and reported in `results/diagnostics/feasibility_report.json`.