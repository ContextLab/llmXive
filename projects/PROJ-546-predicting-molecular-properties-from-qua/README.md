# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview
This project implements a pipeline to predict molecular properties (specifically reaction barriers)
using descriptors generated from semi-empirical (DFTB+) and high-level DFT (Psi4) calculations.
The goal is to evaluate the trade-off between computational cost and prediction accuracy.

## Project Structure
```
.
├── code/ # Source code for the pipeline
│ ├── utils/ # Utility functions (error handling, memory monitoring)
│ ├── validators/ # Data validation logic
│ ├── download_data.py # Data fetching script
│ ├── generate_descriptors.py
│ ├── train_models.py
│ └──...
├── data/ # Data artifacts (raw, processed, reports)
├── figures/ # Generated plots and visualizations
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications and design docs
└── README.md
```

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Ensure DFTB+ and Psi4 are installed and available in your PATH (for descriptor generation tasks).

## Usage
Follow the tasks in `tasks.md` to execute the pipeline step-by-step.
Key entry points:
- `python code/download_data.py`
- `python code/generate_descriptors.py`
- `python code/train_models.py`

## License
MIT
