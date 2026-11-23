# Data Sources and Acquisition

This document describes the real-world datasets used in the cognitive fatigue prediction pipeline,
their acquisition methods, and validation requirements.

## Primary Dataset: Sleep-EDF (STUDY: Sleep-EDF-Expanded)

The pipeline primarily utilizes the **Sleep-EDF Expanded** dataset from PhysioNet.
This dataset contains polysomnographic recordings with EEG channels suitable for complexity analysis.

### Dataset Details

- **Source**: PhysioNet (https://physionet.org/content/sleep-edfx/)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Format**: EDF+ (European Data Format)
- **Channels**: Fpz-Cz, Pz-Oz (EEG), EOG, EMG, ECG
- **Sampling Rate**: 100 Hz
- **Duration**: Full night sleep recordings (approx. 15-20 hours per subject)
- **Subjects**: 153 healthy subjects (83 with sleep onset insomnia, 70 controls)

### Required Variables

Per FR-001, the dataset metadata must contain the following variables:
- `pre_fatigue`: Baseline fatigue score (measured before sleep)
- `post_fatigue`: Post-sleep fatigue score (measured upon awakening)
- `subject_id`: Unique identifier for each participant
- `age`: Age of the participant (for covariate analysis)
- `sex`: Biological sex (for covariate analysis)

**Note**: If the primary Sleep-EDF dataset lacks the required fatigue rating columns,
the pipeline will attempt to fetch the **SHHS (Sleep Heart Health Study)** dataset as a fallback,
which includes home sleep studies with self-reported fatigue measures.

### Acquisition Script

Data is fetched programmatically via `code/download.py` using the `datasets` library:

```bash
python code/download.py
```

This script:
1. Validates the presence of required variables (pre/post fatigue ratings).
2. Checks participant count (N ≥ 30 required).
3. Downloads raw EDF+ files to `data/raw/`.
4. Generates a `validation_report.json` if validation fails.

### Validation Requirements

The download script enforces strict validation per FR-001:
- **Variable Check**: Must find `pre_fatigue` and `post_fatigue` columns.
- **Sample Size**: Must have at least 30 participants with complete data.
- **Data Integrity**: Files must be readable by MNE-Python.

If validation fails, the script exits with code 1 and logs the error:
`ERROR: No valid dataset found with required variables.`

## Data Directory Structure

```
data/
├── raw/
│ └── sleep-edfx/ # Downloaded EDF+ files
│ ├── SC001.edf
│ ├── SC002.edf
│ └──...
├── processed/
│ ├── cleaned_eeg.fif # Preprocessed data (MNE format)
│ ├── lzc_metrics.csv # Lempel-Ziv Complexity per channel
│ └── pe_metrics.csv # Permutation Entropy per channel
└── results/
 ├── correlation_results.csv
 └── sensitivity_table.csv
```

## Data Preprocessing Pipeline

Raw data undergoes the following transformations (see `code/preprocess.py`):

1. **Bandpass Filtering**: 1–40 Hz to remove slow drifts and high-frequency noise.
2. **Notch Filtering**: 50 Hz to remove line noise.
3. **Artifact Rejection**:
 - Amplitude threshold: > ±100 µV
 - Minimum segment length: 120 seconds
4. **Epoching**: Segmentation into fixed-length windows for feature extraction.

Output: `data/processed/cleaned_eeg.fif`

## Data Quality Assurance

- **Exclusion Log**: `logs/exclusion_log.csv` tracks rejected participants and reasons.
- **Rejection Summary**: Aggregated statistics on artifact rejection rates.
- **Validation Report**: `data/processed/validation_report.json` confirms dataset integrity.

## Alternative Sources

If the primary source is unavailable or fails validation:
1. **SHHS (Sleep Heart Health Study)**: Large-scale home sleep study with fatigue measures.
2. **MASS (Montreal Archive of Sleep Studies)**: Another potential source with EEG and behavioral data.

The pipeline is designed to fail loudly if no real, valid source is found, ensuring no synthetic data is used.
