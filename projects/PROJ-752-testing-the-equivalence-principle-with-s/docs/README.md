# PROJ-752: Testing the Equivalence Principle with Satellite Laser Ranging

A scientific pipeline to test the Weak Equivalence Principle (WEP) using Satellite Laser Ranging (SLR) data from LAGEOS, Etalon, and Starlette satellites.

## Overview

This project implements a rigorous orbit determination and differential acceleration analysis to estimate the Eötvös parameter ($\eta$). It follows a modular architecture with distinct phases for data ingestion, orbit pre-processing, parameter estimation, and statistical validation.

## Key Features

- **Data Ingestion**: Automated fetching and parsing of SLR normal-point series from the ILRS archive.
- **Orbit Determination**: Separate and Joint Least-Squares solvers for estimating orbital elements and non-gravitational accelerations.
- **WEP Analysis**: Calculation of the Eötvös parameter with 95% confidence intervals.
- **Robustness**: Sensitivity analysis across different geopotential models (GGM, EGM2008, GOCO).
- **Reproducibility**: Automated validation via `quickstart.md` and artifact hashing.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Eotvos calculations, validation
│ ├── cli/ # Command line interface
│ ├── config.py # Configuration loader
│ ├── data/ # Ingestion, preprocessing, output
│ ├── models/ # Dynamics, estimators, entities
│ ├── scripts/ # Utility scripts (validation, setup)
│ ├── utils/ # Logging, hashing, helpers
│ └── tests/ # Pytest tests
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned and aligned data
│ ├── results/ # Analysis outputs
│ └── logs/ # Execution logs
├── docs/ # Documentation
│ ├── README.md # This file
│ ├── quickstart.md # Reproducibility guide
│ └──...
├── config.yaml # Project configuration
├── requirements.txt # Python dependencies
└──...
```

## Quick Start

See [docs/quickstart.md](docs/quickstart.md) for instructions on validating the pipeline.

## Running the Pipeline

```bash
python code/cli/main.py --help
```

## Documentation

- [Quickstart Guide](docs/quickstart.md)
- [Dynamics Specification](docs/dynamics_spec.md)
- [API Reference](docs/api.md) (Generated from docstrings)

## License

[Insert License]
