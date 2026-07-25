# PROJ-054: Assessing the Validity of p-Values in High-Dimensional Data

## Linting and Formatting

This project uses **Ruff** for linting and **Black** for code formatting.

### Setup

Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Usage

**Format code:**
```bash
black code/ tests/
```

**Lint code:**
```bash
ruff check code/ tests/
```

**Fix linting issues automatically (where safe):**
```bash
ruff check --fix code/ tests/
```

**Run pre-commit checks (if configured):**
```bash
pre-commit run --all-files
```

## Project Structure

- `code/`: Source code for the research pipeline
- `tests/`: Unit and integration tests
- `data/`: Generated datasets and results
- `docs/`: Documentation
- `specs/`: Feature specifications and design documents