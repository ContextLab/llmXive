# llmXive: Automated Science Pipeline

A research pipeline for analyzing code artifacts and predicting dynamic execution necessity.

## Project Structure

- `code/`: Python modules and scripts for the pipeline
- `data/`: Raw, processed, and graph data artifacts
- `tests/`: Unit, contract, and integration tests
- `docs/`: Documentation
- `models/`: Trained models and decision boundaries
- `contracts/`: JSON/YAML schemas for validation

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the ingestion pipeline: `python code/scripts/ingest.py`
3. Extract features: `python code/scripts/extract_features.py`
4. Train model: `python code/scripts/train_model.py`

See `docs/usage.md` for detailed instructions.
