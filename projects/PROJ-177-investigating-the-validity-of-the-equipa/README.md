# PROJ-177: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Overview
This project implements an automated pipeline to investigate the validity of the equipartition theorem in driven granular systems. It ingests particle tracking data, calculates energy components, performs statistical hypothesis testing against Maxwell-Boltzmann distributions, and conducts sensitivity and regression analyses.

## Project Structure
```
.
├── code/ # Python source modules
├── data/ # Input and derived data
│ ├── raw/ # Raw experimental data (gitignored, fetch required)
│ ├── derived/ # Processed data (e.g., energy_samples.csv)
│ └── config.yaml # Material properties and frequency bins
├── artifacts/ # Final analysis outputs (JSON, figures)
├── state/ # Pipeline state and hashes
├── figures/ # Generated plots
├── tests/ # Pytest test suite
├── requirements.txt # Python dependencies
├── pyproject.toml # Project config, linting, formatting
└── README.md
```

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Configure linting and formatting (optional but recommended):
 ```bash
 pip install ruff black
 ```

## Usage
Run the main pipeline script:
```bash
python code/main.py --help
```

Run tests:
```bash
pytest tests/
```

## Data Requirements
This project requires real experimental data from driven granular systems.
Refer to `specs/001-validity-equipartition-granular/` for data format specifications.
Place raw data in `data/raw/`.

## License
MIT
