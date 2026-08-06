# Assessing Uncertainty Quantification Techniques for Machine-Learning Predicted Material Properties

## Project Overview
This project assesses various Uncertainty Quantification (UQ) techniques (Deep Ensembles, MC Dropout, Sparse GP) applied to machine learning models predicting material properties (specifically OQMD formation energy). The goal is to evaluate calibration, reliability, and practical utility in downstream screening tasks.

## Implementation Plan
The project follows a phased approach:
1. **Setup**: Project structure, dependencies, linting.
2. **Foundational**: Data download, preprocessing (PCA, stratified split), config management.
3. **User Story 1**: Baseline model training and UQ application.
4. **User Story 2**: Calibration and reliability evaluation.
5. **User Story 3**: Downstream screening case study.

## Directory Structure
```
.
├── code/ # Source code
│ ├── data/ # Data loading and preprocessing
│ ├── models/ # Model definitions and training
│ ├── uq/ # Uncertainty quantification logic
│ ├── utils/ # Utility functions
│ ├── config.yaml # Configuration file
│ └── main.py # Pipeline orchestrator
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Preprocessed data splits
├── results/ # Model outputs and evaluation results
├── tests/ # Unit and contract tests
├── specs/ # Feature specifications and design docs
└── requirements.txt # Python dependencies
```

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Configure settings in `code/config.yaml`.
3. Run the pipeline: `python code/main.py`
4. View results in `results/`.

## Prerequisites
- Python 3.9+
- Access to HuggingFace datasets (for OQMD)
- Sufficient disk space (~10GB for raw data)

## License
MIT
