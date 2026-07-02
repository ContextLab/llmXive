# Data Model: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

## Entity-Relationship Overview

The data model defines the transformation from raw signals to statistical results.

1.  **Participant**: The atomic unit of analysis.
2.  **EEGFeature**: Aggregated power values per band per participant (CLR-transformed).
3.  **BehavioralMetric**: Reaction time statistics per participant.
4.  **ModelResult**: Outputs from regression and correlation analyses.

## Schema Definitions

### 1. Participant (Derived)
*Represents a unique individual with valid EEG and RT data.*
- `participant_id` (str): Unique identifier.
- `eeg_duration_sec` (float): Duration of valid EEG recording.
- `channels_rejected` (int): Number of channels rejected due to variance.
- `trials_kept_pct` (float): Percentage of RT trials kept after outlier removal.
- `status` (str): "included" or "excluded".

### 2. EEGFeature (Derived)
*Relative power in canonical bands (CLR-transformed).*
- `participant_id` (str): FK to Participant.
- `delta_clr` (float): CLR-transformed relative power (0.5-4 Hz).
- `theta_clr` (float): CLR-transformed relative power (4-8 Hz).
- `alpha_clr` (float): CLR-transformed relative power (8-13 Hz).
- `beta_low_clr` (float): CLR-transformed relative power (13-20 Hz).
- `beta_high_clr` (float): CLR-transformed relative power (20-30 Hz).
- `gamma_clr` (float): CLR-transformed relative power (30-40 Hz).
- `total_power` (float): Sum of absolute power across 1-40 Hz.

### 3. BehavioralMetric (Derived)
*Reaction time summary.*
- `participant_id` (str): FK to Participant.
- `median_rt_ms` (float): Median reaction time in milliseconds.
- `std_rt_ms` (float): Standard deviation of RT.
- `n_trials` (int): Number of trials after outlier exclusion.

### 4. ModelResult (Derived)
*Statistical outputs.*
- `model_type` (str): "linear" or "lasso".
- `r_squared` (float): Coefficient of determination.
- `adjusted_r_squared` (float): Adjusted R² value.
- `rmse` (float): Root Mean Square Error.
- `p_value_permutation` (float): P-value from a shuffle test (test-set only).
- `alpha_coef` (float): Coefficient for alpha band (if non-zero).
- `bonferroni_p` (float): Bonferroni-corrected p-value for alpha correlation.
- `significant` (bool): True if `bonferroni_p` < 0.0083.
- `optimal_lambda` (float): Optimal regularization parameter from CV.
- `non_linear_p_value` (float): P-value from F-test comparing linear vs. polynomial model.
- `mdes_n_required` (int): Minimum sample size required to detect R²=0.10 with power ≥ 0.80.

## Data Flow

1.  **Raw Input**: `data/raw/eeg.parquet`, `data/raw/rt.parquet`.
2.  **Preprocessing**:
    - Filter → ICA → PSD Calculation (short-duration windows with overlapping segments).
    - Output: `data/interim/eeg_features_raw.csv` (Absolute power).
3.  **Feature Aggregation**:
    - Calculate Relative Power (Band / Total).
    - **Apply CLR Transformation**.
    - Merge with RT data (on `participant_id`).
    - Filter by inclusion criteria (ratio of rejected channels <= 0.30, trials_kept_pct >= 0.70).
    - Output: `data/processed/features.csv` (Final analysis table with CLR features).
4.  **Modeling**:
    - Split into Train/Test using a standard majority-minority partition.
    - Fit Linear & LASSO.
    - Output: `data/processed/model_results.json`.
5.  **Robustness**:
    - Re-run with 2s windows / no ICA.
    - Output: `data/processed/robustness.csv`.

## Constraints & Invariants

- **Inclusion**: `trials_kept_pct` >= 0.70 AND `channels_rejected / total_channels` <= 0.30.
- **RT Range**: `median_rt_ms` must be between 150ms and 1000ms (physiologically plausible).
- **Relative Power**: Sum of `delta_rel` + ... + `gamma_rel` must be ≈ 1.0 (within floating point tolerance).
- **No PII**: No names, DOBs, or location data in any derived file.