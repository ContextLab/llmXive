# Project Structure

PROJ-552: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Directory Layout

```
PROJ-552-quantifying-the-complexity-of-knot-diagr/
├── code/ # Source code packages
│ ├── __init__.py # Package init with seed pinning
│ ├── download/ # External data download modules
│ │ └── __init__.py
│ ├── data/ # Data parsing and validation
│ │ └── __init__.py
│ ├── analysis/ # Statistical analysis and regression
│ │ └── __init__.py
│ └── reproducibility/ # Logging and checksum utilities
│ └── __init__.py
├── data/ # Data storage
│ ├── raw/ # Unprocessed downloaded data
│ ├── processed/ # Cleaned datasets
│ └── plots/ # Generated visualizations
├── docs/ # Documentation
│ ├── reproducibility/ # Reproducibility artifacts
│ └── PROJECT_STRUCTURE.md # This file
├── specs/ # Feature specifications
│ └── 001-knot-complexity-analysis/
├── tests/ # Test suites
│ ├── __init__.py
│ ├── contract/ # Schema validation tests
│ ├── integration/ # Pipeline integration tests
│ └── unit/ # Module unit tests
├── pyproject.toml # Python project configuration
├── tasks.md # Task tracking and execution order
└── README.md # Project overview
```

## Purpose of Each Module

- **code/download/**: Fetches knot data from Knot Atlas with retry logic
- **code/data/**: Parses, validates, and cleans knot data
- **code/analysis/**: Implements regression models and statistical tests
- **code/reproducibility/**: Logs operations, generates checksums, documents seeds
- **data/raw/**: Stores unprocessed downloads from external sources
- **data/processed/**: Contains cleaned datasets ready for analysis
- **data/plots/**: Generated figures and visualizations
- **docs/reproducibility/**: Validation reports, logs, and methodological notes
- **specs/**: Contract definitions and feature specifications
- **tests/**: Comprehensive test suite (contract, integration, unit)

## Standards

- **Random Seed**: Pinned at 42 (see `code/__init__.py`)
- **Data Formats**: JSON for raw data, CSV for processed data
- **Plot Resolution**: 1200x900 pixels minimum
- **Logging**: Timestamped with operation, input, output, parameters, status, duration
