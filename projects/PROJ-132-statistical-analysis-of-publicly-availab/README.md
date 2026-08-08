# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes publicly available bird migration data (eBird) and climate data (Daymet) to study the correlation between migration patterns and climate change.

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

2. Create a virtual environment:
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

This project uses pre-commit hooks to ensure code quality before commits. The hooks include:

- **Black**: Code formatter
- **Ruff**: Fast Python linter and formatter

### Running Pre-commit Manually

To run all hooks on all files:
```bash
pre-commit run --all-files
```

To run a specific hook:
```bash
pre-commit run black
pre-commit run ruff
```

### Updating Pre-commit Hooks

To update hook versions, edit the `rev` field in `.pre-commit-config.yaml` and run:
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
│ │ ├── analysis/
│ │ └── plan/
│ ├── tests/
│ │ ├── contract/
│ │ ├── unit/
│ │ └── integration/
│ ├── run_pipeline.py
│ └── setup_project.py
├── data/
│ ├── raw/
│ ├── interim/
│ ├── processed/
│ └── provenance/
├── docs/
├──.pre-commit-config.yaml
├── requirements.txt
└── README.md
```

## Running the Pipeline

### Running the Pipeline

```bash
python code/run_pipeline.py
```

### Running Tests

```bash
pytest
```

### Code Formatting and Linting

```bash
# Format code with Black
black code/

# Lint code with Ruff
ruff check code/
```

## Configuration

Project configuration is managed in `code/src/config.py`. Key settings include:

- `SEED`: Random seed for reproducibility
- `GRID_RES`: Spatial grid resolution
- `PERMUTATIONS`: Number of permutations for statistical tests
- Logging configuration

## Data Sources

- **eBird Data**: `vvud/eb-data` from HuggingFace
- **Climate Data**: `daymet/annual` from HuggingFace

## License

[Add license information here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run pre-commit hooks to ensure code quality
5. Submit a pull request