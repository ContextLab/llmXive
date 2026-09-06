# OPID Critical-First Routing Complexity Analysis

Automated science pipeline for analyzing routing complexity in State-Graph Environments.

## Project Structure

- `code/`: Source code modules
 - `config.py`: Configuration management
 - `env/`: Environment and graph generation logic
 - `experiments/`: Experiment runners and analyzers
 - `utils/`: Utility functions
- `data/`: Data storage
 - `raw/`: Raw synthetic graphs
 - `processed/`: Processed experiment results
- `tests/`: Unit and integration tests
- `docs/`: Documentation

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # or
 venv\Scripts\activate # Windows
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

See `quickstart.md` for detailed usage instructions.

## Development

- Run tests: `pytest`
- Run linter: `ruff check code/`
- Format code: `black code/`
