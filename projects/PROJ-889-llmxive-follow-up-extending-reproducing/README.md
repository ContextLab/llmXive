# llmXive: Automated Science Pipeline

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
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

### Running Linters and Formatters Manually

To run Ruff (linting):
```bash
ruff check code/ tests/
```

To run Black (formatting):
```bash
black code/ tests/
```

To run both via Ruff format (if configured):
```bash
ruff format code/ tests/
```

### Running Tests

```bash
pytest tests/ -v
```

## Project Structure

- `code/`: Source code modules
- `data/`: Raw and processed data
- `tests/`: Unit and integration tests
- `contracts/`: Data validation schemas
- `specs/`: Design documents
