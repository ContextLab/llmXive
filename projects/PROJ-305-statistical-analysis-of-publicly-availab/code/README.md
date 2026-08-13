# Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
This project uses `ruff` for linting and `black` for formatting. Configuration is provided in:
- `.ruff.toml`
- `.flake8`
- `pyproject.toml` (for Black and pytest)

### Running Linters and Formatters
```bash
# Format code
black code/

# Lint code
ruff check code/
```

### Running Tests
```bash
pytest
```

## Project Structure
- `code/`: Source code
- `data/`: Data files
- `output/`: Analysis outputs
- `tests/`: Test suite
- `specs/`: Design documents
