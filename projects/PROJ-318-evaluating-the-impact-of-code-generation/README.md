# PROJ-318: Evaluating the Impact of Code Generation Models

This project evaluates the impact of code generation models (specifically `Salesforce/codegen-350M-mono`) on code documentation completeness.

## Project Structure

- `code/`: Source code for the pipeline
 - `utils/`: Utility modules (AST parsing, coverage, stats, etc.)
- `data/`: Data storage
 - `raw/`: Raw data (cloned repos, extracted signatures)
 - `processed/`: Processed results (generated docstrings, analysis)
- `tests/`: Test suites
- `state/`: Pipeline state tracking
- `logs/`: Execution logs

## Setup

To initialize the project directory structure, run:

```bash
python code/setup_structure.py
```

## Dependencies

Install dependencies using:

```bash
pip install -r requirements.txt
```

(Note: `requirements.txt` will be created in a subsequent task)

## Usage

Follow the steps in `quickstart.md` to run the full pipeline.

## License

MIT
