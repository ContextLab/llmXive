# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes the correlation between bird migration patterns and climate change using publicly available eBird and NOAA data.

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
 pre-commit install
 ```

## Pre-commit Configuration

This project uses `pre-commit` to automatically format and lint code before commits.

The following hooks are configured:
- **black**: Code formatting (line-length=88, target-version=['py311'])
- **ruff**: Linting (select=['E','F','W','I'])

To run pre-commit manually:
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
│ │ ├── models/
│ │ └── lib/
│ ├── tests/
│ └──...
├── data/
│ ├── raw/
│ ├── processed/
│ └── interim/
├── logs/
├── docs/
├──.pre-commit-config.yaml
├── README.md
├── requirements.txt
└── pyproject.toml
```

## Usage

### Running the Pipeline

```bash
python code/run_pipeline.py
```

For development with synthetic data:
```bash
python code/run_pipeline.py --mode=synthetic
```

### Running Tests

```bash
python -m pytest tests/
```

## Configuration

Random seeds and sampling parameters are managed via `code/src/lib/config.py`.

## License

[Insert License Information]