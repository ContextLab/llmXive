# PROJ-895: llmXive Follow-up: Extending OCC-RAG Optimal Cognitive Core

This project implements a gradient-free sensitivity analysis to identify the critical sparse sub-network within the OCC-RAG model that maintains faithfulness in question answering.

## Structure
- `code/`: Python implementation modules
- `data/`: Raw and processed datasets
- `tests/`: Unit and integration tests
- `specs/`: Design documents and requirements

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run setup: `python code/scripts/setup_data_dirs.py`
3. Execute pipeline: `python code/01_sensitivity_analysis.py`
