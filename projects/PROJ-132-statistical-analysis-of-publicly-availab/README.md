# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes bird migration patterns and their correlation with climate change using publicly available data from eBird and NOAA.

## Prerequisites

- Python 3.11+
- pip
- git

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-132-statistical-analysis-of-publicly-availab
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Pre-commit Configuration

This project uses `pre-commit` to enforce code quality standards before commits. The following hooks are configured:

- **black**: Code formatting (line-length=88, target-version=['py311'])
- **ruff**: Linting (select=['E','F','W','I'], ignore=[])

To run pre-commit manually on all files:
```bash
pre-commit run --all-files
```

To update pre-commit hooks to the latest versions:
```bash
pre-commit autoupdate
```

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/
│ │ │ ├── download.py
│ │ │ ├── preprocess.py
│ │ │ └── impute.py
│ │ ├── models/
│ │ │ ├── gamm_fit.py
│ │ │ ├── trajectory.py
│ │ │ └── utils.py
│ │ └── lib/
│ │ └── config.py
│ ├── tests/
│ │ ├── contract/
│ │ ├── unit/
│ │ └── integration/
│ ├── run_pipeline.py
│ └── benchmark_runtime.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── interim/
├── docs/
├──.pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Usage

### Running the Pipeline

To run the complete data analysis pipeline:

```bash
python code/run_pipeline.py
```

For development with synthetic data:
```bash
python code/run_pipeline.py --mode=synthetic
```

For production with real data:
```bash
python code/run_pipeline.py --mode=real
```

### Running Tests

Run all tests:
```bash
pytest code/tests/
```

Run specific test suites:
```bash
pytest code/tests/unit/
pytest code/tests/integration/
pytest code/tests/contract/
```

### Benchmarking

To benchmark runtime performance:
```bash
python code/benchmark_runtime.py
```

## Configuration

Key constants are defined in `code/src/lib/config.py`:
- `SEED=42`: Random seed for reproducibility
- `GRID_RES=0.5`: Spatial grid resolution in degrees
- `PERMUTATIONS=10000`: Number of permutations for statistical tests

## Data Sources

- **eBird**: Bird observation data (real or synthetic)
- **NOAA**: Climate data (real or synthetic)

See `code/src/data/download.py` for data acquisition details.

## Contributing

1. Ensure pre-commit hooks pass before committing
2. Write tests for new functionality
3. Follow the existing code style (black + ruff)
4. Update documentation as needed

## License

[License information]