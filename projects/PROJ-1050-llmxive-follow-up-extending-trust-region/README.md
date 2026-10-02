# llmXive Follow-up: Extending Trust Region Policy Distillation

## Project Structure
- `code/`: Source code
- `data/`: Data artifacts (raw, processed)
- `tests/`: Test suite
- `docs/`: Documentation and results

## Setup
1. Install dependencies: `pip install -r code/requirements.txt`
2. Install dev tools: `pip install -e ".[dev]"`
3. Install pre-commit hooks: `pre-commit install`

## Linting & Formatting
This project uses **Ruff** for linting and **Black** for formatting.
- Lint: `ruff check code/`
- Format: `ruff format code/` (or `black code/`)
- Fix automatically: `ruff check --fix code/`
