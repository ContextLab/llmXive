# PROJ-177: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Project Structure

This project follows the standard llmXive pipeline structure:

- `code/`: Python modules for data ingestion, analysis, and orchestration.
- `data/`: Raw input data and derived datasets.
 - `data/raw/`: Unprocessed particle tracking and driving signal logs.
 - `data/derived/`: Computed energy components and intermediate results.
- `artifacts/`: Final outputs, statistical results, and reports.
- `tests/`: Unit and integration tests for all modules.
- `specs/`: Design documents and user stories.
- `state/`: Pipeline state tracking and artifact hashes.

## Prerequisites

- Python 3.11+
- `requirements.txt` dependencies (see T002)

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the full pipeline:
 ```bash
 python code/main.py --run-all
 ```

3. Run specific stages:
 ```bash
 python code/main.py --stage ingestion
 python code/main.py --stage statistics
 ```

## License

Research project for scientific investigation.
