# llmXive Benchmark Project

Heterogeneous Scientific Foundation Model Collaboration Benchmark.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -c "import src; print('Project structure verified.')"
 ```

## Project Structure

- `src/`: Source code
- `tests/`: Test suites
- `data/`: Data storage
- `state/`: State tracking
- `contracts/`: Schema definitions
- `research/`: Research scripts and documentation

## Development

Linting and formatting are configured via `pyproject.toml` (Black) and `ruff.toml` (Ruff).
