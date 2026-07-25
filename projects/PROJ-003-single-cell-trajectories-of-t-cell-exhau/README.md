# T-Cell Exhaustion Trajectory Analysis

## Development Setup

### Prerequisites
- Python 3.9+
- R 4.3+ (for Seurat integration)

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install -r requirements-dev.txt
 ```

### Code Quality
This project uses `ruff` for linting and `black` for formatting.

- **Check linting**: `make lint`
- **Check formatting**: `make check-format`
- **Auto-format**: `make format`

### Running Tests
```bash
make test
# Or with coverage
pytest tests/ --cov=code --cov-report=html
```

## Project Structure
- `code/`: Source code
- `data/`: Data storage (raw, processed, results)
- `tests/`: Test suite
- `specs/`: Design documents
- `contracts/`: Data schemas
- `config.yaml`: Environment configuration