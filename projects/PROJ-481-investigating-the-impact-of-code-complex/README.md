# llmXive: Investigating the Impact of Code Complexity on LLM Code Understanding

## Project Setup

This project uses Python 3.11.

### Dependencies

Install dependencies via pip:
```bash
pip install -r requirements.txt
```

### Linting and Formatting

This project enforces code style using **Black** and **Ruff**.

**Formatting**:
```bash
black code/ tests/
```

**Linting**:
```bash
ruff check code/ tests/
```

**Combined Check**:
```bash
ruff check code/ tests/ && black --check code/ tests/
```

## Directory Structure

- `code/`: Source code for the pipeline
- `data/`: Raw and derived data artifacts
- `results/`: Analysis results, plots, and reports
- `tests/`: Unit and integration tests
