# PROJ-196: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

## Overview
This project investigates the relationship between temporal discounting (delay discounting)
and procrastination behaviors in the context of cognitive tasks, specifically examining
whether working memory capacity moderates this relationship.

## Project Structure
```
.
├── code/ # Source code for data processing and analysis
│ ├── config.py # Configuration and seed management
│ ├── ingestion.py # Data generation and harmonization
│ ├── modeling.py # Statistical modeling and regression
│ ├── robustness.py # Robustness and sensitivity analysis
│ └── utils/ # Utility functions (checksums, etc.)
├── data/
│ ├── raw/ # Raw data files (generated or downloaded)
│ ├── processed/ # Cleaned and harmonized datasets
│ └── figures/ # Generated plots and visualizations
├── tests/ # Pytest test suite
├── state/
│ └── projects/ # Project state and artifact tracking
├── specs/ # Feature specifications and design docs
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Execution
Run the full pipeline:
```bash
python code/ingestion.py
python code/modeling.py
python code/robustness.py
```

## License
[License Information]
