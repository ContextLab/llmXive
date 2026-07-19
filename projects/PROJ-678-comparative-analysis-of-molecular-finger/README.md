# Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Project Overview

This project implements a comparative analysis of molecular fingerprints (Morgan vs. MACCS)
for predicting pesticide toxicity, specifically focusing on organophosphates from the Tox21 dataset.

## Features

- **Data Acquisition**: Automated download and validation of the Tox21 dataset from HuggingFace.
- **Filtering**: SMARTS-based filtering for organophosphates.
- **Fingerprint Generation**: Generation of Morgan (radius=2, 2048 bits) and MACCS (166 bits) fingerprints.
- **Model Training**: 5-Fold Greedy Maximal Dissimilarity Split and Random Forest training.
- **Evaluation**: Comparative metrics (ROC-AUC, PR-AUC), statistical significance testing (paired t-test),
 and feature importance analysis mapped to phosphorus centers.

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-678-comparative-analysis-of-molecular-finger
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

The pipeline is executed via the `quickstart.md` script or by running individual modules:

```bash
# Download and filter data
python code/download.py
python code/filter.py

# Generate fingerprints and split data
python code/fingerprints.py
python code/split.py

# Train models
python code/train.py

# Evaluate and generate report
python code/evaluate.py
```

## Project Structure

```
.
├── code/
│ ├── utils.py # Logging, seed initialization, environment loading
│ ├── constants.py # Global constants (SMARTS, thresholds, etc.)
│ ├── download.py # Tox21 dataset download
│ ├── filter.py # SMARTS filtering and validation
│ ├── fingerprints.py # Morgan and MACCS fingerprint generation
│ ├── split.py # Greedy Maximal Dissimilarity Split
│ ├── train.py # Random Forest model training
│ ├── evaluate.py # Model evaluation and statistical analysis
│ └── save_artifacts.py # Artifact saving utilities
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Filtered data, models, splits, results
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── specs/ # Design documents
├── requirements.txt
├── pyproject.toml
└── README.md
```

## License

This project is for research purposes only.

## Contributors

- llmXive Automated Science Pipeline