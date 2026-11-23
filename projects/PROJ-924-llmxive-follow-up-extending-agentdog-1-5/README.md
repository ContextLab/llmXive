# PROJ-924: llmXive Follow-up - Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Project Structure

This project implements zero-shot drift detection for LLM safety logs.

- `code/`: Python source modules (drift scoring, taxonomy building, validation).
- `data/`:
 - `raw/`: Downloaded datasets (AdvBench, HF4, OWASP Taxonomy).
 - `processed/`: Intermediate and final results (drift scores, merged annotations).
 - `test/`: Static fixtures and mock data for unit testing.
- `specs/`: Design documents and requirements.
- `docs/`: User guides and API documentation.
- `tests/`: Unit and integration tests.

## Setup

1. Ensure Python 3.11 is installed.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the pipeline: `python code/main.py`

## License

Internal use only.