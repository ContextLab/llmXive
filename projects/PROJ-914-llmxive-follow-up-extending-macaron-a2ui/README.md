# llmXive: Follow-up: Extending "Macaron-A2UI"

Automated science pipeline for studying latency and alignment in generative UI agents.

## Project Structure

- `code/`: Source code for ingestion, models, simulation, and analysis
- `data/`: Raw and processed datasets (excluded from git)
- `specs/`: Design documents and contracts
- `tests/`: Unit, integration, and contract tests
- `state/`: Versioning and experiment state tracking

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure environment:
 ```bash
 cp.env.example.env
 # Edit.env to add your HF_TOKEN if required
 ```

## Running the Pipeline

Refer to `specs/001-llmxive-a2ui-latency-study/quickstart.md` for execution steps.

## Testing

```bash
pytest tests/
```

## Linting & Formatting

```bash
ruff check code/
black code/
```