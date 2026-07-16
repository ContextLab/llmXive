# Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## Project Overview
This project implements a machine learning pipeline to predict molecular descriptors (Dipole moment, HOMO, LUMO) from quantum chemical calculations using the QM9 dataset. It leverages 2D fingerprints (Morgan) and 3D graph features to train Random Forest models, performs comparative analysis, and identifies failure boundaries where 2D models underperform compared to 3D models.

## Architecture
The pipeline is divided into four main phases:
1. **Data Acquisition**: Downloads and validates the QM9 dataset from HuggingFace (`lisn/QM9`).
2. **Feature Extraction**: Generates 2D and 3D features with memory-safe downsampling.
3. **Model Training**: Trains Random Forest models with 5-fold Cross-Validation and hyperparameter tuning.
4. **Analysis**: Computes statistical significance, failure boundaries, and generates parity plots.

## Directory Structure
```
.
├── code/ # Pipeline scripts
│ ├── 01_data_download.py # Download, parse, and validate QM9 data
│ ├── 02_feature_extraction.py # Generate 2D/3D features
│ ├── 03_model_training.py # Train models and run CV
│ ├── 04_analysis.py # Statistical analysis and reporting
│ ├── config.py # Global configuration and seeds
│ └── utils/ # Helper utilities (parsers, memory monitor, etc.)
├── data/
│ ├── raw/ # Raw downloaded data (qm9_full.parquet)
│ ├── processed/ # Cleaned data and features
│ └── results/ # Final analysis outputs
├── artifacts/
│ ├── models/ # Trained model pickles
│ ├── metrics/ # CV metrics, statistics, failure boundaries
│ ├── plots/ # Parity plots
│ └── report.md # Final summary report
├── docs/ # Documentation
├── tests/ # Unit and integration tests
└── requirements.txt # Python dependencies
```

## Installation
1. Clone the repository.
2. Create a virtual environment (Python 3.11 recommended).
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
Run the pipeline sequentially using the provided scripts:

1. **Download Data**:
 ```bash
 python code/01_data_download.py
 ```
2. **Extract Features**:
 ```bash
 python code/02_feature_extraction.py
 ```
3. **Train Models**:
 ```bash
 python code/03_model_training.py
 ```
4. **Run Analysis**:
 ```bash
 python code/04_analysis.py
 ```

For a full end-to-end validation, use the quickstart validator:
```bash
python code/05_quickstart_validator.py
```

## Key Features
- **Memory Safety**: Automatic downsampling if RAM usage exceeds 6.5 GB (see `code/utils/memory_monitor.py`).
- **Robust Validation**: Integrity checks on DFT labels and 3D coordinates.
- **Statistical Rigor**: Wilcoxon signed-rank tests with Bonferroni correction for model comparison.
- **Failure Boundaries**: Identification of molecules where 2D models fail relative to 3D models (REI ≥ 10%).

## License
MIT License
