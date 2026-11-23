# Quickstart: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local machine with sufficient RAM).

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

The pipeline automatically downloads the QM9 dataset from HuggingFace.

1. **Run the download script**:
   ```bash
   python code/download_data.py
   ```
   This will fetch the dataset and save it to `data/raw/`.

2. **Extract features**:
   ```bash
   python code/extract_features.py
   ```
   This script:
   - Streams the dataset.
   - Performs memory monitoring and dynamic downsampling if needed.
   - Generates 2D and 3D feature matrices.
   - Saves processed data to `data/processed/`.

## Model Training

1. **Train the models**:
   ```bash
   python code/train_models.py
   ```
   This runs 5-fold cross-validation for both 2D and 3D models and saves the trained models and metrics.

## Analysis & Reporting

1. **Generate the final report and plots**:
   ```bash
   python code/analyze_results.py
   ```
   This computes the Relative Error Increase (REI), performs statistical tests, and generates parity plots.

## Verification

To verify the pipeline:

1. **Check outputs**: Ensure `artifacts/metrics/analysis_report.json` exists and contains valid REI values.
2. **Run tests**:
   ```bash
   pytest tests/
   ```
3. **Static Analysis**:
   ```bash
   mypy code/
   ruff check code/
   ```

## Troubleshooting

- **Memory Error**: If the script fails due to memory, check the logs for the "Downsampling to N=..." message. The script automatically reduces the sample size.
- **Dataset Missing**: Ensure internet access is available to download from HuggingFace.
- **Import Errors**: Verify that `rdkit` and `scikit-learn` are installed correctly (`pip install rdkit scikit-learn`).
