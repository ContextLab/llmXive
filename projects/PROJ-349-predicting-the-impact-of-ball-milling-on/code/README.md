# Predicting the Impact of Ball Milling on Particle Size Distribution

## Overview
This project implements an automated science pipeline to aggregate experimental data on ball milling,
preprocess it, and train predictive models (GPR, Random Forest) to estimate particle size distribution (PSD).

## Project Structure
```
.
├── code/
│ ├── src/ # Source code
│ ├── tests/ # Unit and integration tests
│ ├── data/
│ │ ├── raw/ # Raw downloaded data
│ │ ├── processed/ # Cleaned/feature-engineered data
│ │ └── splits/ # Train/test splits (dynamic)
│ ├── results/ # Model metrics and plots
│ ├── contracts/ # Data schemas
│ └──.github/workflows/ # CI/CD
├── requirements.txt # Dependencies
├── pyproject.toml # Build config & linting settings
└── README.md
```

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Run the setup script to create data directories:
 ```bash
 python code/code/setup_data_dirs.py
 ```

## Execution
See `quickstart.md` for pipeline execution instructions.
