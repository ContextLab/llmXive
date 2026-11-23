# llmXive: EvalVerse Feature Distillation

Automated science pipeline for analyzing technical sub-dimensions in video clips using CPU-tractable feature distillation.

## Project Structure

- `src/`: Source code for data processing, models, and reports
- `data/`: Data storage (raw, processed)
- `tests/`: Test suite
- `specs/`: Feature specifications and design docs
- `state/`: Runtime state (gates, hashes)
- `reports/`: Generated reports
- `figures/`: Generated plots and charts

## Setup

1. Create virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run pipeline: `python -m src.cli.run_pipeline`

## Development

- Linting: `ruff check src/`
- Formatting: `black src/`
- Tests: `pytest tests/`

## License

MIT
