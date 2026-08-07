# PROJ-051: Fractal Dimension and Energy Dissipation in Turbulent Flows

## Overview
This project investigates the relationship between fractal dimension (D_f) of vorticity iso-surfaces and the energy dissipation rate (ε) in turbulent flows using Direct Numerical Simulation (DNS) data.

## Prerequisites
- Python 3.10+
- pip

## Installation
1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
Run the pipeline:
```bash
python main.py
```

## Project Structure
- `code/`: Source code for the pipeline
- `data/`: Input data and generated datasets
- `analysis/`: Analysis modules (fractal dimension, dissipation)
- `validation/`: Validation and synthetic data generation
- `tests/`: Unit and integration tests
- `config.py`: Configuration management
- `main.py`: CLI entry point

## Data Sources
Primary data is fetched from the Johns Hopkins Turbulence Database (JHTDB).
Fallback to Phase-Shifted DNS is available only for algorithm validation.

## License
Internal research use only.
