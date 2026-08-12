# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-132-statistical-analysis-of-publicly-availab
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Install pre-commit hooks**:
 Ensure `pre-commit` is installed (included in `requirements.txt`), then run:
 ```bash
 pre-commit install
 ```
 This will automatically run `black` and `ruff` on every commit.

## Usage

Run the full pipeline:
```bash
python -m src.cli.run_pipeline
```

Or run specific stages:
```bash
python code/setup_project.py
python code/run_pipeline.py
```

## Development

- **Formatting**: Code is formatted with `black` and linted with `ruff`.
- **Testing**: Run tests with `pytest`.
- **Pre-commit**: Ensure all hooks pass before committing.

## Project Structure

- `src/`: Source code
- `data/`: Data files (raw, processed, interim)
- `tests/`: Test suite
- `docs/`: Documentation
- `code/`: Standalone scripts for pipeline execution