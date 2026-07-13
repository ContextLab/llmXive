# Development Setup

This project uses `black` for formatting and `ruff` for linting.

## Prerequisites

Ensure you have Python 3.11+ installed.

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies and development tools:
 ```bash
 pip install -r requirements.txt
 pip install black ruff
 ```

## Usage

### Formatting

To format the codebase:
```bash
black code/
```

### Linting

To check for linting errors:
```bash
ruff check code/
```

To automatically fix fixable issues:
```bash
ruff check --fix code/
```

### Pre-commit Hook (Optional)

To run these checks before committing:
```bash
pip install pre-commit
pre-commit install
```
(Add a `.pre-commit-config.yaml` file to your repo root if you wish to automate this).
