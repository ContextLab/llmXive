# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes publicly available bird migration data to study the correlation
between migration patterns and climate change.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality before each commit.
The following hooks are configured:

- **Black**: Code formatter to maintain consistent style
- **Ruff**: Fast Python linter and formatter

To manually run all hooks on all files:
```bash
pre-commit run --all-files
```

To run hooks on staged files only:
```bash
pre-commit run
```

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/
│ │ ├── models/
│ │ ├── analysis/
│ │ └── config.py
│ ├── tests/
│ ├── run_pipeline.py
│ └── setup_project.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── interim/
├── docs/
├──.pre-commit-config.yaml
├── pyproject.toml
└── README.md
```

## Usage

Run the full analysis pipeline:
```bash
python code/run_pipeline.py
```

## Configuration

Project configuration is managed in `code/src/config.py`. Key parameters include:
- `GRID_RES`: Spatial grid resolution (default: 0.5 degrees)
- `PERMUTATIONS`: Number of permutation test iterations (default: 10000)
- `SEED`: Random seed for reproducibility (default: 42)

## License

This project is licensed under the terms specified in the LICENSE file.