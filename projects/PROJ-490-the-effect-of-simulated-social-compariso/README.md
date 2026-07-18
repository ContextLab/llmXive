# PROJ-490: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

## Overview
This project investigates the impact of simulated social comparison on self-esteem within virtual reality environments. It implements a reproducible scientific pipeline for data discovery, preprocessing, statistical analysis (ANCOVA), and robustness checks.

## Project Structure
```
projects/PROJ-490-the-effect-of-simulated-social-compariso/
├── code/ # Source code modules
│ ├── analysis/ # Statistical models and validation
│ ├── data/ # Data loading, preprocessing, generation
│ └── utils/ # Logging, validation utilities
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/ # Cleaned and analyzed data
├── tests/
│ ├── contract/ # Schema validation tests
│ └── unit/ # Unit tests
├── docs/ # Documentation
├── state/ # Pipeline state and hashes
├── contracts/ # Data schema definitions
├── requirements.txt # Python dependencies
└── README.md
```

## Setup
1. Create a virtual environment:
 `python -m venv venv`
2. Activate the environment:
 `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies:
 `pip install -r requirements.txt`

## Linting and Formatting
This project enforces code quality using `flake8` and `black`.

**Run Linting:**
```bash
flake8 code/ tests/
```

**Run Formatting:**
```bash
black code/ tests/
```

**Run Pylint:**
```bash
pylint code/
```

## Usage
Refer to the `docs/` directory for specific analysis plans and execution guides.

## License
MIT License
