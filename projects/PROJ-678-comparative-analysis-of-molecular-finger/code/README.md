# Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Overview
This project implements a comparative analysis of Morgan and MACCS molecular fingerprints
for predicting pesticide toxicity using the Tox21 dataset. The pipeline includes data
acquisition, organophosphate filtering via SMARTS patterns, fingerprint generation,
model training, and statistical evaluation.

## Project Structure
```
.
├── code/
│ ├── requirements.txt # Python dependencies
│ ├── pyproject.toml # Project configuration and linting
│ ├── utils.py # Utility functions (logging, seeding)
│ ├── constants.py # Project constants
│ ├── download.py # Tox21 dataset acquisition
│ ├── filter.py # SMARTS-based filtering
│ ├── fingerprints.py # Fingerprint generation
│ ├── split.py # Data splitting logic
│ ├── train.py # Model training
│ └── evaluate.py # Model evaluation and reporting
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Processed data and model artifacts
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── specs/ # Design documents
```

## Prerequisites
- Python 3.9 or higher
- pip package manager

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage
Run the pipeline steps in order:
1. Download and filter data: `python code/download.py && python code/filter.py`
2. Generate fingerprints: `python code/fingerprints.py`
3. Split data: `python code/split.py`
4. Train models: `python code/train.py`
5. Evaluate and report: `python code/evaluate.py`

## Configuration
Key parameters are defined in `code/constants.py`:
- `SMARTS_PATTERN`: Pattern for organophosphate detection
- `TANIMOTO_THRESHOLD`: Threshold for dissimilarity splitting
- `MORGAN_RADIUS`, `MORGAN_BITS`: Morgan fingerprint parameters
- `MACCS_BITS`: MACCS key count
- `N_FOLDS`: Number of cross-validation folds

## Testing
Run tests using pytest:
```bash
pytest tests/
```

## License
This project is part of the llmXive automated science pipeline.