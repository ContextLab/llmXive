# Predicting Individual Pain Sensitivity from Resting-State EEG Microstates

**Project ID**: PROJ-712
**Pipeline**: llmXive Automated Science Pipeline
**Python Version**: 3.11+

## Overview

This project implements a reproducible machine learning pipeline to predict individual heat-pain sensitivity thresholds using resting-state EEG microstate features. The pipeline adheres to strict scientific rigor, including nested permutation testing, FDR correction, and sensitivity analyses, all designed to run within a 6-hour execution window on standard compute resources.

## Key Features

- **Data Ingestion**: Automated download and preprocessing of OpenNeuro EEG datasets.
- **Feature Extraction**: Derivation of 30 specific microstate and spectral features per participant.
- **Predictive Modeling**: Elastic Net regression with nested cross-validation.
- **Statistical Rigor**:
 - Nested permutation tests (1,000 iterations) for null distribution generation.
 - Bootstrap confidence intervals (200 iterations) for Pearson correlation.
 - FDR correction on permutation importance scores.
 - Dual sensitivity analysis (median-split and regularization sweep).
- **Reproducibility**: Deterministic seeding, artifact hashing, and full audit trails.

## Installation

### Prerequisites
- Python 3.11 or higher
- `pip`
- System dependencies for MNE-Python (e.g., `libsndfile1` on Linux)

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-712-predicting-individual-pain-sensitivity-f
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

4. (Optional) Install development tools for linting and formatting:
 ```bash
 pip install ruff black
 ```

## Usage

### Running the Full Pipeline

Execute the main pipeline script to run all stages from data ingestion to diagnostics:

```bash
python code/main.py
```

This will:
1. Verify data availability and checksums.
2. Preprocess EEG data and extract 30 features.
3. Train the Elastic Net model with nested CV.
4. Run permutation tests and bootstrap CI.
5. Perform diagnostics (VIF, FDR, sensitivity).
6. Save results to `artifacts/` and `data/processed/`.

**Note**: The pipeline enforces a 6-hour total runtime limit (SC-005). If the estimated time exceeds this, it will dynamically adjust parameters (e.g., reducing permutation iterations) or abort.

### Running Individual Stages

You can run specific stages independently by invoking the corresponding module:

- **Data Preprocessing & Feature Extraction**:
 ```bash
 python code/preprocessing.py
 ```
- **Model Training & Validation**:
 ```bash
 python code/modeling.py
 ```
- **Diagnostics & Sensitivity Analysis**:
 ```bash
 python code/diagnostics.py
 ```

### Running Tests

Run the unit and integration tests:

```bash
pytest tests/ -v
```

Specific test suites:
- Unit tests: `pytest tests/unit/ -v`
- Integration tests: `pytest tests/integration/ -v`

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── config.py # Configuration and path management
│ ├── data_loader.py # Data loading and chunking
│ ├── preprocessing.py # EEG preprocessing and feature extraction
│ ├── modeling.py # Model training, CV, and permutation tests
│ ├── diagnostics.py # Statistical diagnostics and sensitivity
│ ├── main.py # Pipeline orchestration
│ ├── utils.py # Utility functions (seeding, logging, timing)
│ └── checksums.py # Data integrity verification
├── data/
│ ├── raw/ # Raw downloaded EEG data
│ └── processed/ # Processed feature matrices
├── artifacts/ # Model results, reports, and null distributions
├── state/ # Execution state and checksum records
├── tests/ # Unit and integration tests
├── specs/ # Design documents and requirements
├── contracts/ # Data schemas
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Output Artifacts

Upon successful completion, the pipeline generates:

- `data/processed/feature_matrix.csv`: 30 features per participant + pain threshold labels.
- `artifacts/model_result.json`: Pearson r, p-value, MAE, and confidence intervals.
- `artifacts/null_distribution.npy`: Empirical null distribution from permutation tests.
- `artifacts/diagnostics_report.md`: FDR tables, VIF flags, and sensitivity analysis plots.
- `state/projects/PROJ-712-predicting-individual-pain-sensitivity-f.yaml`: Execution state and artifact hashes.

## Configuration

Environment variables can be set in a `.env` file or exported directly:

- `DATA_DIR`: Root directory for data storage (default: `data/`)
- `ARTIFACTS_DIR`: Root directory for artifacts (default: `artifacts/`)
- `SEED`: Random seed for reproducibility (default: `42`)
- `MAX_RUNTIME_HOURS`: Maximum allowed runtime (default: `6`)

## Contributing

1. Ensure all tests pass: `pytest tests/ -v`
2. Format code: `black code/ tests/`
3. Lint code: `ruff check code/ tests/`
4. Submit a pull request with a description of changes.

## License

This project is part of the llmXive automated science initiative. See the LICENSE file for details.

## Citation

If you use this pipeline in your research, please cite the associated design documents and methodology papers referenced in `specs/`.