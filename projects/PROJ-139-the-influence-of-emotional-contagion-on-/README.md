# llmXive: The Influence of Emotional Contagion on Collective Decision-Making

## Project Setup

This project uses Python 3.11.

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

### Linting and Formatting

This project uses **Black** for formatting and **Ruff** for linting.

- Check formatting: `black --check code/`
- Format code: `black code/`
- Check linting: `ruff check code/`
- Fix linting issues: `ruff check --fix code/`

Alternatively, use the provided scripts:
- `./scripts/lint.sh`
- `./scripts/format.sh`
- `./scripts/setup_linting.sh`

### Running Tests

```bash
pytest
```

### Data Structure

- `data/raw/`: Raw downloaded data
- `data/processed/`: Processed datasets
- `code/`: Source code
- `state/`: Artifact hashes and logs
- `docs/`: Documentation

## Development Workflow

1. Create a new branch for your task.
2. Implement your changes.
3. Run `./scripts/format.sh` and `./scripts/lint.sh` to ensure code quality.
4. Run `pytest` to verify tests pass.
5. Commit your changes.