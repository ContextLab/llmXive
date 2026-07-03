# PROJ-490: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

## Overview
This project investigates how simulated social comparison in virtual reality (VR)
environments affects self-esteem, specifically examining the interaction between
avatar condition and individual comparison tendencies.

## Project Structure
```
projects/PROJ-490-the-effect-of-simulated-social-compariso/
├── code/ # Source code for data processing and analysis
│ ├── data/ # Data loading, cleaning, and generation
│ ├── analysis/ # Statistical models and robustness checks
│ └── utils/ # Logging, validation, and configuration
├── data/
│ ├── raw/ # Raw datasets (downloaded or synthetic)
│ └── processed/ # Cleaned data and analysis outputs
├── contracts/ # JSON/YAML schemas for data and outputs
├── tests/ # Unit and contract tests
├── docs/ # Documentation
├── state/ # Project state tracking
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Run the analysis pipeline:
 ```bash
 python code/main.py
 ```

## Data Contracts
- `contracts/dataset.schema.yaml`: Schema for input data
- `contracts/output.schema.yaml`: Schema for regression results
- `contracts/results.schema.yaml`: Schema for final report

## License
Research project for educational purposes.
