# PROJ-990: llmXive Follow-up: Extending "AgenticSTS"

This project implements a bounded-memory testbed for long-horizon LLM agents,
focusing on dynamic layer retrieval strategies to optimize token usage while
maintaining performance.

## Structure

- `code/`: Python source modules (entropy, parser, classifier, simulator, etc.)
- `data/`:
 - `raw/`: Input trajectory logs
 - `processed/`: Derived metrics, ablation labels, splits
- `models/`: Trained classifier artifacts
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design docs

## Prerequisites

- Python 3.11+
- Dependencies listed in `requirements.txt`

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Ensure `data/raw/trajectories.csv` exists.
3. Run the pipeline: `python code/parser.py && python code/entropy.py...`
