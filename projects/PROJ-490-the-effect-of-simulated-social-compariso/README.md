# The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Project ID**: PROJ-490

## Overview
This project implements an automated research pipeline to analyze the effect of simulated social comparison on self-esteem within virtual reality environments. It leverages real-world datasets (where available and compliant) or a rigorously defined synthetic data generator to perform statistical analysis, robustness checks, and sensitivity analysis.

## Project Structure
```
.
├── code/ # Source code for analysis pipelines
│ ├── data/ # Data loading, preprocessing, and generation
│ ├── analysis/ # Statistical modeling and robustness checks
│ └── utils/ # Shared utilities (logging, validation, config)
├── data/
│ ├── raw/ # Unmodified downloaded data
│ └── processed/ # Cleaned and feature-engineered data
├── tests/
│ ├── unit/ # Unit tests for functions
│ └── contract/ # Schema validation tests
├── docs/ # Documentation
├── state/ # Project state tracking and hashes
└── requirements.txt # Python dependencies
```

## Setup
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
The pipeline is designed to be run via the main entry point (to be implemented in future tasks):
```bash
python code/main.py
```

## Data Sources
This project attempts to load data from:
- HuggingFace Datasets
- OpenML
- Open Science Framework (OSF)

If no compliant real-world dataset is found (IRB/Consent verified), the system will fall back to a synthetic data generator with defined ground-truth parameters for pipeline validation only.

## Quality Assurance
- **Linting**: `flake8` is used for style enforcement.
- **Formatting**: `black` is used for consistent code formatting.
- **Testing**: `pytest` is used for unit and contract testing.

Run checks:
```bash
# Lint
flake8 code/ tests/

# Format
black code/ tests/

# Test
pytest tests/
```
