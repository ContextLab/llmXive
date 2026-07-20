# Brain Network Topology and Visual Illusions

## Development Setup

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
pip install -r requirements.txt
```

### Tooling Configuration
This project uses:
- **flake8** for linting (configured in `.flake8`)
- **black** for code formatting (configured in `pyproject.toml`)
- **isort** for import sorting (configured in `pyproject.toml`)
- **mypy** for static type checking (configured in `mypy.ini`)

To verify your environment:
```bash
python code/utils/setup_tooling.py
```

### Running Checks
```bash
# Format code
black code/ tests/
isort code/ tests/

# Lint code
flake8 code/ tests/

# Type check
mypy code/ tests/
```

### CI Integration
Ensure all checks pass before committing. Consider setting up a `pre-commit` hook
(see T007) to run these automatically.