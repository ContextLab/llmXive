# Evaluating Resting-State fMRI Entropy as a Biomarker for Attention-Deficit Traits

This project implements a pipeline to evaluate sample entropy of resting-state fMRI signals as a biomarker for ADHD traits, comparing it against functional connectivity baselines.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
# Create and activate virtual environment
python3 -m venv code/.venv
source code/.venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

## Quickstart

Run the full pipeline from data fetching to model evaluation with a single command:

```bash
python code/main.py
```

This will:
1. Fetch the ADHD-200 dataset from OpenNeuro
2. Preprocess fMRI data (motion correction, scrubbing, truncation)
3. Compute sample entropy features for each parcel
4. Train and evaluate predictive models (Ridge Regression, Logistic Ridge)
5. Perform statistical validation (permutation testing, sensitivity analysis)
6. Generate all output artifacts in `data/` and `data/derived/`

## Project Structure

```
.
├── code/
│ ├── config.py # Hyperparameters and configuration
│ ├── data_loader.py # OpenNeuro dataset fetching
│ ├── preprocessing.py # FD calculation, scrubbing, truncation
│ ├── entropy_engine.py # Sample entropy computation
│ ├── connectivity_engine.py # Functional connectivity and PCA
│ ├── modeling.py # Model training and evaluation
│ ├── validation.py # Permutation testing, FDR, sensitivity
│ ├── main.py # Pipeline orchestration
│ └── requirements.txt # Dependencies
├── data/
│ ├── raw/ # Raw downloaded data and logs
│ ├── processed/ # Preprocessed NIfTI and feature CSVs
│ └── derived/ # Aggregated statistics and model metrics
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── README.md
```

## Output Artifacts

After successful execution, the following key artifacts will be generated:

- `data/derived/valid_subjects.csv` - List of valid subjects with metadata
- `data/derived/subject_fd_stats.csv` - Motion statistics for all subjects
- `data/processed/subject_entropy_features.csv` - Primary entropy feature matrix
- `data/derived/connectivity_features_baseline.csv` - Connectivity baseline features
- `data/derived/model_metrics.json` - Aggregated model performance metrics
- `data/derived/motion_confound_report.json` - Motion confound analysis results

## Configuration

Edit `code/config.py` to adjust hyperparameters:
- `m`: Embedding dimension for sample entropy (default: 2)
- `r_factor`: Tolerance parameter scaling factor (default: 0.2)
- `fd_threshold`: Framewise displacement threshold for scrubbing (default: 0.2)
- `target_length`: Target number of volumes after truncation (default: 120)
- `atlas_n`: Number of parcels in the atlas (default: 200)

## License

This project is part of the llmXive automated science pipeline.