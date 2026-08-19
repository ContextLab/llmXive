# llmXive Follow-up: Extending Macaron-A2UI

This project implements a study on latency and fidelity in generative UI for personal agents, extending the "Macaron-A2UI" model.

## Project Structure

- `code/`: Source code for ingestion, simulation, models, and analysis.
- `data/`: Raw and processed data artifacts.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Feature specifications and design documents.
- `figures/`: Generated plots and visualizations.

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

3. Configure environment variables:
 ```bash
 cp.env.example.env
 # Edit.env as needed
 ```

## Running the Pipeline

Refer to `specs/001-llmxive-a2ui-latency-study/quickstart.md` for detailed execution steps.

## Development

- Formatting: `black code/ tests/`
- Linting: `ruff check code/ tests/`
- Testing: `pytest`

## License

[Insert License]
