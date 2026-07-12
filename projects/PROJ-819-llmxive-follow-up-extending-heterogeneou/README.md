# llmXive Project: Extending Heterogeneous Scientific Foundation Model Collaboration

## Setup

### Prerequisites
- Python 3.10+

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

### Configuration
This project uses `black` for formatting and `ruff` for linting. Configuration is in `pyproject.toml` and `ruff.toml`.

### Running Linting and Formatting
To check code quality:
```bash
# Check formatting
black --check code/ tests/

# Run linter
ruff check code/ tests/
```

To automatically fix formatting issues:
```bash
black code/ tests/
```

### Testing
```bash
pytest
```

## Project Structure
- `code/`: Source code
- `data/`: Data files
- `tests/`: Test suites
- `state/`: Manifest and hashes
- `specs/`: Design documents

## Task Status
- [X] T001a: Project directories created
- [X] T001b: __init__.py files created
- [X] T002: Python project initialized with requirements
- [X] T003: Linting and formatting tools configured
- [ ] T004: Pytest configuration
... (remaining tasks)