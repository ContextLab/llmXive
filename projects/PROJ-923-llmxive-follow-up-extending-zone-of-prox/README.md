# llmXive Follow-up: Extending Zone of Proximal Policy Optimization

## Project Setup

This project implements a simulation of the ZPPO training loop with Confidence-Adaptive Pruning (CAP).

### Prerequisites

- Python 3.9+
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
 ```

### Development Tools

This project uses `black` for formatting and `ruff` for linting.

### Running Linters and Formatters

```bash
# Check formatting
make format

# Auto-fix formatting
make format-write

# Check linting
make lint

# Run all checks
make check
```

### Running Tests

```bash
pytest tests/
```

### Running the Simulation

```bash
python code/main.py --runs 10 --seeds 10
```
