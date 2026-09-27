# PROJ-030: Predicting Crystal Structures from Molecular Fingerprints

## Project Structure
- `code/`: Python source code, configuration, and scripts
- `data/`: Raw and processed datasets
- `tests/`: Unit and integration tests
- `docs/`: Documentation and planning artifacts
- `specs/`: Feature specifications and user stories

## Setup
1. Create virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install dependencies: `pip install -r code/requirements.txt`
3. Configure environment variables:
 - `HF_TOKEN`: HuggingFace API token (for dataset access)
 - `HF_HOME`: Cache directory for HuggingFace datasets

## Running the Pipeline
See `code/ingestion/run_pipeline.py` for the main data ingestion entry point.
See `code/modeling/train.py` for model training.
