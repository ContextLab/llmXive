# QM9 ML Pipeline

## Development Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install -r requirements-dev.txt
 ```

2. Install pre-commit hooks (optional but recommended):
 ```bash
 pre-commit install
 ```

3. Run linting and formatting:
 ```bash
 # Check code
 ruff check code/
 black --check code/

 # Fix code automatically
 ruff check --fix code/
 black code/
 ```

4. Run tests:
 ```bash
 pytest tests/
 ```

## Project Structure

- `code/`: Source code for the pipeline
- `data/`: Raw and processed data
- `artifacts/`: Model outputs and metrics
- `tests/`: Unit and integration tests
- `specs/`: Project specifications
