# llmXive Follow-up: Extending JoyAI-VL-Interaction

## Project Setup

This project uses `ruff` for linting and `black` for formatting.

### Prerequisites
- Python 3.9+
- `pip` or `poetry`

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 pip install -r code/requirements-dev.txt
 ```
3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

### Linting and Formatting
- Run linting:
 ```bash
 ruff check code/
 ```
- Run formatting:
 ```bash
 black code/
 ```
- Run both via pre-commit:
 ```bash
 pre-commit run --all-files
 ```

## Project Structure
- `code/src/`: Source code
- `code/tests/`: Test suite
- `data/`: Data artifacts
- `specs/`: Design documents