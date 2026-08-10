# llmXive Follow-up: Extending Qwen-Image-Agent

This project implements a hybrid routing system for image generation agents based on syntactic complexity.

## Project Structure

- `src/`: Source code for scoring, routing, fidelity analysis, and pipeline execution.
- `tests/`: Unit and integration tests.
- `data/`:
 - `raw/`: Downloaded datasets (IA-Bench, WISE-Verified).
 - `derived/`: Processed results (scores, routing decisions, images, regression outputs).
- `requirements.txt`: Python dependencies.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python src/main.py`

See `tasks.md` for the implementation roadmap.