# llmXive: Predicting Gene Essentiality from Protein Interaction Network Topology

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```
3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

### Linting and Formatting
This project uses:
- **Black** for code formatting
- **Ruff** for linting

To run manually:
```bash
# Format code
black.

# Lint code
ruff check.

# Fix linting issues automatically
ruff check --fix.
```

To run pre-commit hooks on all files:
```bash
pre-commit run --all-files
```

## Project Structure
- `code/` - Source code
- `data/` - Data files
- `results/` - Analysis results
- `tests/` - Test suite
- `specs/` - Feature specifications

## Configuration
See `code/config.py` and `config.yaml` (if present) for configuration options.