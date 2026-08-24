# PROJ-002: Evolutionary Pressure on Alternative Splicing in Primates

## Overview
This project investigates lineage-specific alternative splicing events in primates
and tests for enrichment in regions of accelerated evolution.

## Quick Start

### Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
python setup_python_env.py
```

### R Environment
```bash
# Install R dependencies
bash setup_r_env.sh
```

### Linting & Formatting
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Dependencies
- Python: See `requirements.txt`
- R: See `renv.lock`

## Project Structure
```
code/
├── data_models/ # Data model definitions
├── pipeline/ # Pipeline scripts
├── utils/ # Utility functions
├── tests/ # Test suites
├── requirements.txt # Python dependencies
├── renv.lock # R dependencies
├── setup_python_env.py
├── setup_r_env.sh
└── README.md
data/ # Raw and processed data
results/ # Pipeline outputs
config/ # Configuration files
docs/ # Documentation
```

## Running the Pipeline
See individual pipeline scripts in `code/pipeline/` for usage instructions.

## License
[License information]
