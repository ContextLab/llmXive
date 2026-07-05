# Cognitive Fatigue Prediction from Resting-State EEG Complexity

## Project Overview

This project investigates the relationship between resting-state EEG signal complexity
and cognitive fatigue levels. It implements a pipeline to download public EEG datasets,
preprocess the signals, extract complexity metrics (Lempel-Ziv Complexity and Permutation Entropy),
and analyze correlations with fatigue scores.

## Key Research Question

Does cognitive fatigue manifest as a phase transition in neural signal complexity,
characterized by either adaptive simplification or degenerative noise?

## Pipeline Phases

1. **Data Retrieval**: Fetch Sleep-EDF or SHHS datasets from PhysioNet
2. **Preprocessing**: Apply bandpass filtering (1-40 Hz) and artifact rejection
3. **Feature Extraction**: Calculate LZC and Permutation Entropy per channel
4. **Analysis**: Correlate complexity metrics with fatigue scores using statistical tests

## Directory Structure

```
projects/PROJ-470-predicting-cognitive-fatigue-from-restin/
├── code/
│ ├── config.yaml # Pipeline configuration
│ ├── download.py # Data retrieval scripts
│ ├── preprocess.py # Signal preprocessing
│ ├── features.py # Complexity metric calculation
│ ├── analysis.py # Statistical correlation analysis
│ ├── report.py # Report generation
│ ├── models/ # Data models
│ │ ├── __init__.py
│ │ ├── eeg_segment.py
│ │ └── complexity_metric.py
│ ├── utils/ # Utility functions
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Downloaded raw EEG data
│ ├── processed/ # Preprocessed EEG and extracted features
│ └── analysis/ # Analysis results and reports
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── docs/
 └── README.md # This file
```

## Usage

### Setup

1. Create a Python 3.11 virtual environment
2. Install dependencies: `pip install -r code/requirements.txt`
3. Verify environment: `python code/check_env.py`

### Running the Pipeline

```bash
# Download data
python code/download.py

# Preprocess EEG signals
python code/preprocess.py

# Extract complexity features
python code/features.py

# Run correlation analysis
python code/analysis.py

# Generate final report
python code/report.py
```

## Configuration

Pipeline parameters are defined in `code/config.yaml`:
- Filter cutoffs (1-40 Hz)
- Artifact rejection thresholds (±100µV)
- Dataset IDs and versions
- Statistical analysis parameters

## Dependencies

- mne: EEG data handling and preprocessing
- scikit-learn: Statistical tools
- lempel-ziv-complexity: LZC calculation
- scipy: Signal processing
- pandas/numpy: Data manipulation
- pyyaml: Configuration loading

## License

This project is for research purposes only.