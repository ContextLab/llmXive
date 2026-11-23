# Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

This project implements a pipeline to predict cognitive load from EEG spectral power changes using the OpenNeuro ds000246 dataset.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-295-predicting-cognitive-load-from-eeg-spect
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Set up virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

## Data Preparation

Before running the main pipeline, ensure the dataset is downloaded and verified:

```bash
python code/data/download.py
python code/data/verify_dataset.py
```

This will:
- Download the OpenNeuro ds000246 dataset
- Verify the presence of required files (EEG data, gaze.tsv)
- Generate a manifest with checksums

## Quickstart

Run the full pipeline end-to-end:

```bash
python code/main.py --data-dir data/processed --output-dir results
```

This command will:
1. Load and preprocess EEG data (filtering, ICA artifact removal, epoching)
2. Extract spectral power features (theta/alpha bands)
3. Generate cognitive load labels from gaze variance
4. Train a Ridge Regression model with subject-wise cross-validation
5. Perform statistical validation (permutation tests, baseline comparison)
6. Generate comprehensive reports in the `results/` directory

## Project Structure

```
PROJ-295-predicting-cognitive-load-from-eeg-spect/
├── code/
│ ├── config.py # Configuration loading
│ ├── data/ # Data ingestion and preprocessing
│ │ ├── download.py # Dataset download
│ │ ├── loader.py # Chunked data loading
│ │ ├── preprocess_filter.py
│ │ ├── preprocess_ica.py
│ │ ├── preprocess_epoch.py
│ │ └──...
│ ├── features/ # Feature extraction
│ │ ├── extract.py # PSD calculation
│ │ ├── labels.py # Cognitive load labels
│ │ └──...
│ ├── models/ # Model training and evaluation
│ │ ├── train.py # Ridge Regression training
│ │ ├── evaluate.py # Statistical validation
│ │ └──...
│ ├── main.py # Pipeline orchestration
│ └── utils/ # Utility functions
├── data/
│ ├── raw/ # Raw downloaded dataset
│ └── processed/ # Preprocessed data
├── results/ # Output reports and figures
├── specs/ # Design documents
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
├── pipeline_config.yaml # Pipeline configuration
└── README.md # This file
```

## Output Files

After successful execution, the following files will be generated in `results/`:

- `verification_report.json`: Dataset verification status
- `power_analysis_report.json`: Statistical power analysis
- `memory_check_report.json`: Memory usage validation
- `channel_importance.json`: Channel/band correlation analysis
- `sensitivity_report.csv`: Window size sensitivity analysis
- `permutation_test.json`: Permutation test results
- `baseline_comparison.json`: Model vs. mean-baseline comparison
- `model_metrics.json`: Final aggregated metrics
- `runtime_profile.json`: Execution time profiling

## Configuration

Edit `pipeline_config.yaml` to customize:
- Signal processing parameters (bandpass filters, ICA settings)
- Feature extraction bands (theta: 4-8 Hz, alpha: 8-13 Hz)
- Model hyperparameters (Ridge alpha values)
- Window sizes for sensitivity analysis

## Testing

Run unit tests:
```bash
python -m pytest tests/unit/ -v
```

Run integration tests:
```bash
python -m pytest tests/integration/ -v
```

## License

This project is for research purposes only.
