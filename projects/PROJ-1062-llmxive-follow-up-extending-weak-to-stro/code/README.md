# llmXive Follow-up: Extending Weak-to-Strong Generalization

This project implements the research pipeline for "Weak-to-Strong Generalization via Direct On-Policy Distillation".

## Requirements

- Python 3.11+
- PyTorch 2.1.0+
- Transformers 4.36.0+

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Project Structure

```
code/
├── core/ # Core logic (trainer, evaluator, reward computation)
├── data/ # Data loading and preprocessing
├── models/ # Model loaders (Teacher, MoE Student, SSM Student)
├── scripts/ # Utility scripts
└── tests/ # Unit and integration tests
```

## Running Tests

```bash
python -m pytest code/tests/
```

## Linting and Formatting

```bash
# Lint
python code/scripts/run_lint.py

# Format
python code/scripts/run_format.py
```
