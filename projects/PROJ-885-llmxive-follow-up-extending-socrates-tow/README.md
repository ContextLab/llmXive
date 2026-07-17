# llmXive: Dynamic Socio-Cognitive State Injection

This project implements a pipeline for generating conflict trajectories and running mediation experiments with dynamic state injection.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

## Linting and Formatting

This project uses **Black** for formatting and **Ruff** for linting.

### Running Linting

```bash
ruff check code/ tests/
```

### Running Formatting

```bash
black code/ tests/
```

### Fixing Issues Automatically

```bash
ruff check --fix code/ tests/
black code/ tests/
```

## Project Structure

- `code/`: Source code for the pipeline
- `data/`: Data storage (raw, processed, results)
- `tests/`: Test suite
- `specs/`: Feature specifications

## Execution

See `specs/001-dynamic-state-injection/quickstart.md` for detailed execution steps.