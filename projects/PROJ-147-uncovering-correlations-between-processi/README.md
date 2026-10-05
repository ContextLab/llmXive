# llmXive: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

This project implements a data-driven pipeline to analyze correlations between processing conditions and texture in rolled metals.

## Project Structure

- `code/`: Source code for the pipeline.
- `data/`: Raw and processed data.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation and schemas.
- `figures/`: Generated plots.
- `models/`: Trained model artifacts.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize directories: `python code/data/setup_directories.py`
3. Run tests: `pytest tests/`

## Usage

Run the main pipeline:
```bash
python code/main.py
```