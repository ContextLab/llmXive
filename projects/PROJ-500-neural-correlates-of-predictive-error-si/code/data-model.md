# Data Model: Neural Correlates of Predictive Error

## Entities

### Subject
- `subject_id`: Unique identifier (string)
- `excluded_reason`: Optional string (e.g., "underpowered", "zero_accuracy", "artifact")
- `analysis_mode`: Enum ("error_signal", "stimulus_driven")

### Trial
- `trial_id`: Unique identifier
- `subject_id`: FK to Subject
- `stimulus_type`: Enum ("standard", "deviant")
- `response_correctness`: Boolean (True/False)
- `timestamp`: Float (seconds from start)

### Block
- `block_id`: Unique identifier
- `subject_id`: FK to Subject
- `start_trial`: Integer
- `end_trial`: Integer
- `accuracy`: Float (0.0 to 1.0)
- `mmn_amplitude`: Float (µV)
- `source_window_start_trial`: Integer (Start of the 50-trial lookback window for MMN calculation)
- `mmn_window_end_trial`: Integer (End of the 50-trial lookback window)

## Derived Artifacts

### `data/aligned_data.csv`
- Schema: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, `accuracy`, `analysis_mode`
- **Constraint:** Rows corresponding to underpowered subjects or zero-accuracy blocks must be excluded from the primary GLMM input set.

### `data/excluded_subjects.csv`
- Schema: `subject_id`, `reason`
- Contains subjects excluded due to underpowered data (<20 subjects threshold) or other quality flags.

### `data/validation_report.json`
- Contains `analysis_mode` determination and lists of `underpowered_subjects`.

## Methodological Corrections (Plan Phase 0.5)
- **Lagged Alignment:** The `mmn_amplitude` in a block is derived from trials `[block_start - 50, block_start - 10]`.
- **Gaussian LME:** The statistical model assumes a Gaussian distribution for the dependent variable (MMN Amplitude).
- **Exclusion:** Underpowered subjects are excluded from the final model but retained in the dataset for reporting.
