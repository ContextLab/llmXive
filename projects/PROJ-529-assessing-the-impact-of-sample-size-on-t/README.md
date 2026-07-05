# llmXive Project: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Project Setup

### Prerequisites
- Python 3.11+

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install linting and formatting tools:
 ```bash
 pip install ruff black
 ```
 Or run the setup script:
 ```bash
 bash scripts/setup_linting.sh
 ```

## Configuration

### Linting (Ruff)
Configuration is in `.ruff.toml`.
Run checks:
```bash
ruff check code/ tests/
```

### Formatting (Black)
Configuration is in `pyproject.toml`.
Run formatter:
```bash
black code/ tests/
```
Check formatting without modifying:
```bash
black --check code/ tests/
```

## Directory Structure
- `code/`: Source code
 - `utils/`: Utility modules
 - `models/`: Model definitions
 - `tests/`: Test modules
- `data/`: Data storage
 - `raw/`: Raw downloaded data
 - `processed/`: Processed data
 - `output/`: Final outputs
- `tests/`: Test directory (mirrors code structure)
 - `unit/`: Unit tests
 - `integration/`: Integration tests
- `specs/`: Feature specifications

## Development Workflow
1. Write code
2. Format with Black: `black code/ tests/`
3. Lint with Ruff: `ruff check code/ tests/`
4. Run tests