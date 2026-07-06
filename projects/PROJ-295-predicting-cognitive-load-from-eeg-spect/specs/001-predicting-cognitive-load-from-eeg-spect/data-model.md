# Data Model: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

## Entities

### EEG Epoch
A time-locked segment of EEG data associated with a specific video stimulus and behavioral event.

**Attributes**:
- `epoch_id`: Unique identifier (string)
- `subject_id`: Participant identifier (string)
- `stimulus_id`: Video stimulus identifier (string)
- `start_time`: Epoch start time in seconds (float)
- `duration`: Epoch duration in seconds (float)
- `channels`: List of channel names (list of strings)
- `data_shape`: Shape of EEG data array [channels, timepoints] (list of integers)
- `artifact_clean`: Boolean indicating ICA cleaning status (boolean)

### Spectral Feature Vector
A vector containing the log-transformed relative power values for theta and alpha bands across all EEG channels for a single epoch.

**Attributes**:
- `feature_id`: Unique identifier (string)
- `epoch_id`: Reference to EEG Epoch (string)
- `subject_id`: Participant identifier (string)
- `theta_power`: Dictionary mapping channel → log relative theta power (dict)
- `alpha_power`: Dictionary mapping channel → log relative alpha power (dict)
- `theta_alpha_ratio`: Dictionary mapping channel → theta/alpha power ratio (dict)

### Cognitive Load Label
A continuous numerical value derived from gaze variance representing the estimated mental effort for a given epoch.

**Attributes**:
- `label_id`: Unique identifier (string)
- `epoch_id`: Reference to EEG Epoch (string)
- `subject_id`: Participant identifier (string)
- `gaze_variance`: Variance of gaze coordinates within epoch (float)
- `normalized_load`: Min-max scaled cognitive load score (float, range 0–1)
- `timestamp`: Epoch timestamp in seconds (float)

### Stimulus Feature Vector
A vector containing video-level features computed for each epoch to control for stimulus-driven effects.

**Attributes**:
- `stimulus_feature_id`: Unique identifier (string)
- `epoch_id`: Reference to EEG Epoch (string)
- `subject_id`: Participant identifier (string)
- `global_luminance`: Average luminance of the video frame (float)
- `cut_rate`: Number of cuts per second in the epoch (float)
- `motion_energy`: Total motion energy in the epoch (float)

## Data Flow

1. **Raw Data** → `download_data.py`: Fetches OpenNeuro ds000246 parquet files.
2. **Preprocessed Data** → `preprocess_eeg.py`: Applies filtering, downsampling, ICA; outputs clean epochs.
3. **Stimulus Features** → `compute_stimulus_features.py`: Extracts video features; outputs stimulus feature vectors.
4. **Feature Extraction** → `extract_features.py`: Computes PSD, extracts theta/alpha power; outputs feature vectors.
5. **Label Generation** → `extract_features.py`: Computes gaze variance, normalizes; outputs cognitive load labels.
6. **Model Training** → `train_model.py`: Trains Ridge Regression; outputs model weights and predictions.
7. **Evaluation** → `evaluate_results.py`: Computes metrics; outputs results table and plots.

## Storage Format

- **Raw data**: Parquet files from OpenNeuro (preserved in `data/raw/`)
- **Processed epochs**: HDF5 files in `data/processed/epochs.h5`
- **Feature matrices**: NumPy `.npy` files in `data/processed/features.npy`
- **Labels**: CSV file in `data/processed/labels.csv`
- **Stimulus Features**: CSV file in `data/processed/stimulus_features.csv`
- **Model artifacts**: Pickle file in `data/processed/model.pkl`
- **Results**: JSON file in `data/processed/results.json`

## Validation Rules

- **EEG Epoch**: `artifact_clean` must be True for inclusion in analysis.
- **Spectral Feature Vector**: All power values must be finite (no NaN/Inf).
- **Cognitive Load Label**: `normalized_load` must be in [0, 1] range.
- **Alignment**: Epoch timestamps must match behavioral logs within 100ms tolerance.
- **Stimulus Feature Vector**: All features must be finite and non-negative.