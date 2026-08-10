# llmXive: Evaluating the Impact of Code Generation on Code Review Quality

## Setup

### Prerequisites
- Python 3.11+

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

### Configuration
This project uses:
- **Ruff** for linting (configured in `.ruff.toml`)
- **Black** for formatting (configured in `pyproject.toml`)
- **Pre-commit** for automated checks (configured in `.pre-commit-config.yaml`)

### Usage
Run linter:
```bash
ruff check.
```

Run formatter:
```bash
black.
```

Run tests:
```bash
pytest
```

### Project Structure
- `code/`: Source code modules
- `data/`: Raw and processed data
- `tests/`: Unit and integration tests
- `reports/`: Generated figures and reports
- `specs/`: Design documents
