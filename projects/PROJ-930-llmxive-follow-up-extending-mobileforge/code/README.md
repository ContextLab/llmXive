# llmXive Follow-up: Extending MobileForge with CPU-Tractable Logic Distillation

## Project Setup

This project uses Python 3.11+ and requires specific linting and formatting tools.

### Prerequisites

- Python 3.11 or higher
- pip and virtualenv (recommended)

### Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Install development tools (linting and formatting):
 ```bash
 pip install -e "code[dev]"
 ```

### Linting and Formatting

This project uses **Ruff** for linting and **Black** for code formatting.

#### Running the Linter

To check code quality:
```bash
cd code
ruff check.
```

To fix linting errors automatically:
```bash
ruff check --fix.
```

#### Running the Formatter

To format code automatically:
```bash
cd code
black.
```

To check formatting without modifying files:
```bash
black --check.
```

#### Pre-commit Hooks (Optional)

To run linting and formatting automatically before commits:
```bash
pip install pre-commit
pre-commit install
```

### Testing

Run the test suite:
```bash
cd code
pytest
```

### Configuration

All configuration for linting and formatting is defined in `pyproject.toml` under `[tool.ruff]` and `[tool.black]` sections.

- **Line Length**: 88 characters
- **Target Version**: Python 3.11
- **Linting Rules**: E, W, F, I, C, B, UP
- **Ignored Rules**: E501 (line length), B008, C901 (complexity)