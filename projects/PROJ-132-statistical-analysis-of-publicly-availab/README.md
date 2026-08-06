# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes publicly available bird migration data (eBird) and climate data to investigate correlations between climate change and phenological shifts in bird migration patterns.

## Prerequisites

- Python 3.11+
- pip
- git

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
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

This will configure pre-commit to automatically run `black` and `ruff` on your code before each commit.

## Pre-commit Configuration

This project uses pre-commit with the following hooks:
- **black**: Code formatter (line-length=88, target-version=['py311'])
- **ruff**: Linter (select=['E','F','W','I'], ignore=[])

To manually run pre-commit on all files:
```bash
pre-commit run --all-files
```

To update pre-commit hooks:
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
│ │ │ ├── download.py
│ │ │ ├── impute.py
│ │ │ └── preprocess.py
│ │ └── models/
│ │ ├── gamm_fit.py
│ │ ├── trajectory.py
│ │ └── utils.py
│ ├── tests/
│ │ ├── contract/
│ │ ├── integration/
│ │ └── unit/
│ ├── benchmark_runtime.py
│ ├── run_pipeline.py
│ └── setup_project.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── interim/
├── docs/
├── specs/
├──.pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Usage

### Running the Pipeline

```bash
python code/run_pipeline.py
```

### Running Tests

```bash
pytest code/tests/
```

### Data Requirements

This project requires real eBird and NOAA climate data. Set the `DATA_PATH` environment variable to point to your data directory, or ensure real data files are present in `data/raw/`.

See `code/src/data/download.py` for data acquisition details.

## Configuration

Project configuration is managed in `code/src/config.py`. Key parameters include:
- `GRID_RES`: Spatial grid resolution (default: 0.5 degrees)
- `PERMUTATIONS`: Number of permutation test shuffles (default: 10000)
- `SEED`: Random seed for reproducibility (default: 42)
- Statistical power and CI width targets

## License

[Add license information here]

## Contributing

1. Create a feature branch
2. Make your changes
3. Run `pre-commit run --all-files` to ensure code quality
4. Run tests: `pytest code/tests/`
5. Submit a pull request