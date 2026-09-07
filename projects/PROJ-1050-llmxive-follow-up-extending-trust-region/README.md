# PROJ-1050: llmXive Follow-up: Extending Trust Region Policy Distillation

## Overview
This project implements a synthetic Reasoning MDP environment and a capacity-constrained student policy to study reasoning collapse under Trust Region Policy Distillation (TOP-D).

## Structure
- `code/`: Source code for environment, policies, experiments, and analysis
- `data/`: Raw and processed data artifacts
- `docs/`: Documentation and results
- `tests/`: Unit and integration tests

## Quickstart
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run experiments: `python code/experiments/runner.py`
3. Analyze results: `python code/analysis/tobit_model.py`

## User Stories
- **US1**: Synthetic Reasoning Environment & Teacher Policy
- **US2**: Capacity-Constrained Student Policy & TOP-D Training Loop
- **US3**: Interaction Analysis & Collapse Detection
