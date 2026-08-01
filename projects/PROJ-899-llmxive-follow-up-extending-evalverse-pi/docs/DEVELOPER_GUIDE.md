# Developer Guide: llmXive Feature Distillation

## Getting Started

1. **Environment Setup**:
 Ensure you have Python 3.11 installed.
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

2. **Directory Initialization**:
 Run the setup script to create necessary folders (`data/raw`, `state`, etc.).
 ```bash
 python code/scripts/setup_environment.py
 ```

3. **Data Fetching**:
 The pipeline expects the EvalVerse dataset in `data/raw`.
 ```bash
 python code/scripts/run_pipeline.py --stage fetch
 ```
 *Note: This uses `DATASET_URL` and `DATASET_DOI` from `src/config.py`.*

## Development Workflow

### Running Tests
The project uses `pytest`. Run all tests:
```bash
pytest code/tests/ -v
```

Run specific test suites:
```bash
pytest code/tests/unit/ # Unit tests
pytest code/tests/integration/ # Integration tests
```

### Code Quality
We use `ruff` for linting and `black` for formatting.
```bash
ruff check code/
black code/
```

### Adding a New Feature
1. Define the user story in `specs/`.
2. Create a task in `tasks.md`.
3. Implement the logic in the appropriate module (e.g., `src/models/metrics.py`).
4. Add unit tests in `tests/unit/`.
5. Update `docs/README.md` if new CLI flags or artifacts are introduced.

## Module Responsibilities

- **`src/data/download.py`**: Handles fetching and unzipping the dataset.
- **`src/data/preprocess.py`**: Extracts optical flow, HOG, and audio features.
- **`src/models/train.py`**: Trains Ridge, Lasso, and XGBoost models.
- **`src/models/metrics.py`**: Calculates correlations, CIs, and sensitivity sweeps.
- **`src/models/evaluate.py`**: Handles baseline comparisons and feasibility projections.
- **`src/reports/generate.py`**: Compiles final JSON/CSV reports.

## Troubleshooting

### "Module not found" errors
Ensure `code/` is in your `PYTHONPATH` or run scripts from the project root:
```bash
PYTHONPATH=code python code/scripts/run_pipeline.py
```

### "Data not available" errors
Verify that `data/raw/` contains the extracted dataset. Run `fetch_evalverse_dataset` again if the checksum fails.

### Memory Limit Exceeded
The pipeline is optimized for 7GB RAM. If you encounter OOM errors, check if other applications are consuming memory, or reduce the batch size in `src/cli/run_pipeline.py`.
