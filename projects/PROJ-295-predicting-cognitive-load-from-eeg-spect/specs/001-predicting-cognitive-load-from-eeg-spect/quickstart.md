# Quickstart: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

## Prerequisites

- Python 3.11+
- 7 GB RAM minimum
- 14 GB disk space minimum
- Git

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/your-repo.git
cd your-repo/projects/PROJ-295-predicting-cognitive-load-eeg

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Data Download

```bash
# Download OpenNeuro ds000246 dataset
python code/download_data.py
```

This script:
- Fetches data from verified OpenNeuro source
- Validates checksum against `data/manifest.json`
- Stores raw data in `data/raw/`

## Preprocessing

```bash
# Run EEG preprocessing pipeline
python code/preprocess_eeg.py
```

This script:
- Applies 1–45 Hz bandpass filter
- Downsamples to 250 Hz
- Removes 50/60 Hz line noise
- Performs ICA artifact removal
- Validates output against `eeg-epoch.schema.yaml`
- Outputs clean epochs to `data/processed/epochs.h5`

## Stimulus Feature Extraction

```bash
# Extract video features for stimulus control
python code/compute_stimulus_features.py
```

This script:
- Computes global luminance, cut rate, and motion energy from video files
- Outputs stimulus feature vectors to `data/processed/stimulus_features.csv`

## Feature Extraction & Label Generation

```bash
# Extract spectral features and generate cognitive load labels
python code/extract_features.py
```

This script:
- Computes PSD using Welch's method
- Extracts theta/alpha log-transformed relative power
- Generates cognitive load proxy from gaze variance
- Validates output against `spectral-feature-vector.schema.yaml` and `cognitive-load-label.schema.yaml`
- Outputs feature matrix and labels to `data/processed/`

## Model Training & Evaluation

```bash
# Train Ridge Regression model and evaluate performance
python code/train_model.py
python code/evaluate_results.py
```

These scripts:
- Split data by subject using Leave-One-Subject-Out (LOSO) CV
- Tune alpha via 5-fold CV within training folds
- Train Ridge Regression model with stimulus features as covariates
- Compute Pearson correlation, RMSE, permutation baseline
- Apply FDR or cluster-based correction for multiple comparisons
- Output results to `data/processed/results.json`

## Running Tests

```bash
# Execute unit tests
pytest tests/
```

## Monitoring Resources

```bash
# Monitor memory usage during preprocessing
python -m memory_profiler code/preprocess_eeg.py
```

## Troubleshooting

- **Memory error**: Ensure chunked loading is enabled; reduce batch size.
- **Missing behavioral logs**: Check dataset manifest; re-run download script.
- **Numerical instability**: Verify epsilon added to denominators in ratio calculations.
- **Runtime exceeded**: Reduce number of subjects or epochs; verify downsampling applied; check video feature extraction efficiency.