# Evaluating Resting-State fMRI Entropy as a Biomarker for Attention-Deficit Traits

## Setup

### Prerequisites
- Python 3.10+
- pip

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Install development dependencies (for linting and testing):
 ```bash
 pip install -e ".[dev]"
 ```

### Linting and Formatting
This project uses `ruff` for linting and `black` for code formatting.

**Format code:**
```bash
black code/ tests/
```

**Lint code:**
```bash
ruff check code/ tests/
```

**Fix linting issues automatically:**
```bash
ruff check --fix code/ tests/
```

**Run all checks in one go:**
```bash
black --check code/ tests/ && ruff check code/ tests/
```

## Quickstart
To run the full pipeline after setup:
```bash
python code/main.py
```

See `docs/` for detailed documentation.