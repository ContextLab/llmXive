# llmXive: SWE-Explore Extension

This project extends the "SWE-Explore" benchmark to investigate iterative exploration strategies for coding agents.

## Project Structure

- `code/`: Source code for data processing, agents, and analysis.
- `data/raw/`: Raw downloaded datasets.
- `data/curated/`: Curated and processed datasets.
- `data/results/`: Experiment outputs and logs.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Design documents and contracts.

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Create project structure (if not already present):
 ```bash
 python code/setup_project_structure.py
 ```

3. Run the pipeline (see `docs/quickstart.md` for full details).

## Verification

Run the verification script to ensure structure is correct:
```bash
python code/validate_quickstart.py
```