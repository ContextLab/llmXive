# PROJ-205: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

## Setup

1. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```

2. **Install Pre-commit Hooks** (Optional but recommended)
 ```bash
 pip install pre-commit
 pre-commit install
 ```

## Development

### Linting & Formatting

This project uses **Black** for formatting and **Ruff** for linting.

- **Format code**: `black code/`
- **Check formatting**: `black --check code/`
- **Lint code**: `ruff check code/`
- **Fix linting errors**: `ruff check --fix code/`

### Testing

Run the test suite:
```bash
pytest tests/
```

### Running the Survey App

```bash
streamlit run code/survey/app.py
```

## Project Structure

- `code/`: Source code
- `data/`: Data files (raw, processed, consent)
- `tests/`: Test suite
- `specs/`: Feature specifications
- `docs/`: Design documents and protocols