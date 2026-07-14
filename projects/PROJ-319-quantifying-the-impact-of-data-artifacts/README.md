# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

## Overview
This project implements an automated science pipeline to quantify how instrumental data artifacts (specifically noise and saturation) bias the measurement of planetary nebula morphology (ellipticity and asymmetry). The goal is to derive calibration functions to correct these biases.

## Quickstart

### Prerequisites
- Python 3.11+
- pip

### Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Configuration
The project uses `code/config.py` for seeds and parameters. Default values are provided.

### Running the Pipeline
To generate synthetic data and run the initial analysis:
```bash
python code/main.py
```

### Testing
Run the test suite:
```bash
pytest
```

### Linting & Formatting
The project uses `ruff` for linting and `black` for formatting.
```bash
ruff check.
black.
```
