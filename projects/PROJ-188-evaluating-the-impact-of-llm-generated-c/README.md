# PROJ-188: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation
1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install -r requirements-dev.txt
 ```

3. Configure environment variables:
 ```bash
 cp.env.example.env
 # Edit.env and add your HF_TOKEN
 ```

4. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Linting and Formatting

This project uses **ruff** for linting and **black** for formatting.

### Run manually
```bash
# Format code
black code/ tests/

# Lint code
ruff check code/ tests/
```

### Fix automatically
```bash
ruff check --fix code/ tests/
black code/ tests/
```

## Testing
```bash
pytest
```

## Project Structure
- `code/`: Source code modules
- `tests/`: Test suites
- `data/`: Data artifacts (raw, intermediate, processed)
- `specs/`: Feature specifications
- `projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/`: Project root (this directory)