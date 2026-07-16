# PROJ-078: Predicting Polymer Degradation Pathways

Automated science pipeline for predicting polymer degradation pathways using Graph Neural Networks.

## Project Structure

- `code/`: Source code, scripts, and utilities
- `data/raw/`: Raw downloaded data from NIST/Materials Project
- `data/processed/`: Processed and cleaned datasets
- `data/reports/`: Analysis reports and model outputs
- `tests/unit/`: Unit tests
- `tests/integration/`: Integration tests
- `state/`: Checkpoints and intermediate state

## Setup

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Run the pipeline:
 ```bash
 python code/ingest.py
 python code/preprocess.py
 python code/train.py
 ```

## Configuration

Environment variables can be used to configure paths and API keys. See `code/utils.py` for details.
