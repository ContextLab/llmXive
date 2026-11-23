# PROJ-815: llmXive Follow-up: Extending Intern-Atlas

This project implements the automated science pipeline for extending the Intern-Atlas graph analysis.

## Structure

- `code/`: Source code for data extraction, feature engineering, and modeling.
- `data/`: Raw and processed data artifacts.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and specifications.

## Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and configure environment variables.

## Execution

Run the extraction pipeline:
`python code/data/run_extraction.py`
