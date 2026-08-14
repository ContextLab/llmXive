# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes bird migration patterns and their correlation with climate change using publicly available data sources.

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
 pip install -e.
 ```

4. Install pre-commit hooks:
 ```bash
 pip install pre-commit
 pre-commit install
 ```

## Project Structure

```
.
├── code/ # Source code and scripts
│ ├── src/ # Main source package
│ │ ├── data/ # Data processing modules
│ │ ├── models/ # Statistical models
│ │ ├── utils/ # Utility functions
│ │ ├── config.py # Configuration constants
│ │ └──...
│ ├── tests/ # Test suite
│ │ ├── unit/ # Unit tests
│ │ ├── integration/ # Integration tests
│ │ └── contract/ # Contract tests
│ └──...
├── data/ # Data directories
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data
│ └── interim/ # Intermediate data
├── docs/ # Documentation
├── reports/ # Generated reports
├──.pre-commit-config.yaml # Pre-commit configuration
├── pyproject.toml # Project configuration
└── README.md # This file
```

## Running the Pipeline

To run the full analysis pipeline:

```bash
python -m src.cli.run_pipeline
```

For help with command-line options:

```bash
python -m src.cli.run_pipeline --help
```

## Development

### Code Quality

This project uses Black for code formatting and Ruff for linting. Pre-commit hooks are configured to run these tools automatically before each commit.

To run checks manually:

```bash
# Format code
black code/

# Lint code
ruff check code/
```

### Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src
```

## Data Sources

This project uses the following verified data sources:

- **eBird Data**: Verified sample from `vvud/eb-data` (Hugging Face Datasets)
- **Climate Data**: Daymet annual climate data (Hugging Face Datasets)

See `specs/001-bird-migration-climate-correlation/amendments/FR-001-data-substitution.md` for details on data source substitutions.

## License

This project is licensed under the MIT License.