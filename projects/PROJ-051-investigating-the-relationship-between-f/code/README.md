# PROJ-051: Investigating the Relationship between Fractal Dimension and Energy Dissipation in Turbulent Flows

## Overview
This project implements a pipeline to compute fractal dimensions of vorticity iso-surfaces and analyze their correlation with local energy dissipation rates in turbulent flows.

## Prerequisites
- Python 3.10 or higher
- pip

## Installation
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Project Structure
- `code/`: Source code
 - `analysis/`: Core algorithms (fractal dimension, dissipation, stats)
 - `data/`: Data loading and preprocessing
 - `utils/`: Logging and utility functions
 - `validation/`: Synthetic data and null models
- `data/`: Input and output data files
- `tests/`: Unit and integration tests
- `contracts/`: Schema definitions for output validation
- `config.py`: Project configuration

## Usage
Run the main pipeline:
```bash
python code/main.py --config config.py
```

Run tests:
```bash
pytest tests/
```

## Data Sources
This project primarily uses data from the Johns Hopkins Turbulence Database (JHTDB).
Fallback to Phase-Shifted DNS data is available for validation only.

## License
[Add License Information]
