# llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

This project implements the follow-up research on extending the Zone of Proximal Policy Optimization (ZPPO) method, focusing on "Teacher in Prompts, Not Gradient".

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e.
 ```

3. Run tests:
 ```bash
 pytest
 ```

## Formatting and Linting

This project uses `black` for formatting and `ruff` for linting.

To format code:
```bash
black.
```

To check linting:
```bash
ruff check.
```

To fix linting issues automatically:
```bash
ruff check. --fix
```

## Project Structure

- `code/`: Source code
- `data/`: Data files and outputs
- `tests/`: Test suites
- `contracts/`: Schema definitions
- `specs/`: Design documents
- `data/models/`: Data models and state stores
- `data/loops/`: Training loop implementations
- `data/analysis/`: Metrics and statistical analysis

## Configuration

Configuration is managed via YAML files in the `config/` directory (if present) or via the `config.py` module.

## License

Research code - see LICENSE file for details.
