# Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

This project implements an automated science pipeline to predict cognitive load from EEG data using spectral power features (theta/alpha ratios) derived from the OpenNeuro `ds000246` dataset.

## Prerequisites

- Python 3.11+
- pip
- At least 8GB RAM (recommended 16GB for full dataset processing)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Ensure the dataset is available. The pipeline will automatically download `ds000246` if not present, or you can manually download it to `data/raw`.

## Quickstart

Run the full pipeline from data ingestion to model evaluation:

```bash
python code/main.py --data-dir data/processed --output-dir results
```

This command will:
1. Verify dataset integrity and presence of `gaze.tsv`
2. Apply bandpass filtering and ICA artifact removal
3. Segment data into epochs aligned with behavioral events
4. Extract spectral power features (theta/alpha bands)
5. Generate cognitive load labels from gaze variance
6. Train a Ridge Regression model with subject-wise cross-validation
7. Perform channel importance analysis and sensitivity testing
8. Save all results to the `results/` directory

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration loading
│ ├── main.py # Pipeline orchestration
│ ├── data/
│ │ ├── download.py # Dataset download and verification
│ │ ├── loader.py # Chunked data loading
│ │ ├── preprocess_filter.py
│ │ ├── preprocess_ica.py
│ │ └── preprocess_epoch.py
│ ├── features/
│ │ ├── extract.py # PSD and feature extraction
│ │ ├── labels.py # Cognitive load label generation
│ │ └── validity.py # Data validity checks
│ └── models/
│ ├── split.py # Subject-wise data splitting
│ ├── train.py # Model training
│ ├── evaluate.py # Model evaluation and importance analysis
│ └── sensitivity.py # Sensitivity analysis
├── data/
│ ├── raw/ # Raw downloaded dataset
│ └── processed/ # Cleaned and processed data
├── results/ # Output reports and metrics
├── specs/ # Design documents
├── requirements.txt # Python dependencies
├── pipeline_config.yaml # Processing parameters
└── README.md # This file
```

## Output Files

After successful execution, the `results/` directory will contain:

- `verification_report.json`: Dataset verification status
- `power_analysis_report.json`: Statistical power analysis results
- `memory_check_report.json`: Memory usage validation
- `manifest.yaml`: Dataset manifest with checksums
- `channel_importance.json`: Channel/band importance with statistical corrections
- `model_metrics.json`: Final model performance metrics (R², RMSE)
- `sensitivity_report.csv`: Sensitivity analysis across window sizes

## Configuration

Processing parameters are defined in `pipeline_config.yaml`. Key parameters include:
- Bandpass filter settings (high-pass and low-pass frequencies)
- ICA component rejection criteria
- Epoch duration and overlap
- Cognitive load window sizes for sensitivity analysis

## License

This project is for research purposes only.
