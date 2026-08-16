# llmXive Follow-up: Extending Weak-to-Strong Generalization

## Project Setup

This project requires Python 3.11+ and uses `pip` for dependency management.

### Prerequisites

- Python 3.11 or higher
- pip (>= 23.0)

### Installation

1. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -m pytest code/tests/test_environment.py -v
 ```

### Development Tools

The project includes `ruff` for linting and `black` for formatting.

- Run linter: `python -m code.scripts.run_lint`
- Run formatter: `python -m code.scripts.run_format`

### Project Structure

```
.
├── code/ # Source code
│ ├── core/ # Core utilities (trainer, evaluator, etc.)
│ ├── data/ # Data loading and preprocessing
│ ├── models/ # Model loaders (MoE, SSM, Teacher)
│ ├── scripts/ # Utility scripts
│ └── tests/ # Test suite
├── data/ # Data directory (raw, processed, results)
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration (ruff, black, pytest)
└── README.md
```

## Running Experiments

Refer to `tasks.md` for the execution order of specific experiments (MoE, SSM).

## License

Research use only.
