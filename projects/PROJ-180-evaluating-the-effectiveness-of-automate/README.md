# Evaluating Automated Code Review Tools Effectiveness

## Setup

1. Create a virtual environment and activate it:
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
 pip install pre-commit
 pre-commit install
 ```

## Development

### Linting and Formatting

This project uses **Ruff** for linting and **Black** for formatting.

- Run linting manually:
 ```bash
 ruff check.
 ```

- Run formatting manually:
 ```bash
 black.
 ```

- Run both with pre-commit:
 ```bash
 pre-commit run --all-files
 ```

### Testing

Run tests with pytest:
```bash
pytest
```

## Project Structure

- `code/`: Source code for data acquisition, analysis, and utilities.
- `data/raw`: Raw data downloaded from external sources (GitHub).
- `data/processed`: Processed data ready for analysis.
- `results`: Output reports, figures, and statistical summaries.
- `specs/`: Project specifications and design documents.
- `tests/`: Unit and integration tests.