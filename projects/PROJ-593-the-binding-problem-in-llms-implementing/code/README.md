# The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## Project Structure
This project follows a standard Python research pipeline structure:
- `src/`: Source code for modules, models, and analysis
- `tests/`: Unit, integration, and contract tests
- `data/`: Raw, processed, and synthetic data artifacts
- `config/`: Configuration files (YAML)
- `docs/`: Documentation and traceability reports

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Quick Start
1. **Setup**: Ensure the directory structure exists (created by T001).
2. **Data**: Run data ingestion scripts (T005, T006) to populate `data/raw/`.
3. **Preprocess**: Run `python src/data/preprocess_meg.py` to generate `data/processed/` artifacts.
4. **Experiment**: Run `python src/main.py` to execute the frequency sweep and generate results.

## Verification
Run tests to verify implementation:
```bash
pytest tests/
```
