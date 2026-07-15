# Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Project Overview
This project implements a pipeline to analyze resting-state EEG data to predict
cognitive fatigue. It focuses on measuring signal complexity using Lempel-Ziv
complexity and permutation entropy to distinguish between adaptive simplification
and degenerative noise patterns.

## Pipeline Stages
1. **Data Retrieval**: Fetches Sleep-EDF or SHHS datasets from PhysioNet/HuggingFace
2. **Preprocessing**: Applies bandpass filtering (1-40Hz) and artifact rejection
3. **Feature Extraction**: Calculates LZC and Permutation Entropy per channel
4. **Analysis**: Correlates complexity metrics with fatigue scores
5. **Reporting**: Generates statistical reports with effect sizes

## Directory Structure
```
.
├── code/ # Pipeline implementation
│ ├── config.yaml # Pipeline parameters
│ ├── download.py # Data retrieval
│ ├── preprocess.py # Filtering and artifact rejection
│ ├── features.py # Complexity metric calculation
│ ├── analysis.py # Statistical analysis
│ ├── report.py # Report generation
│ └── models/ # Data models
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Cleaned data and features
│ └── analysis/ # Statistical results
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── figures/ # Generated plots
```

## Usage
Run the full pipeline:
```bash
python code/download.py
python code/preprocess.py
python code/features.py
python code/analysis.py
python code/report.py
```

## Dependencies
See `code/requirements.txt` for the full list of dependencies.

## Data Sources
- **Primary**: Sleep-EDF dataset (PhysioNet/HuggingFace)
- **Fallback**: SHHS dataset (if Sleep-EDF lacks required variables)

## License
Research use only.