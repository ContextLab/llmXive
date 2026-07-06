# Data Model Specification

## Overview
This document defines the data structures, schemas, and relationships used throughout the pipeline.

## Core Entities

### Dataset
- `dataset_id`: Unique identifier (e.g., OpenNeuro ID).
- `subject_id`: Participant identifier.
- `trial_id`: Unique trial identifier.
- `stimulus_type`: "standard" or "deviant".
- `response_correctness`: "correct" or "incorrect" (nullable).
- `latency`: Stimulus onset latency in seconds.

### Preprocessed Data
- `raw_data`: Path to raw EEG file.
- `filtered_data`: Path to filtered EEG data.
- `epochs`: Array of epoched data (channels x time x trials).
- `bad_channels`: List of interpolated channel names.

### Aligned Data (Output of US2)
- `subject_id`: Participant identifier.
- `block_id`: Block identifier.
- `mmn_amplitude`: Mean difference wave amplitude (µV) in 150–250ms window.
- `accuracy`: Behavioral accuracy percentage for the aligned block.
- `source_window_start_trial`: The starting trial index of the 50-trial MMN calculation window.
- `analysis_mode`: "error_signal" or "stimulus_driven".
- `excluded`: Boolean flag indicating if the subject was excluded due to underpowering.

## Schemas

### validation_report.json
```yaml
type: object
properties:
 analysis_mode:
 type: string
 enum: [error_signal, stimulus_driven]
 underpowered_subjects:
 type: array
 items:
 type: string
 missing_metadata_datasets:
 type: array
 items:
 type: string
```

### aligned_data.csv
```csv
subject_id,block_id,mmn_amplitude,accuracy,source_window_start_trial,analysis_mode
sub-001,block-1,0.12,0.85,10,error_signal
```

### model_output.json
```yaml
type: object
properties:
 coefficients:
 type: object
 p_values:
 type: object
 fdr_corrected_p_values:
 type: object
 permutation_p_value:
 type: number
 robustness_metrics:
 type: object
```

## Methodological Corrections & Deviations
- **Lagged Alignment**: The data model explicitly includes `source_window_start_trial` to track the 50-trial window used for MMN calculation, which precedes the behavioral block.
- **Exclusion of Underpowered Subjects**: The `underpowered_subjects` list in `validation_report.json` and the `excluded` flag in `aligned_data.csv` document subjects excluded from the primary GLMM input due to insufficient power (<20 subjects or trials).
- **Gaussian LME**: The model output schema is updated to reflect Gaussian distribution assumptions rather than non-Gaussian alternatives.
