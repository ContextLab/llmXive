# PROJ-855: llmXive Follow-up: Extending "Translation as a Bridging Action"

## Project Overview
This project implements the research pipeline for studying translation-only
manipulation strategies for stability prediction, excluding rotation and force
data.

## Directory Structure
- `code/`: Python source code for simulation, training, and evaluation.
- `data/`: Raw and processed datasets, model checkpoints, and metrics.
- `contracts/`: JSON/YAML schemas for data validation.
- `tests/`: Unit and contract tests.
- `specs/`: Design documents and requirements.

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies: `pip install -r code/requirements.txt`
3. Initialize data directories: `python code/scripts/init_data_dirs.py`

## Execution
- Generate Data: `python code/generate_data.py`
- Train Model: `python code/train_model.py`
- Evaluate: `python code/evaluate.py`

## Validation
- Run tests: `pytest tests/`
- Validate schemas: `python -m pytest tests/contract/`
