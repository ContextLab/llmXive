# Molecular Property Prediction using Topological Data Analysis

This project implements a pipeline for predicting molecular properties (specifically logP) from topological data analysis (TDA) features derived from molecular graphs.

## Setup

1. Ensure Python 3.11+ is installed
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\\Scripts\\activate
 ```
3. Install dependencies:
 ```bash
 pip install -e.
 pip install -e ".[dev]" # For development tools
 ```

## Linting and Formatting

This project uses `ruff` for linting and `black` for formatting.

To check code quality:
```bash
python code/00_lint_format.py
```

To auto-fix formatting issues:
```bash
python code/00_lint_format.py --fix
```

## Running the Pipeline

Follow the instructions in `quickstart.md` to run the full pipeline.

## Project Structure

```
.
├── code/ # Implementation scripts
│ ├── utils/ # Utility modules
│ └── *.py # Pipeline scripts
├── data/ # Data directory
│ ├── raw/ # Raw input data
│ └── processed/ # Processed data
├── reports/ # Generated reports
│ └── metrics/ # Model metrics and diagnostics
├── tests/ # Test suite
├── docs/ # Documentation
├── pyproject.toml # Project configuration
└── README.md
```

## License

MIT License