# llmXive: Follow-up: Extending SWE-Explore

This project implements an automated science pipeline to benchmark how coding agents explore repositories, extending the "SWE-Explore" study.

## Project Structure

The project follows a standard data science structure:
- `code/`: Source code, modules, and scripts.
- `data/raw/`: Raw data fetched from external sources.
- `data/curated/`: Cleaned, filtered, and derived datasets.
- `data/results/`: Intermediate and final analysis results.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Design documents and schema contracts.

## Setup

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Initialize project structure (if not already done):
 ```bash
 python code/setup_project_structure.py
 ```

## Execution

Refer to `docs/quickstart.md` for the full pipeline execution commands.

## License

MIT License