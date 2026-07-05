# PROJ-051: Fractal Dimension and Energy Dissipation in Turbulent Flows

## Overview
This project investigates the relationship between the fractal dimension of vorticity iso-surfaces and the energy dissipation rate in turbulent flows using Direct Numerical Simulation (DNS) data.

## Structure
- `code/`: Core Python modules
- `data/`: Input datasets and generated results
- `analysis/`: Analysis algorithms (fractal, gradients, stats)
- `validation/`: Synthetic data generators and validation logic
- `tests/`: Unit and integration tests

## Requirements
Python 3.10+
See `requirements.txt` for dependencies.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py --re-lambda 200 400 600
```

## License
Internal Research Project
