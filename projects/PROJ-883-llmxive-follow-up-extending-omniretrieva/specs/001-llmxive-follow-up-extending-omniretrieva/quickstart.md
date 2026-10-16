# Quickstart: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment (GitHub Actions runner or equivalent)
- >= 7 GB RAM, >= 2 CPU cores

## Installation
```bash
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lint
```bash
ruff check code/
```

## End-to-End Run
```bash
python -m code.main
```

The command performs the skeleton initialization:
1. Creates the required directories (`data/raw/`, `data/processed/`, `data/results/`).
2. Verifies that the environment is configured correctly.

Note: Actual query generation, execution, and analysis are implemented in subsequent tasks (T003-T014).

## Quick Help
```bash
python -m code.main --help
```

## Tests
```bash
python -m pytest -v
```