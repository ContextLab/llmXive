# Development Guide

## Setup

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Linting & Formatting

The project uses `flake8` and `black`.

```bash
# Check linting
flake8 code/ tests/

# Format code
black code/ tests/
```

Configuration is in `.flake8` and `pyproject.toml`.

## Running Tests

```bash
pytest tests/
```

Tests are organized into:
- `tests/contract/`: Schema and API contract tests.
- `tests/integration/`: End-to-end pipeline tests.
- `tests/unit/`: Unit tests for individual functions.

## Adding a New Data Source

1. Update `data/config/sources.yaml` with the new source URL and type.
2. Implement the fetching logic in `code/ingestion/api_fetcher.py` or `literature_scraper.py`.
3. Ensure the source is validated by `run_reference_validation.py`.

## Modifying the Pipeline

The pipeline is driven by `code/run_pipeline.py`. To add a new step:
1. Implement the logic in the appropriate module (e.g., `code/features/`).
2. Add the step to `run_pipeline.py` with proper dependency checks.
3. Update `docs/architecture.md` to reflect the change.

## Troubleshooting

- **Missing Artifacts**: Check `logs/pipeline.log` for the step that failed to write its output.
- **Data Validation Errors**: Review `data/processed/excluded_records.csv` for reasons why records were dropped.
- **Memory Issues**: If running out of memory, ensure streaming is enabled for large datasets (see `T059-Stream`).

## Contributing

When contributing code:
- Ensure all new functions have type hints.
- Add unit tests for new logic.
- Update documentation if the public API changes.
