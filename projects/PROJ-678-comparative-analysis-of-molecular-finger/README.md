# Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Project Overview

This project implements a comparative analysis of molecular fingerprints (Morgan and MACCS) for predicting pesticide toxicity, specifically focusing on organophosphate compounds. The pipeline downloads the Tox21 dataset, filters for organophosphates using SMARTS patterns, generates fingerprints, performs 5-fold cross-validation with greedy maximal dissimilarity splitting, and trains Random Forest models.

## Prerequisites

- Python 3.10+
- pip

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```
projects/PROJ-678-comparative-analysis-of-molecular-finger/
├── code/ # Implementation modules
│ ├── utils.py # Logging, seeding, environment setup
│ ├── constants.py # Global constants (SMARTS, thresholds)
│ ├── download.py # Tox21 dataset download
│ ├── filter.py # SMARTS filtering and validation
│ ├── fingerprints.py # Morgan and MACCS fingerprint generation
│ ├── split.py # Greedy maximal dissimilarity split
│ ├── train.py # Model training
│ └── evaluate.py # Model evaluation and reporting
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Filtered data, models, splits, reports
├── tests/ # Test suite
│ ├── unit/
│ └── integration/
├── specs/ # Design documents
└── README.md
```

## Usage

### Quick Start

Run the full pipeline:

```bash
# 1. Download and filter data (User Story 1)
python code/download.py
python code/filter.py

# 2. Generate fingerprints and train models (User Story 2)
python code/fingerprints.py
python code/split.py
python code/train.py

# 3. Evaluate and report (User Story 3)
python code/evaluate.py
```

### Output Artifacts

- `data/processed/organophosphates_filtered.csv`: Filtered dataset
- `data/processed/models/`: Trained Random Forest models
- `data/processed/splits/`: Fold split indices
- `data/processed/research_results.md`: Final analysis report

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Configuration

Key parameters are defined in `code/constants.py`:

- `SMARTS_PATTERN`: Organophosphate detection pattern
- `TANIMOTO_THRESHOLD`: Dissimilarity threshold for splitting
- `MORGAN_RADIUS`, `MORGAN_BITS`: Morgan fingerprint parameters
- `MACCS_BITS`: MACCS fingerprint bit count
- `N_FOLDS`: Number of cross-validation folds

## License

This project is for research purposes.

## Contributors

- llmXive Automated Science Pipeline