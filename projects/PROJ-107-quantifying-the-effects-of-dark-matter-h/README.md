# llmXive Research Pipeline: Dark Matter Halo Shapes

This project implements the automated science pipeline for quantifying the effects of dark matter halo shapes on galaxy formation.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Code Quality Tools

This project uses **Black** for formatting, **Ruff** for linting, and **Flake8** as a legacy compatibility layer.

### Formatting

Format code using Black:
```bash
black code/
```

### Linting

Check code using Ruff:
```bash
ruff check code/
```

Alternatively, using Flake8:
```bash
flake8 code/
```

### Pre-commit Hooks (Optional)

To automatically run these checks before committing, install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

## Running the Pipeline

See `docs/sampling_protocol.md` and `data/metadata.yaml` for data configuration.

Execute the main pipeline:
```bash
python code/main.py
```

## Testing

Run the test suite:
```bash
pytest code/tests/
```

## Project Structure

- `code/`: Source code
- `data/`: Raw and processed data
- `outputs/`: Generated reports and figures
- `docs/`: Documentation
- `state/`: Pipeline state files

## License

Research use only.
