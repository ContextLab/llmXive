# PROJ-008: Mindfulness Components and Delivery Formats in ASD Social Skills

## Project Overview
This project implements a systematic review and meta-analysis of mindfulness-based interventions
for improving social skills in children with Autism Spectrum Disorder (ASD).

## Directory Structure
```
projects/PROJ-008-psychology-research/
├── code/ # Source code
│ ├── analysis/ # Statistical analysis modules
│ ├── data/ # Data collection and cleaning
│ ├── utils/ # Utilities (logging, config)
│ └── viz/ # Visualization modules
├── tests/ # Test suites
│ ├── contract/ # Schema contract tests
│ ├── integration/ # Integration tests
│ └── unit/ # Unit tests
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned/processed data
│ └── external/ # External reference data
├── figures/ # Generated plots and charts
├── contracts/ # Schema validation contracts
├── docs/ # Documentation
├── scripts/ # Utility scripts
└── specs/ # Feature specifications
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run data collection: `python scripts/run_pipeline.py`
3. Run analysis: `python scripts/run_analysis.py`
4. Generate reports: `python scripts/generate_report.py`

## Key Constraints
- **CPU Only**: No GPU dependencies
- **Data Integrity**: Real data from ClinicalTrials.gov and OSF only
- **Reproducibility**: All random seeds pinned in `code/utils/config.py`
