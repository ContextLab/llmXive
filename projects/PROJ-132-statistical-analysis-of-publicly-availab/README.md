# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes bird migration patterns and their correlation with climate change using publicly available datasets.

## Prerequisites

- Python 3.11+
- pip
- virtualenv (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-132-statistical-analysis-of-publicly-availab
```

2. Create and activate a virtual environment:
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
pip install pre-commit
pre-commit install
```

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality before each commit. The following hooks are configured:

- **Black**: Code formatter to ensure consistent code style.
- **Ruff**: Fast Python linter to catch errors and enforce coding standards.

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
│ │ ├── config.py
│ │ ├── data/
│ │ ├── models/
│ │ └── analysis/
│ ├── tests/
│ │ ├── unit/
│ │ ├── integration/
│ │ └── contract/
│ └── run_pipeline.py
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

## Running the Pipeline

To execute the full analysis pipeline:
```bash
python code/run_pipeline.py
```

## Configuration

Project configuration is managed in `code/src/config.py`. Key parameters include:
- `GRID_RES`: Spatial grid resolution (default: 0.5 degrees)
- `PERMUTATIONS`: Number of permutations for statistical testing (default: 10000)
- Logging settings and output paths

## License

This project is licensed under the MIT License.