# llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Project ID**: PROJ-860-llmxive-follow-up-extending-dragmesh-2-p

## Overview
This project implements a virtual tactile adaptation pipeline for zero-shot
generalization to unseen damping and friction conditions using PyBullet physics
simulations.

## Structure
- `code/`: Source code for simulation, estimation, and training
- `data/`: Raw and generated data assets
- `tests/`: Unit and integration tests
- `state/`: Project state tracking and artifact hashes

## Installation
```bash
cd code
pip install -r requirements.txt
```

## Usage
See individual scripts for CLI usage:
- `python code/generator.py --help`
- `python code/train.py --help`
- `python code/evaluate.py --help`

## License
MIT
