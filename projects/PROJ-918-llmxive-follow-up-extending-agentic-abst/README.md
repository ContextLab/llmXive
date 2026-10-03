# llmXive: Agentic Abstention Follow-up

This project implements the automated science pipeline for the "Agentic Abstention: Do Agents Know When to Stop Instead of Act?" follow-up study.

## Project Structure

- `code/`: Source code for data ingestion, feature extraction, model training, and analysis.
- `data/`: Data storage.
 - `raw/`: Original benchmark data (downloaded via `code/data/ingest.py`).
 - `processed/`: Feature-engineered datasets and models.
 - `results/`: Statistical reports and comparison metrics.
- `tests/`: Test suite.
 - `contract/`: Schema and output contract tests.
 - `integration/`: End-to-end pipeline tests.
 - `unit/`: Unit tests for individual functions.
- `state/`: Pipeline state management and snapshots.

## Setup

1. Ensure Python 3.11 is installed.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the ingestion pipeline: `python code/data/ingest.py`
4. Run tests: `pytest`

## Execution

Follow the tasks in `tasks.md` to execute the pipeline phases sequentially.