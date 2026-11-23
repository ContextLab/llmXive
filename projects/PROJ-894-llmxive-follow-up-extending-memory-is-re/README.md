# llmXive Follow-up: Extending "Memory is Reconstructed, Not Retrieved"

This project implements research code for analyzing graph-based memory reconstruction in LLM agents.

## Project Structure

- `code/`: Source code for the research pipeline
- `data/`: Data storage
 - `raw/`: Raw downloaded datasets
 - `intermediate/`: Intermediate processing artifacts
 - `processed/`: Final processed data and results
 - `graphs/`: Graph structures
 - `results/`: Execution results
- `tests/`: Test suite

## Setup

1. Run `python setup_directories.py` to ensure the directory structure is created.
2. Install dependencies: `pip install -r code/requirements.txt`
3. Download spaCy model: `python code/scripts/setup_spacy.py` (after T011a-3 is implemented)

## Usage

Refer to `quickstart.md` for execution instructions.