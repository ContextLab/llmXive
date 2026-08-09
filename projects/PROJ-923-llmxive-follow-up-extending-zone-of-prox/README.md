# llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

**Project ID**: PROJ-923-llmxive-follow-up-extending-zone-of-prox
**Status**: Active Research Pipeline

## Overview
This project implements a follow-up study to "Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradient".
The core extension is **Confidence-Adaptive Pruning (CAP)**, a mechanism that dynamically prunes negative candidates
from the NCQ prompt based on the student model's historical confidence scores.

## Structure
- `code/`: Source code for loaders, models, loops, and analysis.
- `data/`: Generated datasets, metrics, and intermediate artifacts.
- `tests/`: Unit, contract, and integration tests.
- `contracts/`: JSON Schema definitions for data validation.
- `specs/`: Design documents and requirements.

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

## Quick Start
1. **Generate Baseline**: `python code/main.py --mode baseline`
2. **Run CAP Simulation**: `python code/main.py --mode cap`
3. **Statistical Analysis**: `python code/main.py --mode compare`

## License
Research Use Only.
