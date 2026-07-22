# llmXive: Extending LiveCodeBench to Multiple Programming Languages

## Project Structure
- `code/`: Source code for the pipeline
- `data/`: Raw and processed data
- `tests/`: Unit and integration tests
- `specs/`: Design documents

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure model path in `code/config.py` or via `LLMXIVE_MODEL_PATH` env var.

## Running the Pipeline
```bash
python code/main.py
```

## Tasks
This project implements tasks T001-T049 as defined in `tasks.md`.
Current status: T001 (Project Structure) - Completed.