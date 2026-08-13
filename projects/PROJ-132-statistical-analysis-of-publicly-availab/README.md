# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes bird migration patterns and their correlation with climate change using publicly available datasets.

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -e.
 ```
3. Install pre-commit hooks:
 ```bash
 pip install pre-commit
 pre-commit install
 ```

## Usage

Run the full pipeline:
```bash
python -m src.cli.run_pipeline --help
```

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. The following hooks are configured:
- **black**: Code formatting
- **ruff**: Linting

To run hooks manually:
```bash
pre-commit run --all-files
```

## Project Structure

- `src/`: Source code
- `data/`: Data files (raw, processed, interim)
- `tests/`: Test suite
- `docs/`: Documentation
- `data/provenance/`: Provenance tracking files

## Configuration

See `src/config.py` for configuration constants.

## License

MIT License