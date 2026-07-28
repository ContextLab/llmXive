# PROJ-094: Evaluating the Effectiveness of Retrieval-Augmented Generation for Code Search

## Project Structure

This project follows the structure defined in `tasks.md`:

- `src/`: Source code for the research pipeline
 - `lib/`: Utility functions (metrics, stats, utils)
 - `data/`: Data loading, preprocessing, and checksums
 - `models/`: Retrievers (BM25, Neural, RAG) and generators
 - `analysis/`: Evaluation, correlation, and control experiments
 - `cli/`: Command-line interface
- `tests/`: Unit, integration, and contract tests
- `data/`: Data storage
 - `raw/`: Downloaded raw datasets (via ir-datasets)
 - `results/`: Generated metrics and reports
- `figures/`: Generated plots and visualizations
- `specs/`: Project specifications and design documents
- `docs/`: Documentation

## Quick Start

1. **Setup Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

2. **Initialize Project Structure** (if not already done):
 ```bash
 python code/setup_project.py
 ```

3. **Run the Pipeline**:
 ```bash
 python -m src.cli.main --seed 42
 ```

## Data

Raw data is downloaded automatically via `ir-datasets` to `data/raw/`.
Results are written to `data/results/`.

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## License

[Project License]
