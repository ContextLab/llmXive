# Molecular Flexibility and Permeability Research Project

## Overview
This project explores the correlation between molecular flexibility and drug transport across cell membranes (Caco-2 permeability).

## Setup
1. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

2. Configure linting and formatting:
 ```bash
 # Linting
 flake8 code/ tests/

 # Formatting
 black code/ tests/
 ```

## Project Structure
- `code/`: Source code for data retrieval, processing, analysis, and visualization
- `tests/`: Unit and integration tests
- `data/`: Raw and processed data files
- `specs/`: Project specifications and documentation
- `state/`: Project state and governance records

## Linting and Formatting
This project uses `flake8` for linting and `black` for code formatting.
Configuration files are located at the project root:
- `.flake8`: Flake8 configuration
- `pyproject.toml`: Black and isort configuration

Run linting:
```bash
flake8 code/ tests/
```

Run formatting:
```bash
black code/ tests/
```

To check formatting without modifying files:
```bash
black --check code/ tests/
```
