# Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Overview
This project implements a pipeline to analyze resting-state EEG data to predict cognitive fatigue using complexity metrics (Lempel-Ziv Complexity and Permutation Entropy).

## Project Structure
```
projects/PROJ-470-predicting-cognitive-fatigue-from-restin/
├── code/
│ ├── config.yaml
│ ├── download.py
│ ├── preprocess.py
│ ├── features.py
│ ├── analysis.py
│ ├── report.py
│ └── models/
├── data/
│ ├── raw/
│ ├── processed/
│ └── analysis/
├── tests/
│ ├── unit/
│ └── integration/
├── docs/
│ └── README.md
└── logs/
```

## Requirements
- Python 3.11
- MNE-Python
- scikit-learn
- numpy
- pandas
- lempel-ziv-complexity
- scipy
- pyyaml
- pytest

## Usage
1. Download data: `python code/download.py`
2. Preprocess: `python code/preprocess.py`
3. Extract features: `python code/features.py`
4. Analyze: `python code/analysis.py`
5. Generate report: `python code/report.py`

## License
MIT License