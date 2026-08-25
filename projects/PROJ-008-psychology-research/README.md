# Mindfulness in ASD Social Skills Meta-Analysis

This project implements a systematic review and meta-analysis of mindfulness-based interventions for improving social skills in children with Autism Spectrum Disorder (ASD).

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-008-psychology-research
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

4. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Linting and Formatting

This project uses **Ruff** for linting and **Black** for formatting.

### Running Linting
```bash
ruff check.
```

### Running Formatting
```bash
ruff format.
# Or
black.
```

### Pre-commit
To automatically check and fix code before committing:
```bash
pre-commit run --all-files
```

## Project Structure
- `code/`: Source code modules
- `data/`: Raw and processed data
- `tests/`: Unit and integration tests
- `contracts/`: Data schema definitions
- `docs/`: Documentation and reports
- `specs/`: Research specifications and plans

## Running the Pipeline
Refer to `quickstart.md` for detailed execution steps.
