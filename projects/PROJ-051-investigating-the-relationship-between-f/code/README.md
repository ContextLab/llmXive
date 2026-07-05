# PROJ-051: Fractal Dimension and Energy Dissipation in Turbulent Flows

## Overview

This project investigates the relationship between fractal dimensions of vorticity iso-surfaces and energy dissipation rates in turbulent flows using Direct Numerical Simulation (DNS) data.

## Requirements

- Python 3.10+
- Dependencies listed in `code/requirements.txt`

## Installation

```bash
cd code
pip install -r requirements.txt
```

## Usage

```bash
# Run the full pipeline
python main.py

# Run with specific Reynolds numbers
python main.py --re-lambda 200 400 600

# Verbose mode
python main.py --verbose
```

## Project Structure

```
.
├── code/
│ ├── __init__.py
│ ├── config.py # Configuration management
│ ├── main.py # CLI entry point
│ ├── requirements.txt # Dependencies
│ ├── analysis/ # Analysis algorithms
│ ├── data/ # Data loading and preprocessing
│ ├── validation/ # Validation and synthetic data
│ └── utils/ # Utility functions
├── data/
│ └── results/ # Output results
├── tests/ # Test suite
├── specs/ # Design documents
└── README.md
```

## Key Features

- Box-counting algorithm for fractal dimension computation
- Energy dissipation rate calculation from DNS data
- Statistical correlation analysis with block-bootstrapping
- Reynolds number scaling analysis
- Memory-constrained processing for large grids (512³)

## License

Research project - see LICENSE file for details.
