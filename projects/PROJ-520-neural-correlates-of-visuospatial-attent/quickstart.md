# Quickstart Guide

## Prerequisites

- Python 3.8+
- pip
- Access to OpenNeuro dataset (ds0001171)

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

Run the full pipeline end-to-end:
```bash
python code/main.py --task all
```

Or run individual stages:
```bash
python code/main.py --task download
python code/main.py --task preprocess
python code/main.py --task features
python code/main.py --task classify
```

## Data Integrity

**Fail Loudly Policy**: This pipeline is configured to fail immediately if:
- The real OpenNeuro dataset cannot be downloaded.
- Required event markers are missing and no valid fallback is found.
- Sample size requirements (<100 epochs/condition) are not met.
- Resource limits (CPU/RAM) are exceeded.

**No Synthetic Data**: Do not attempt to run this pipeline with synthetic or mock data. All analysis requires real EEG data from OpenNeuro.

## Output Artifacts

After successful execution, the following files will be generated in `data/processed/`:
- `epochs_cleaned.fif`: Preprocessed epochs.
- `features_matrix.csv`: Extracted feature matrix.
- `feature_metadata.json`: Correlation and metadata report.
- `results.json`: Classification and statistical results.

## Troubleshooting

- **Import Errors**: Ensure `code/` is in your Python path or run from the project root.
- **Memory Errors**: The pipeline enforces limits. If you hit limits, reduce `max_memory_gb` in config or use a machine with more RAM.
- **Download Failures**: Check your internet connection and ensure OpenNeuro is accessible.