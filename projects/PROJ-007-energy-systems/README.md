# PROJ-007-energy-systems

Automated science pipeline for analyzing energy inequity in low-income communities.

## Setup

1. Create virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e.
 ```

## Linting and Formatting

This project uses **Black** for formatting and **Ruff** for linting.

To format code:
```bash
black.
```

To lint code:
```bash
ruff check.
```

To fix linting issues automatically:
```bash
ruff check --fix.
```

## Running Tests

```bash
pytest
```

## Project Structure

- `src/`: Source code
- `tests/`: Test suite
- `data/`: Data artifacts (ignored by git)
- `specs/`: Research specifications and plans

## Configuration

See `src/config.yaml` for analysis parameters.