# Quantifying the Impact of Data Cleaning on Statistical Inference

## Development Setup

### Prerequisites
- Python 3.11+

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install -r requirements-dev.txt
 ```

### Linting and Formatting
This project uses `ruff` for linting and `black` for formatting.

**Check code quality:**
```bash
python code/run_lint.py
```

**Fix formatting and auto-fixable linting issues:**
```bash
python code/run_lint.py format
```

**Manual commands:**
```bash
black code/
ruff check code/
```

## Project Structure
- `code/`: Source code
- `data/raw/`: Raw downloaded datasets
- `data/processed/`: Processed datasets and analysis results
- `tests/`: Test suite
- `specs/`: Feature specifications