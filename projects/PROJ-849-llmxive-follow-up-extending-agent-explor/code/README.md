# Semantic Divergence Diagnostic for Agentic Reasoning

## Setup

1. Create a virtual environment:
 ```bash
 python3 -m venv.venv
 source.venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 make install
 ```

## Development

- **Linting**: `make lint` (uses Ruff)
- **Formatting**: `make format` (uses Black)
- **Fix Linting**: `make lint-fix`
- **Tests**: `make test`

## Project Structure

- `code/`: Source code
- `data/`: Datasets and generated data (gitignored)
- `tests/`: Test suite
- `specs/`: Design documents
- `state/`: Runtime state and versioning (gitignored)