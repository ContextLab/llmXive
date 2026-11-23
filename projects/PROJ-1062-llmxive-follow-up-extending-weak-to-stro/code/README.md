# llmXive Follow-up: Extending Weak-to-Strong Generalization

This project implements Direct On-Policy Distillation experiments comparing MoE and SSM student models against Transformer teachers.

## Prerequisites

- Python 3.11
- CPU-only PyTorch environment (no GPU required)

## Installation

1. Ensure you are using Python 3.11:
 ```bash
 python --version
 ```

2. Install dependencies. For CPU-only PyTorch, use the extra index URL:
 ```bash
 pip install -r code/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
 ```

3. Verify installation:
 ```bash
 cd code
 python -m pytest tests/test_environment.py -v
 ```

## Project Structure

- `code/`: Source code modules
- `data/`: Raw and processed datasets
- `tests/`: Unit and integration tests
- `specs/`: Design documents

## Execution

See `tasks.md` for the list of executable scripts and their dependencies.
