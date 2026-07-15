# Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Project Overview
This project implements a comparative analysis of molecular fingerprints (Morgan vs. MACCS) for predicting organophosphate pesticide toxicity using the Tox21 dataset.

## Prerequisites
- Python 3.9+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure
```
.
├── code/ # Source code modules
│ ├── utils.py # Logging, seed initialization
│ ├── constants.py # Project constants (SMARTS, thresholds)
│ ├── download.py # Tox21 dataset download
│ ├── filter.py # SMARTS-based filtering
│ ├── fingerprints.py # Fingerprint generation
│ ├── split.py # Greedy Maximal Dissimilarity Split
│ ├── train.py # Model training
│ └── evaluate.py # Evaluation and statistical testing
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Processed data, models, and reports
├── specs/ # Design documents and research specs
├── tests/ # Unit and integration tests
└── requirements.txt # Python dependencies
```

## Usage
Run the pipeline steps in order:
1. Download and filter data: `python code/download.py` and `python code/filter.py`
2. Generate fingerprints and split: `python code/fingerprints.py` and `python code/split.py`
3. Train models: `python code/train.py`
4. Evaluate and report: `python code/evaluate.py`

## Configuration
Key parameters are defined in `code/constants.py`:
- `SMARTS_PATTERN`: Organophosphate filter pattern
- `TANIMOTO_THRESHOLD`: Dissimilarity threshold for splitting
- `MORGAN_RADIUS`, `MORGAN_BITS`: Morgan fingerprint parameters
- `MACCS_BITS`: MACCS key count
- `N_FOLDS`: Number of cross-validation folds

## License
MIT License