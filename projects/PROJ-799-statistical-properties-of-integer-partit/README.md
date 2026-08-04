# Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Project Overview
This project investigates the statistical properties of integer partitions into distinct prime summands, denoted as $p_{\mathcal{P}}(n)$. We compute exact values for $n \in [1, 50000]$ [UNRESOLVED-CLAIM: c_6a09483e — status=not_enough_info] and compare them against asymptotic baselines derived from the distinct-partition variant of Meinardus' theorem.

## Directory Structure
- `code/`: Source code for data generation, feature engineering, and modeling.
- `code/utils/`: Utility modules (e.g., prime sieves).
- `data/raw/`: Generated raw data (partitions).
- `data/processed/`: Processed features and model results.
- `data/schemas/`: JSON/YAML schemas for data validation.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation.
- `state/`: Project state tracking (checksums, versions).

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -e.
 ```
 Or manually:
 ```bash
 pip install numpy scipy scikit-learn statsmodels matplotlib pandas pygam flake8 black pytest
 ```

## Linting and Formatting
This project uses `flake8` for linting and `black` for formatting, scoped to the `code/` directory.

### Run Linting
```bash
flake8 code/
```

### Run Formatting
```bash
black code/
```

### Check Formatting (Dry Run)
```bash
black --check code/
```

## Running the Pipeline
Refer to `quickstart.md` for the full execution pipeline.

## Testing
```bash
pytest tests/
```
