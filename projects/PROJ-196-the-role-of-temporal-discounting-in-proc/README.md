# The Role of Temporal Discounting in Procrastination on Cognitive Tasks

## Project Overview
This project investigates the relationship between temporal discounting rates and procrastination behaviors in cognitive tasks, moderated by working memory capacity.

## Environment Setup
This project requires Python 3.11.

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

### Development Setup
Install development tools (linters, formatters, test runners):
```bash
pip install -e ".[dev]"
```

## Project Structure
```
.
├── code/ # Source code
│ ├── config.py # Configuration and seed management
│ ├── ingestion.py # Data generation and harmonization
│ ├── modeling.py # Statistical modeling
│ ├── robustness.py # Robustness checks
│ └── utils/ # Utility modules
├── data/
│ ├── raw/ # Raw/generated data
│ └── processed/ # Processed datasets
├── tests/ # Test suite
├── specs/ # Feature specifications
├── state/ # Project state tracking
├── requirements.txt # Pinned dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## Execution
Run the full pipeline:
```bash
python code/ingestion.py
python code/modeling.py
python code/robustness.py
```

Run tests:
```bash
pytest tests/
```

Run linters:
```bash
ruff check code/
black --check code/
```
