# Data Model: Investigate Brain Network Dynamics and VR Therapy Response

## 1. Conceptual Model

The data model tracks the lifecycle of a subject from raw scan to final statistical result.

### Entities

1.  **Subject**: An individual participant.
    -   `subject_id`: Unique identifier (string).
    -   `group`: (e.g., "VR_Therapy", "Control" if applicable).
    -   `age`: Integer.
    -   `sex`: String (M/F/Other).
    -   `medication_status`: String (None, SSRI, etc.).
    -   `pre_treatment_score`: Float (Anxiety scale).
    -   `post_treatment_score`: Float (Anxiety scale).
    -   `instrument_name`: String (e.g., "GAD-7").
    -   `motion_metrics`: Dict (mean_fd, max_translation, max_rotation).
    -   `exclusion_reason`: String (null if included).

2.  **Scan**: A single fMRI acquisition.
    -   `scan_id`: Unique identifier.
    -   `subject_id`: FK to Subject.
    -   `timepoint`: Enum ("pre", "post").
    -   `file_path_raw`: Path to NIfTI.
    -   `file_path_processed`: Path to preprocessed NIfTI.
    -   `checksum`: SHA256 string.

3.  **NetworkMetric**: Computed graph properties.
    -   `metric_id`: Unique identifier.
    -   `subject_id`: FK to Subject.
    -   `timepoint`: Enum ("pre", "post").
    -   `atlas`: String (e.g., "Schaefer100").
    -   `modularity_q`: Float.
    -   `global_efficiency`: Float.
    -   `local_efficiency`: Float.
    -   `valid`: Boolean (False if NaN or out of bounds).

4.  **AnalysisResult**: Statistical outcomes.
    -   `result_id`: Unique identifier.
    -   `metric_type`: String ("modularity", "global_efficiency", "local_efficiency").
    -   `coefficient`: Float.
    -   `p_value_uncorrected`: Float.
    -   `p_value_corrected`: Float.
    -   `effect_size`: Float (Cohen's d).
    -   `model_type`: String ("ANCOVA_State", "Linear_Exploratory", "Delta_Delta_Exploratory").
    -   `is_significant`: Boolean.
    -   `framing`: String ("associational", "causal").
    -   `collinearity_flag`: Boolean (True if VIF > 5 detected).

## 2. Data Flow

1.  **Ingestion**: Raw NIfTI -> `data/raw/`.
2.  **Validation**: Check metadata for `pre_treatment_score` and `post_treatment_score`.
3.  **Preprocessing**: Raw -> `data/processed/`.
4.  **Computation**: Processed -> `data/metrics/` (CSV).
5.  **Analysis**: Metrics + Scores + Mean FD -> `data/results/` (JSON/CSV).
6.  **Reporting**: Results -> `paper/` figures.

## 3. Constraints & Rules

-   **Immutability**: Raw files in `data/raw/` are never overwritten.
-   **Checksums**: Every file in `data/` must have a corresponding checksum entry in the state file.
-   **Bounds**:
    -   `modularity_q`: Must be in [0, 1].
    -   `efficiency`: Must be >= 0 and finite.
-   **Collinearity**: **Ridge regression is NOT used**. If VIF > 5, the model is run but flagged as "High Collinearity". The primary strategy is Pre-specified Univariate models. **Spec update required to remove Ridge mandate.**
-   **Framing**: If `study_design` != "randomized", all `is_significant` findings must be labeled as "associational".
-   **Primary Outcome**: `post_treatment_score` (State). `change_score` (Delta) is secondary/exploratory.
-   **Motion Control**: Mean FD is included as a mandatory covariate in all regression models to control for residual motion artifacts.
