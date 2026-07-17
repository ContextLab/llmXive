# llmXive Follow-up: Extending APPO Agentic Procedural Policy Optimization

This project implements the APPO (Agentic Procedural Policy Optimization) follow-up research pipeline.

## Prerequisites

- Python 3.9+
- CPU-only environment (CUDA not required/used)

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` is managed by `pyproject.toml` dependencies in this setup.*

2. Install development tools (linters/formatters):
 ```bash
 pip install -e ".[dev]"
 ```

## Code Style

This project uses `ruff` for linting and `black` for formatting.

To format code:
```bash
black code/ tests/
ruff check --fix code/ tests/
```

To check linting only:
```bash
ruff check code/ tests/
```

## Project Structure

- `code/`: Source code for the pipeline
- `data/`: Input and output data (generated at runtime)
- `tests/`: Unit and integration tests
- `contracts/`: Schema definitions
- `docs/`: Documentation

## Execution

Run the scaffold to initialize directories:
```bash
python code/utils/scaffold.py
```

Run tests:
```bash
pytest
```
