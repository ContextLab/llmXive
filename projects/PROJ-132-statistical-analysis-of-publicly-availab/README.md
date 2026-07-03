# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes the correlation between bird migration patterns and climate change using publicly available data from eBird and NOAA.

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

## Pre-commit Configuration

This project uses pre-commit to enforce code quality standards before each commit. The following hooks are configured:

- **Black**: Code formatting with line length of 88 characters
- **Ruff**: Linting to catch errors and enforce style conventions

To run pre-commit manually:
```bash
pre-commit run --all-files
```

To update hooks:
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
│ │ │ ├── utils.py
│ │ │ ├── entities.py
│ │ │ ├── gamm_fit.py
│ │ │ └── trajectory.py
│ │ └── lib/
│ │ ├── config.py
│ │ └── logging_config.py
│ └── setup_project.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── interim/
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── docs/
├──.pre-commit-config.yaml
├── pyproject.toml
└── README.md
```

## Usage

### Running the Pipeline

```bash
python code/src/data/preprocess.py
```

### Running Tests

```bash
pytest tests/
```

### Configuration

The project uses a configuration module located at `code/src/lib/config.py` to manage random seeds, grid resolution, and sampling parameters.

## License

This project is licensed under the MIT License.