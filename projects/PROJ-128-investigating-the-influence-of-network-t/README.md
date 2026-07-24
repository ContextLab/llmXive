# PROJ-128: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Project Structure

This project follows the llmXive automated science pipeline structure:

- `code/`: Source code for data loading, preprocessing, analysis, and reporting.
- `data/`: Data storage.
 - `raw/`: Raw data fetched from HCP OpenNeuro.
 - `processed/`: Processed metrics (CSVs, JSONs).
 - `logs/`: Execution logs and exclusion records.
- `contracts/`: Schema definitions for data validation.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and research plans.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python code/main.py`

## Data Integrity

This project strictly uses real HCP data. No synthetic data is generated or used.
Data is fetched programmatically from OpenNeuro during execution.
