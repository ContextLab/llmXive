# Bird Migration Climate Correlation Analysis

Statistical analysis of publicly available bird migration patterns and climate change.

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e.
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

Run the pipeline:
```bash
python run_pipeline.py --help
```

## Project Structure

- `src/`: Source code
- `data/`: Data files (raw, processed, interim)
- `tests/`: Test suite
- `docs/`: Documentation

## Pre-commit

This project uses pre-commit to enforce code quality. Run `pre-commit install` after cloning to set up hooks.
