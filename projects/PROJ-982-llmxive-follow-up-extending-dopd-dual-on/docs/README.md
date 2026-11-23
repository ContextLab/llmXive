# DOPD Dual-On Privilege Illusion - Documentation

## Overview
This project implements a discrete-state MDP environment to study the effects of
privilege information asymmetry between a Teacher (Oracle) and a Student agent.
It compares Dynamic On-Policy Distillation (DOPD) against Uniform supervision.

## Directory Structure
- `code/`: Source code for environments, agents, training, and analysis.
- `data/`: Raw and processed data artifacts.
- `tests/`: Test suites for validation.
- `docs/`: This documentation.
- `specs/`: Project specifications and design documents.

## User Stories
1. **US1**: Construct Discrete Privilege Illusion MDP Environment.
2. **US2**: Implement DOPD vs. Uniform Supervision Training Loops.
3. **US3**: Execute Statistical Generalization Analysis.

## Running Tests
```bash
pytest code/tests/
```

## Execution
To run the full experiment:
```bash
python code/scripts/run_experiment.py
```

See `quickstart.md` for detailed setup instructions.
